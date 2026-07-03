from datetime import datetime
from typing import Optional, Any
from fastapi import HTTPException, status


class CustomHTTPException(HTTPException):
    """Custom HTTP exception with additional fields."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        headers: Optional[dict] = None,
        **kwargs
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.timestamp = datetime.utcnow()
        self.additional_data = kwargs


class AuthenticationException(CustomHTTPException):
    """Authentication related exceptions."""
    
    def __init__(self, detail: str = "Authentication failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_FAILED",
            headers={"WWW-Authenticate": "Bearer"},
            **kwargs
        )


class AuthorizationException(CustomHTTPException):
    """Authorization related exceptions."""
    
    def __init__(self, detail: str = "Access denied", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="ACCESS_DENIED",
            **kwargs
        )


class ValidationException(CustomHTTPException):
    """Validation related exceptions."""
    
    def __init__(self, detail: str = "Validation failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_FAILED",
            **kwargs
        )


class ResourceNotFoundException(CustomHTTPException):
    """Resource not found exceptions."""
    
    def __init__(self, detail: str = "Resource not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="RESOURCE_NOT_FOUND",
            **kwargs
        )


class ConflictException(CustomHTTPException):
    """Resource conflict exceptions."""
    
    def __init__(self, detail: str = "Resource conflict", **kwargs):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="RESOURCE_CONFLICT",
            **kwargs
        )


class RateLimitException(CustomHTTPException):
    """Rate limiting exceptions."""
    
    def __init__(self, detail: str = "Rate limit exceeded", **kwargs):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED",
            **kwargs
        )


class ExternalServiceException(CustomHTTPException):
    """External service related exceptions."""
    
    def __init__(self, detail: str = "External service error", service_name: str = "unknown", **kwargs):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="EXTERNAL_SERVICE_ERROR",
            service_name=service_name,
            **kwargs
        )


class ConfigurationException(CustomHTTPException):
    """Configuration related exceptions."""
    
    def __init__(self, detail: str = "Configuration error", **kwargs):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="CONFIGURATION_ERROR",
            **kwargs
        )


# Utility functions for common exceptions
def raise_authentication_error(message: str = "Invalid credentials"):
    """Raise authentication error."""
    raise AuthenticationException(detail=message)


def raise_authorization_error(message: str = "Insufficient permissions"):
    """Raise authorization error."""
    raise AuthorizationException(detail=message)


def raise_not_found_error(resource: str = "Resource"):
    """Raise resource not found error."""
    raise ResourceNotFoundException(detail=f"{resource} not found")


def raise_validation_error(field: str, message: str):
    """Raise validation error."""
    raise ValidationException(detail=f"{field}: {message}")


def raise_rate_limit_error(limit: int, window: str = "minute"):
    """Raise rate limit error."""
    raise RateLimitException(detail=f"Rate limit exceeded: {limit} requests per {window}")


def raise_external_service_error(service: str, error: str):
    """Raise external service error."""
    raise ExternalServiceException(
        detail=f"Error communicating with {service}: {error}",
        service_name=service
    )