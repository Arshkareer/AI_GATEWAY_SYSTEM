from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import asyncio
import time


@dataclass
class LLMResponse:
    """Standardized response from LLM providers."""
    content: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    provider: str
    latency_ms: int
    cost: float
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def success(self) -> bool:
        return self.finish_reason in ["stop", "length"]


@dataclass 
class LLMError:
    """Standardized error from LLM providers."""
    error_code: str
    message: str
    status_code: int
    provider: str
    retryable: bool = False
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMClient(ABC):
    """Base class for all LLM provider clients."""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self._session = None
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of supported models."""
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion."""
        pass
    
    @abstractmethod
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]], 
        model: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion."""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models."""
        pass
    
    @abstractmethod
    def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for token usage."""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        pass
    
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        try:
            models = await self.get_available_models()
            return len(models) > 0
        except Exception:
            return False
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported."""
        return model in self.supported_models
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()


class RateLimitManager:
    """Manage rate limits for providers."""
    
    def __init__(self):
        self._limits = {}
        self._windows = {}
    
    async def check_rate_limit(
        self, 
        provider: str, 
        model: str, 
        requests_per_minute: int
    ) -> bool:
        """Check if request is within rate limit."""
        key = f"{provider}:{model}"
        current_time = time.time()
        
        # Clean old requests outside the window
        if key in self._windows:
            self._windows[key] = [
                req_time for req_time in self._windows[key]
                if current_time - req_time < 60  # 60 seconds window
            ]
        else:
            self._windows[key] = []
        
        # Check if we can make another request
        if len(self._windows[key]) >= requests_per_minute:
            return False
        
        # Add current request
        self._windows[key].append(current_time)
        return True
    
    async def wait_for_rate_limit(
        self,
        provider: str,
        model: str, 
        requests_per_minute: int
    ):
        """Wait until rate limit allows request."""
        while not await self.check_rate_limit(provider, model, requests_per_minute):
            await asyncio.sleep(1)


class RetryManager:
    """Manage retries with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    raise last_exception
                
                # Exponential backoff
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        raise last_exception


class TokenCounter:
    """Utility for counting tokens across different providers."""
    
    @staticmethod
    def estimate_tokens(text: str, encoding: str = "cl100k_base") -> int:
        """Estimate token count using tiktoken or fallback method."""
        try:
            import tiktoken
            enc = tiktoken.get_encoding(encoding)
            return len(enc.encode(text))
        except ImportError:
            # Fallback: rough estimation (4 chars per token for English)
            return max(1, len(text) // 4)
    
    @staticmethod
    def count_message_tokens(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> int:
        """Count tokens in message array."""
        total = 0
        
        for message in messages:
            # Add tokens for message structure
            total += 4  # Every message has role, content, name, etc.
            
            for key, value in message.items():
                total += TokenCounter.estimate_tokens(str(value))
                
        total += 2  # Add tokens for assistant reply priming
        return total