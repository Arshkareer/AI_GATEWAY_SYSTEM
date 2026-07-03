import logging
import sys
from typing import Optional
from datetime import datetime
import structlog
from app.config import settings


def setup_logging():
    """Setup structured logging configuration."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Disable noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class RequestLogger:
    """Logger for API requests."""
    
    def __init__(self):
        self.logger = get_logger("api.request")
    
    def log_request(
        self,
        method: str,
        path: str,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log API request."""
        self.logger.info(
            "API Request",
            method=method,
            path=path,
            user_id=user_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ):
        """Log API response."""
        self.logger.info(
            "API Response",
            method=method,
            path=path,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=user_id,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
        )


class GatewayLogger:
    """Logger for AI Gateway requests."""
    
    def __init__(self):
        self.logger = get_logger("ai.gateway")
    
    def log_llm_request(
        self,
        request_id: str,
        provider: str,
        model: str,
        user_id: int,
        prompt_tokens: int,
        estimated_cost: float,
    ):
        """Log LLM request."""
        self.logger.info(
            "LLM Request",
            request_id=request_id,
            provider=provider,
            model=model,
            user_id=user_id,
            prompt_tokens=prompt_tokens,
            estimated_cost=estimated_cost,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    def log_llm_response(
        self,
        request_id: str,
        provider: str,
        model: str,
        user_id: int,
        response_tokens: int,
        total_tokens: int,
        actual_cost: float,
        latency_ms: int,
        status: str,
        error: Optional[str] = None,
    ):
        """Log LLM response."""
        log_data = {
            "request_id": request_id,
            "provider": provider,
            "model": model,
            "user_id": user_id,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "actual_cost": actual_cost,
            "latency_ms": latency_ms,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if error:
            log_data["error"] = error
            self.logger.error("LLM Response Error", **log_data)
        else:
            self.logger.info("LLM Response Success", **log_data)


# Global logger instances
request_logger = RequestLogger()
gateway_logger = GatewayLogger()