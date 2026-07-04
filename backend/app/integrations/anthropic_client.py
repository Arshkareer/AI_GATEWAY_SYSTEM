import asyncio
import json
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
import aiohttp
from app.integrations.base_client import BaseLLMClient, LLMResponse, LLMError, TokenCounter
from app.utils.constants import MODEL_PRICING, PROVIDER_ENDPOINTS
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic API client implementation."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = PROVIDER_ENDPOINTS["anthropic"]["base_url"]
        self._session = None
        
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session or self._session.closed:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
                
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            )
        
        return self._session
    
    def _convert_messages_to_anthropic_format(
        self, 
        messages: List[Dict[str, str]]
    ) -> tuple[Optional[str], List[Dict[str, str]]]:
        """Convert OpenAI format messages to Anthropic format."""
        system_message = None
        anthropic_messages = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                system_message = content
            elif role in ["user", "assistant"]:
                anthropic_messages.append({
                    "role": role,
                    "content": content
                })
        
        return system_message, anthropic_messages
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 1.0,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion using Anthropic API."""
        
        if not self.validate_model(model):
            raise ValueError(f"Model {model} not supported by Anthropic")
        
        session = await self._get_session()
        url = f"{self.base_url}/v1/messages"
        
        # Convert messages format
        system_message, anthropic_messages = self._convert_messages_to_anthropic_format(messages)
        
        # Count input tokens
        prompt_tokens = sum(self.estimate_tokens(msg["content"]) for msg in messages)
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        if system_message:
            payload["system"] = system_message
        
        if stop_sequences:
            payload["stop_sequences"] = stop_sequences
        
        start_time = time.time()
        
        try:
            async with session.post(url, json=payload) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    raise Exception(f"Anthropic API error: {error_msg}")
                
                # Extract response data
                content = response_data["content"][0]["text"]
                usage = response_data["usage"]
                
                latency_ms = int((time.time() - start_time) * 1000)
                completion_tokens = usage["output_tokens"]
                total_tokens = usage["input_tokens"] + completion_tokens
                
                # Calculate cost
                cost = self.calculate_cost(usage["input_tokens"], completion_tokens, model)
                
                return LLMResponse(
                    content=content,
                    finish_reason=response_data.get("stop_reason", "stop"),
                    prompt_tokens=usage["input_tokens"],
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    model=model,
                    provider=self.provider_name,
                    latency_ms=latency_ms,
                    cost=cost,
                    metadata={
                        "response_id": response_data.get("id"),
                        "usage": usage,
                        "stop_reason": response_data.get("stop_reason")
                    }
                )
        
        except aiohttp.ClientError as e:
            logger.error(f"Anthropic client error: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise e
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion using Anthropic API."""
        
        if not self.validate_model(model):
            raise ValueError(f"Model {model} not supported by Anthropic")
        
        session = await self._get_session()
        url = f"{self.base_url}/v1/messages"
        
        # Convert messages format
        system_message, anthropic_messages = self._convert_messages_to_anthropic_format(messages)
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        if system_message:
            payload["system"] = system_message
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    raise Exception(f"Anthropic API error: {error_msg}")
                
                chunk_count = 0
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        
                        try:
                            chunk_data = json.loads(data)
                            
                            if chunk_data.get("type") == "content_block_delta":
                                delta = chunk_data.get("delta", {})
                                if "text" in delta:
                                    yield {
                                        "chunk_id": chunk_count,
                                        "content_delta": delta["text"],
                                        "finish_reason": None,
                                        "is_final": False
                                    }
                                    chunk_count += 1
                            
                            elif chunk_data.get("type") == "message_stop":
                                yield {
                                    "chunk_id": chunk_count,
                                    "content_delta": "",
                                    "finish_reason": "stop",
                                    "is_final": True
                                }
                        
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise e
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available Anthropic models."""
        # Anthropic doesn't have a public models endpoint, return supported models
        models = []
        
        for model in self.supported_models:
            models.append({
                "id": model,
                "object": "model",
                "owned_by": "anthropic",
                "provider": self.provider_name,
                "created": None  # Not available from Anthropic
            })
        
        return models
    
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for Anthropic model usage."""
        # Map display names to pricing keys
        model_mapping = {
            "claude-3-opus-20240229": "claude-3-opus",
            "claude-3-sonnet-20240229": "claude-3-sonnet", 
            "claude-3-haiku-20240307": "claude-3-haiku",
            "claude-2.1": "claude-2",
            "claude-2.0": "claude-2",
            "claude-instant-1.2": "claude-instant"
        }
        
        pricing_key = model_mapping.get(model, model)
        pricing = MODEL_PRICING.get("anthropic", {}).get(pricing_key)
        
        if not pricing:
            return 0.0
        
        input_cost = (prompt_tokens / 1000) * pricing["input_cost_per_1k"]
        output_cost = (completion_tokens / 1000) * pricing["output_cost_per_1k"]
        
        return round(input_cost + output_cost, 6)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Anthropic models."""
        # Anthropic uses similar tokenization to OpenAI
        return TokenCounter.estimate_tokens(text)
    
    async def validate_api_key(self) -> bool:
        """Validate the Anthropic API key by making a small test request."""
        try:
            test_messages = [{"role": "user", "content": "Hi"}]
            response = await self.chat_completion(
                messages=test_messages,
                model="claude-3-haiku-20240307",
                max_tokens=10
            )
            return response.success
        except Exception as e:
            logger.error(f"Anthropic API key validation failed: {e}")
            return False
    
    async def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        if model not in self.supported_models:
            return None
        
        # Map display names to pricing keys
        model_mapping = {
            "claude-3-opus-20240229": "claude-3-opus",
            "claude-3-sonnet-20240229": "claude-3-sonnet",
            "claude-3-haiku-20240307": "claude-3-haiku", 
            "claude-2.1": "claude-2",
            "claude-2.0": "claude-2",
            "claude-instant-1.2": "claude-instant"
        }
        
        pricing_key = model_mapping.get(model, model)
        pricing = MODEL_PRICING.get("anthropic", {}).get(pricing_key, {})
        
        return {
            "id": model,
            "object": "model", 
            "owned_by": "anthropic",
            "provider": self.provider_name,
            "input_cost_per_1k": pricing.get("input_cost_per_1k", 0),
            "output_cost_per_1k": pricing.get("output_cost_per_1k", 0),
            "max_tokens": 200000 if "claude-3" in model else 100000,
            "supports_streaming": True,
            "supports_system_messages": True
        }
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the session when exiting context."""
        if self._session and not self._session.closed:
            await self._session.close()