from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.request_log import LLMProvider


class ModelConfig(BaseModel):
    """Model configuration schema."""
    name: str
    provider: LLMProvider
    max_tokens: int = 4096
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    
    # Cost configuration (per 1K tokens)
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    
    # Rate limiting
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000


class ProviderConfig(BaseModel):
    """Provider configuration schema."""
    provider: LLMProvider
    api_key: str
    base_url: Optional[str] = None
    is_active: bool = True
    default_model: str
    available_models: List[str]
    
    # Provider-specific settings
    organization_id: Optional[str] = None  # OpenAI
    project_id: Optional[str] = None  # Google Cloud
    region: Optional[str] = None


class GatewayRequest(BaseModel):
    """Gateway request schema."""
    
    # Model selection
    model: Optional[str] = None  # If not provided, will use smart routing
    provider: Optional[LLMProvider] = None
    
    # Message content
    messages: List[Dict[str, Any]] = Field(..., min_items=1)
    
    # Generation parameters
    max_tokens: Optional[int] = Field(None, ge=1, le=32000)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0)
    stop: Optional[List[str]] = None
    
    # Request metadata
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    user_metadata: Optional[Dict[str, Any]] = {}
    
    # Privacy controls
    store_prompt: bool = False
    store_response: bool = False
    
    # Routing preferences
    prefer_speed: bool = False
    prefer_cost: bool = False
    prefer_quality: bool = True
    
    @validator('messages')
    def validate_messages(cls, v):
        """Validate message format."""
        for msg in v:
            if 'role' not in msg or 'content' not in msg:
                raise ValueError('Each message must have "role" and "content" fields')
            if msg['role'] not in ['system', 'user', 'assistant']:
                raise ValueError('Message role must be "system", "user", or "assistant"')
        return v


class GatewayResponse(BaseModel):
    """Gateway response schema."""
    
    # Request identification
    request_id: str
    session_id: Optional[str]
    
    # Provider & model used
    provider: LLMProvider
    model: str
    
    # Response content
    content: str
    finish_reason: str
    
    # Usage metrics
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    # Performance metrics
    latency_ms: int
    
    # Cost information
    cost: float
    currency: str = "USD"
    
    # Metadata
    created_at: datetime
    response_metadata: Optional[Dict[str, Any]] = {}
    
    # Quality metrics (if available)
    quality_score: Optional[float] = None
    confidence_score: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "request_id": "req_123456789",
                "session_id": "session_abc123",
                "provider": "openai",
                "model": "gpt-4",
                "content": "Hello! How can I help you today?",
                "finish_reason": "stop",
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18,
                "latency_ms": 1250,
                "cost": 0.0054,
                "currency": "USD",
                "created_at": "2023-12-01T10:30:00Z"
            }
        }


class StreamChunk(BaseModel):
    """Streaming response chunk schema."""
    request_id: str
    chunk_id: int
    content_delta: str
    is_final: bool = False
    
    # Only included in final chunk
    usage: Optional[Dict[str, int]] = None
    cost: Optional[float] = None
    latency_ms: Optional[int] = None


class BatchRequest(BaseModel):
    """Batch request schema."""
    requests: List[GatewayRequest] = Field(..., min_items=1, max_items=100)
    batch_id: Optional[str] = None
    priority: int = Field(1, ge=1, le=5)  # 1 = lowest, 5 = highest
    
    # Batch processing options
    fail_fast: bool = False  # Stop on first error
    max_parallel: int = Field(5, ge=1, le=10)
    
    @validator('requests')
    def validate_batch_size(cls, v):
        if len(v) > 100:
            raise ValueError('Batch size cannot exceed 100 requests')
        return v


class BatchResponse(BaseModel):
    """Batch response schema."""
    batch_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    
    # Aggregate metrics
    total_tokens: int
    total_cost: float
    total_latency_ms: int
    
    # Individual responses
    responses: List[GatewayResponse]
    errors: List[Dict[str, Any]]
    
    # Processing info
    started_at: datetime
    completed_at: datetime
    processing_time_ms: int


class ModelInfo(BaseModel):
    """Model information schema."""
    name: str
    provider: LLMProvider
    description: str
    
    # Capabilities
    max_tokens: int
    supports_streaming: bool
    supports_functions: bool
    supports_vision: bool
    
    # Pricing (per 1K tokens)
    input_cost_per_1k: float
    output_cost_per_1k: float
    
    # Performance characteristics
    avg_latency_ms: int
    quality_rating: float  # 1-5 scale
    
    # Availability
    is_available: bool
    rate_limit_per_minute: int