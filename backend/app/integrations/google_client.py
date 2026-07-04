import asyncio
import json
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
import aiohttp
from app.integrations.base_client import BaseLLMClient, LLMResponse, LLMError, TokenCounter
from app.utils.constants import MODEL_PRICING, PROVIDER_ENDPOINTS
from app.core.logging import get_logger

logger = get_logger(__name__)


class GoogleClient(BaseLLMClient):
    """Google AI (Gemini) API client implementation."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = PROVIDER_ENDPOINTS["google"]["base_url"]
        self._session = None
        
    @property
    def provider_name(self) -> str:
        return "google"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "gemini-pro",
            "gemini-pro-vision", 
            "palm-2"
        ]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            )
        
        return self._session
    
    def _convert_messages_to_google_format(
        self, 
        messages: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Convert OpenAI format messages to Google format."""
        google_messages = []
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            # Map roles to Google format
            if role == "system":
                # Google doesn't have system messages, prepend to first user message
                if google_messages and google_messages[0]["role"] == "user":
                    google_messages[0]["parts"][0]["text"] = f"{content}\n\n{google_messages[0]['parts'][0]['text']}"
                else:
                    google_messages.insert(0, {
                        "role": "user",
                        "parts": [{"text": content + "\n\n"}]
                    })
            elif role == "user":
                google_messages.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "assistant":
                google_messages.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })
        
        return google_messages
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        top_p: float = 1.0,
        top_k: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion using Google AI API."""
        
        if not self.validate_model(model):
            raise ValueError(f"Model {model} not supported by Google")
        
        session = await self._get_session()
        url = f"{self.base_url}/models/{model}:generateContent"
        
        # Convert messages format
        google_messages = self._convert_messages_to_google_format(messages)
        
        # Count input tokens (approximate)
        prompt_tokens = sum(self.estimate_tokens(msg["content"]) for msg in messages)
        
        payload = {
            "contents": google_messages,
            "generationConfig": {
                "temperature": temperature,
                "topP": top_p,
                "candidateCount": 1
            }
        }
        
        if max_output_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_output_tokens
        
        if top_k:
            payload["generationConfig"]["topK"] = top_k
        
        # Add API key to URL
        url += f"?key={self.api_key}"
        
        start_time = time.time()
        
        try:
            async with session.post(url, json=payload) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("error", {}).get("message", "Unknown error")
                    raise Exception(f"Google AI API error: {error_msg}")
                
                # Extract response data
                candidates = response_data.get("candidates", [])
                if not candidates:
                    raise Exception("No response candidates from Google AI")
                
                candidate = candidates[0]
                content = candidate["content"]["parts"][0]["text"]
                finish_reason = candidate.get("finishReason", "STOP")
                
                # Get usage info if available
                usage_metadata = response_data.get("usageMetadata", {})
                completion_tokens = usage_metadata.get("candidatesTokenCount", 
                                                     self.estimate_tokens(content))
                total_tokens = usage_metadata.get("totalTokenCount", 
                                                prompt_tokens + completion_tokens)
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Calculate cost
                cost = self.calculate_cost(prompt_tokens, completion_tokens, model)
                
                return LLMResponse(
                    content=content,
                    finish_reason=finish_reason.lower(),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    model=model,
                    provider=self.provider_name,
                    latency_ms=latency_ms,
                    cost=cost,
                    metadata={
                        "usage_metadata": usage_metadata,
                        "finish_reason": finish_reason,
                        "safety_ratings": candidate.get("safetyRatings", [])
                    }
                )
        
        except aiohttp.ClientError as e:
            logger.error(f"Google AI client error: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Google AI API error: {e}")
            raise e
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion using Google AI API."""
        
        if not self.validate_model(model):
            raise ValueError(f"Model {model} not supported by Google")
        
        session = await self._get_session()
        url = f"{self.base_url}/models/{model}:streamGenerateContent"
        
        # Convert messages format
        google_messages = self._convert_messages_to_google_format(messages)
        
        payload = {
            "contents": google_messages,
            "generationConfig": {
                "temperature": temperature,
                "candidateCount": 1
            }
        }
        
        if max_output_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_output_tokens
        
        # Add API key to URL
        url += f"?key={self.api_key}"
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_data = await response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    raise Exception(f"Google AI API error: {error_msg}")
                
                chunk_count = 0
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        
                        try:
                            chunk_data = json.loads(data)
                            
                            candidates = chunk_data.get("candidates", [])
                            if candidates:
                                candidate = candidates[0]
                                if "content" in candidate:
                                    parts = candidate["content"].get("parts", [])
                                    if parts and "text" in parts[0]:
                                        yield {
                                            "chunk_id": chunk_count,
                                            "content_delta": parts[0]["text"],
                                            "finish_reason": candidate.get("finishReason"),
                                            "is_final": "finishReason" in candidate
                                        }
                                        chunk_count += 1
                        
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"Google AI streaming error: {e}")
            raise e
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available Google AI models."""
        session = await self._get_session()
        url = f"{self.base_url}/models?key={self.api_key}"
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch models: {response.status}")
                
                data = await response.json()
                models = []
                
                for model in data.get("models", []):
                    model_id = model["name"].split("/")[-1]  # Extract model name from full path
                    
                    if model_id in self.supported_models:
                        models.append({
                            "id": model_id,
                            "name": model["name"],
                            "display_name": model.get("displayName", model_id),
                            "description": model.get("description", ""),
                            "provider": self.provider_name,
                            "supported_generation_methods": model.get("supportedGenerationMethods", [])
                        })
                
                return models
        
        except Exception as e:
            logger.error(f"Error fetching Google AI models: {e}")
            return []
    
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for Google AI model usage."""
        pricing = MODEL_PRICING.get("google", {}).get(model)
        
        if not pricing:
            return 0.0
        
        input_cost = (prompt_tokens / 1000) * pricing["input_cost_per_1k"]
        output_cost = (completion_tokens / 1000) * pricing["output_cost_per_1k"]
        
        return round(input_cost + output_cost, 6)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Google AI models."""
        # Google AI uses similar tokenization patterns
        return TokenCounter.estimate_tokens(text)
    
    async def validate_api_key(self) -> bool:
        """Validate the Google AI API key."""
        try:
            models = await self.get_available_models()
            return len(models) > 0
        except Exception as e:
            logger.error(f"Google AI API key validation failed: {e}")
            return False
    
    async def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        models = await self.get_available_models()
        
        for model_info in models:
            if model_info["id"] == model:
                # Add pricing information
                pricing = MODEL_PRICING.get("google", {}).get(model, {})
                model_info.update({
                    "input_cost_per_1k": pricing.get("input_cost_per_1k", 0),
                    "output_cost_per_1k": pricing.get("output_cost_per_1k", 0),
                    "max_tokens": 32768 if "gemini" in model else 8192,
                    "supports_streaming": True,
                    "supports_vision": "vision" in model
                })
                return model_info
        
        return None
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the session when exiting context."""
        if self._session and not self._session.closed:
            await self._session.close()