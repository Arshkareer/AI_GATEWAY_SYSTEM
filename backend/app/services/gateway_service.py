import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from sqlalchemy.orm import Session

from app.integrations import OpenAIClient, AnthropicClient, GoogleClient, BaseLLMClient, LLMResponse
from app.models.user import User
from app.models.department import Department  
from app.models.request_log import RequestLog, LLMProvider, RequestStatus
from app.schemas.gateway import GatewayRequest, GatewayResponse, StreamChunk
from app.utils.helpers import generate_request_id, hash_content
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProviderManager:
    """Manages LLM provider clients and configurations."""
    
    def __init__(self):
        self._clients: Dict[str, BaseLLMClient] = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM provider clients based on configuration."""
        
        # OpenAI
        if settings.OPENAI_API_KEY:
            self._clients["openai"] = OpenAIClient(settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        
        # Anthropic
        if settings.ANTHROPIC_API_KEY:
            self._clients["anthropic"] = AnthropicClient(settings.ANTHROPIC_API_KEY)
            logger.info("Anthropic client initialized")
        
        # Google AI
        if settings.GOOGLE_API_KEY:
            self._clients["google"] = GoogleClient(settings.GOOGLE_API_KEY)
            logger.info("Google AI client initialized")
    
    def get_client(self, provider: str) -> Optional[BaseLLMClient]:
        """Get client for specified provider."""
        return self._clients.get(provider.lower())
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self._clients.keys())
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if provider is available."""
        return provider.lower() in self._clients
    
    async def get_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available models from all providers."""
        all_models = {}
        
        for provider_name, client in self._clients.items():
            try:
                models = await client.get_available_models()
                all_models[provider_name] = models
            except Exception as e:
                logger.error(f"Failed to get models from {provider_name}: {e}")
                all_models[provider_name] = []
        
        return all_models
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all providers."""
        health_status = {}
        
        for provider_name, client in self._clients.items():
            try:
                health_status[provider_name] = await client.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {e}")
                health_status[provider_name] = False
        
        return health_status


class ModelRouter:
    """Smart model routing based on request characteristics."""
    
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
    
    async def select_optimal_model(
        self, 
        request: GatewayRequest,
        user: User,
        available_providers: Optional[List[str]] = None
    ) -> tuple[str, str]:
        """Select optimal model and provider based on request preferences."""
        
        # If model and provider are explicitly specified
        if request.model and request.provider:
            if self.provider_manager.is_provider_available(request.provider):
                return request.provider, request.model
            else:
                raise ValueError(f"Provider {request.provider} is not available")
        
        # If only model is specified, find the provider
        if request.model:
            provider = await self._find_provider_for_model(request.model)
            if provider:
                return provider, request.model
            else:
                raise ValueError(f"Model {request.model} is not available")
        
        # Smart routing based on preferences
        return await self._smart_route(request, user, available_providers)
    
    async def _find_provider_for_model(self, model: str) -> Optional[str]:
        """Find which provider supports the specified model."""
        for provider_name, client in self.provider_manager._clients.items():
            if client.validate_model(model):
                return provider_name
        return None
    
    async def _smart_route(
        self, 
        request: GatewayRequest,
        user: User,
        available_providers: Optional[List[str]] = None
    ) -> tuple[str, str]:
        """Intelligently route request to optimal provider and model."""
        
        if available_providers is None:
            available_providers = self.provider_manager.get_available_providers()
        
        # Calculate message complexity
        message_length = sum(len(msg.get("content", "")) for msg in request.messages)
        is_complex = message_length > 1000  # Threshold for complexity
        
        # Route based on preferences
        if request.prefer_cost and "google" in available_providers:
            # Google Gemini Pro is typically cheapest
            return "google", "gemini-pro"
        
        elif request.prefer_speed and "openai" in available_providers:
            # GPT-3.5-turbo is fast
            return "openai", "gpt-3.5-turbo"
        
        elif request.prefer_quality or is_complex:
            # For quality, prefer GPT-4 or Claude
            if "openai" in available_providers:
                return "openai", "gpt-4"
            elif "anthropic" in available_providers:
                return "anthropic", "claude-3-sonnet-20240229"
        
        # Default fallback
        if "openai" in available_providers:
            return "openai", "gpt-3.5-turbo"
        elif "anthropic" in available_providers:
            return "anthropic", "claude-3-haiku-20240307"
        elif "google" in available_providers:
            return "google", "gemini-pro"
        
        raise ValueError("No available providers for request")


class GatewayService:
    """Main AI Gateway service for processing requests."""
    
    def __init__(self):
        self.provider_manager = ProviderManager()
        self.model_router = ModelRouter(self.provider_manager)
    
    async def process_request(
        self,
        request: GatewayRequest,
        user: User,
        db: Session,
        stream: bool = False
    ) -> Union[GatewayResponse, AsyncGenerator[StreamChunk, None]]:
        """Process AI request through the gateway."""
        
        # Generate request ID
        request_id = request.request_id or generate_request_id()
        
        try:
            # Select optimal provider and model
            provider, model = await self.model_router.select_optimal_model(request, user)
            
            # Get provider client
            client = self.provider_manager.get_client(provider)
            if not client:
                raise ValueError(f"Provider {provider} client not available")
            
            # Create initial request log
            request_log = await self._create_request_log(
                request_id, request, user, provider, model, db
            )
            
            # Process request
            if stream:
                return self._process_streaming_request(
                    request, client, provider, model, request_log, db
                )
            else:
                return await self._process_regular_request(
                    request, client, provider, model, request_log, db
                )
        
        except Exception as e:
            logger.error(f"Gateway request failed: {e}")
            
            # Log error
            if 'request_log' in locals():
                await self._update_request_log_error(request_log, str(e), db)
            
            raise e
    
    async def _create_request_log(
        self,
        request_id: str,
        request: GatewayRequest,
        user: User,
        provider: str,
        model: str,
        db: Session
    ) -> RequestLog:
        """Create initial request log entry."""
        
        # Calculate prompt tokens
        messages_text = " ".join(msg.get("content", "") for msg in request.messages)
        prompt_tokens = len(messages_text) // 4  # Rough estimate
        
        request_log = RequestLog(
            request_id=request_id,
            session_id=request.session_id,
            user_id=user.id,
            department_id=user.department_id,
            provider=LLMProvider(provider),
            model_name=model,
            prompt_text=messages_text if request.store_prompt else None,
            prompt_hash=hash_content(messages_text),
            prompt_tokens=prompt_tokens,
            store_prompt=request.store_prompt,
            store_response=request.store_response,
            request_metadata=request.user_metadata
        )
        
        db.add(request_log)
        db.commit()
        db.refresh(request_log)
        
        return request_log
    
    async def _process_regular_request(
        self,
        request: GatewayRequest,
        client: BaseLLMClient,
        provider: str,
        model: str,
        request_log: RequestLog,
        db: Session
    ) -> GatewayResponse:
        """Process regular (non-streaming) request."""
        
        start_time = datetime.utcnow()
        
        try:
            # Call LLM provider
            llm_response = await client.chat_completion(
                messages=request.messages,
                model=model,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
                top_p=request.top_p or 1.0,
                frequency_penalty=request.frequency_penalty or 0.0,
                presence_penalty=request.presence_penalty or 0.0,
                stop=request.stop
            )
            
            # Update request log
            await self._update_request_log_success(
                request_log, llm_response, request.store_response, db
            )
            
            # Update user and department stats
            await self._update_usage_stats(request_log, db)
            
            # Create gateway response
            return GatewayResponse(
                request_id=request_log.request_id,
                session_id=request_log.session_id,
                provider=LLMProvider(provider),
                model=model,
                content=llm_response.content,
                finish_reason=llm_response.finish_reason,
                prompt_tokens=llm_response.prompt_tokens,
                completion_tokens=llm_response.completion_tokens,
                total_tokens=llm_response.total_tokens,
                latency_ms=llm_response.latency_ms,
                cost=llm_response.cost,
                created_at=datetime.utcnow(),
                response_metadata=llm_response.metadata
            )
        
        except Exception as e:
            await self._update_request_log_error(request_log, str(e), db)
            raise e
    
    async def _process_streaming_request(
        self,
        request: GatewayRequest,
        client: BaseLLMClient,
        provider: str,
        model: str,
        request_log: RequestLog,
        db: Session
    ) -> AsyncGenerator[StreamChunk, None]:
        """Process streaming request."""
        
        full_content = ""
        chunk_count = 0
        
        try:
            async for chunk in client.stream_chat_completion(
                messages=request.messages,
                model=model,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens
            ):
                full_content += chunk.get("content_delta", "")
                
                yield StreamChunk(
                    request_id=request_log.request_id,
                    chunk_id=chunk_count,
                    content_delta=chunk.get("content_delta", ""),
                    is_final=chunk.get("is_final", False)
                )
                
                chunk_count += 1
                
                # If final chunk, update logs
                if chunk.get("is_final"):
                    # Calculate final metrics
                    completion_tokens = len(full_content) // 4  # Rough estimate
                    total_tokens = request_log.prompt_tokens + completion_tokens
                    cost = client.calculate_cost(
                        request_log.prompt_tokens, 
                        completion_tokens, 
                        model
                    )
                    
                    # Create mock LLM response for logging
                    from app.integrations.base_client import LLMResponse
                    mock_response = LLMResponse(
                        content=full_content,
                        finish_reason=chunk.get("finish_reason", "stop"),
                        prompt_tokens=request_log.prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        model=model,
                        provider=provider,
                        latency_ms=0,  # Will be calculated in update
                        cost=cost
                    )
                    
                    await self._update_request_log_success(
                        request_log, mock_response, request.store_response, db
                    )
                    await self._update_usage_stats(request_log, db)
        
        except Exception as e:
            await self._update_request_log_error(request_log, str(e), db)
            raise e
    
    async def _update_request_log_success(
        self,
        request_log: RequestLog,
        llm_response: LLMResponse,
        store_response: bool,
        db: Session
    ):
        """Update request log with successful response."""
        
        request_log.response_text = llm_response.content if store_response else None
        request_log.response_hash = hash_content(llm_response.content)
        request_log.response_tokens = llm_response.completion_tokens
        request_log.total_tokens = llm_response.total_tokens
        request_log.latency_ms = llm_response.latency_ms
        request_log.status = RequestStatus.SUCCESS
        request_log.total_cost = llm_response.cost
        request_log.response_metadata = llm_response.metadata
        
        db.commit()
    
    async def _update_request_log_error(
        self,
        request_log: RequestLog,
        error_message: str,
        db: Session
    ):
        """Update request log with error information."""
        
        request_log.status = RequestStatus.ERROR
        request_log.error_message = error_message
        request_log.total_cost = 0.0  # No cost for failed requests
        
        db.commit()
    
    async def _update_usage_stats(self, request_log: RequestLog, db: Session):
        """Update user and department usage statistics."""
        
        # Update user stats
        user = db.query(User).filter(User.id == request_log.user_id).first()
        if user:
            user.total_requests += 1
            user.total_cost += request_log.total_cost
        
        # Update department stats
        if request_log.department_id:
            department = db.query(Department).filter(
                Department.id == request_log.department_id
            ).first()
            if department:
                department.total_requests += 1
                department.total_cost += request_log.total_cost
                department.current_month_cost += request_log.total_cost
        
        db.commit()
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        health_status = await self.provider_manager.health_check_all()
        
        status = {
            "providers": {},
            "total_providers": len(self.provider_manager._clients),
            "healthy_providers": sum(health_status.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for provider_name, client in self.provider_manager._clients.items():
            status["providers"][provider_name] = {
                "healthy": health_status.get(provider_name, False),
                "supported_models": client.supported_models,
                "provider_class": client.__class__.__name__
            }
        
        return status
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get all available models from all providers."""
        all_models = []
        
        for provider_name, models in (await self.provider_manager.get_all_models()).items():
            all_models.extend(models)
        
        return all_models