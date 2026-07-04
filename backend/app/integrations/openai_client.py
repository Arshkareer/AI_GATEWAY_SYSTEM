import asyncio
import json
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
import aiohttp
from app.integrations.base_client import BaseLLMClient, LLMResponse, LLMError, TokenCounter
from app.utils.constants import MODEL_PRICING, PROVIDER_ENDPOINTS
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client implementation."""
    
    def __init__(self, api_key: str, organization_id: Optional[str] = None):
        super().__init__(api_key)
        self.organization_id = organization_id
        self.base_url = PROVIDER_ENDPOINTS["openai"]["base_url"]
        self._session = None
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "gpt-4", "gpt-4-32k", "gpt-4-1106-preview", "gpt-4-vision-preview",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-1106",
            "text-davinci-003", "text-davinci-002"
        ]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            if self.organization_id:
                headers["OpenAI-Organization"] = self.organization_id
                
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            )
        
        return self._session
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion using OpenAI API."""
        
        if not self.validate_model(model):
            raise ValueError(f"Model {model} not supported by OpenAI")
        
        session = await self._get_session()
        url = f"{self.base_url}/chat/completions"
        
        # Count input tokens
        prompt_tokens = TokenCounter.count_message_tokens(messages, model)
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": False
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if stop:
            payload["stop"] = stop
        
        start_time = time.time()
        
        try:
            async with session.post(url, json=payload) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    raise Exception(f"OpenAI API error: {error_msg}")
                
                # Extract response data
                choice = response_data["choices"][0]
                usage = response_data["usage"]
                
                latency_ms = int((time.time() - start_time) * 1000)
                completion_tokens = usage["completion_tokens"]
                total_tokens = usage["total_tokens"]
                
                # Calculate cost
                cost = self.calculate_cost(prompt_tokens, completion_tokens, model)
                
                return LLMResponse(
                    content=choice["message"]["content"],
                    finish_reason=choice["finish_reason"],
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    model=model,
                    provider=self.provider_name,
                    latency_ms=latency_ms,
                    cost=cost,
                    metadata={
                        "response_id": response_data.get("id"),
                        "created": response_data.get("created"),
                        "usage": usage
                    }
                )
        
        except aiohttp.ClientError as e:
            logger.error(f"OpenAI client error: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise e
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion using OpenAI API."""
        
        if not self.validate_model(model):
            raise ValueError(f"Model {model} not supported by OpenAI")
        
        session = await self._get_session()
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    raise Exception(f"OpenAI API error: {error_msg}")
                
                chunk_count = 0
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        
                        if data == '[DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(data)
                            choice = chunk_data["choices"][0]
                            
                            if "delta" in choice and "content" in choice["delta"]:
                                yield {
                                    "chunk_id": chunk_count,
                                    "content_delta": choice["delta"]["content"],
                                    "finish_reason": choice.get("finish_reason"),
                                    "is_final": choice.get("finish_reason") is not None
                                }
                                chunk_count += 1
                        
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise e
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available OpenAI models."""
        session = await self._get_session()
        url = f"{self.base_url}/models"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch models: {response.status}")
                
                data = await response.json()
                models = []
                
                for model in data["data"]:
                    if model["id"] in self.supported_models:
                        models.append({
                            "id": model["id"],
                            "object": model["object"],
                            "created": model["created"],
                            "owned_by": model["owned_by"],
                            "provider": self.provider_name
                        })
                
                return models
        
        except Exception as e:
            logger.error(f"Error fetching OpenAI models: {e}")
            return []
    
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for OpenAI model usage."""
        pricing = MODEL_PRICING.get("openai", {}).get(model)
        
        if not pricing:
            return 0.0
        
        input_cost = (prompt_tokens / 1000) * pricing["input_cost_per_1k"]
        output_cost = (completion_tokens / 1000) * pricing["output_cost_per_1k"]
        
        return round(input_cost + output_cost, 6)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for OpenAI models."""
        return TokenCounter.estimate_tokens(text, "cl100k_base")
    
    async def validate_api_key(self) -> bool:
        """Validate the OpenAI API key."""
        try:
            models = await self.get_available_models()
            return len(models) > 0
        except Exception:
            return False
    
    async def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        models = await self.get_available_models()
        
        for model_info in models:
            if model_info["id"] == model:
                # Add pricing information
                pricing = MODEL_PRICING.get("openai", {}).get(model, {})
                model_info.update({
                    "input_cost_per_1k": pricing.get("input_cost_per_1k", 0),
                    "output_cost_per_1k": pricing.get("output_cost_per_1k", 0)
                })
                return model_info
        
        return None
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the session when exiting context."""
        if self._session and not self._session.closed:
            await self._session.close()