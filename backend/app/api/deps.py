from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.config import get_db, get_redis, settings
from app.core.security import verify_token
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.models.user import User, UserRole
from app.config.redis import RedisClient

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise AuthenticationException("Invalid token")
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise AuthenticationException("Invalid token payload")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise AuthenticationException("User not found")
        
        if not user.is_active:
            raise AuthenticationException("User account is disabled")
        
        return user
        
    except JWTError:
        raise AuthenticationException("Could not validate credentials")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise AuthenticationException("User account is disabled")
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if they are an admin."""
    if not current_user.is_admin:
        raise AuthorizationException("Admin access required")
    return current_user


async def get_user_with_permission(
    permission: str,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current user if they have specific permission."""
    
    # Define permissions based on user roles
    permissions = {
        UserRole.ADMIN: [
            "read:users", "write:users", "delete:users",
            "read:departments", "write:departments", "delete:departments",
            "read:analytics", "write:analytics",
            "read:gateway", "write:gateway",
            "admin:all"
        ],
        UserRole.EMPLOYEE: [
            "read:analytics", "read:gateway", "write:gateway"
        ],
        UserRole.VIEWER: [
            "read:analytics", "read:gateway"
        ]
    }
    
    user_permissions = permissions.get(current_user.role, [])
    
    if permission not in user_permissions:
        raise AuthorizationException(f"Permission '{permission}' required")
    
    return current_user


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def permission_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        return get_user_with_permission(permission, current_user)
    
    return Depends(permission_dependency)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if token is provided (optional authentication)."""
    
    if credentials is None:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            return None
        
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        return user
        
    except JWTError:
        return None


class RateLimiter:
    """Rate limiting dependency."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
    
    async def __call__(
        self,
        request: Request,
        redis: RedisClient = Depends(get_redis),
        current_user: Optional[User] = Depends(get_optional_user)
    ):
        # Create rate limit key
        if current_user:
            key = f"rate_limit:user:{current_user.id}"
        else:
            # Use IP address for unauthenticated requests
            client_ip = request.client.host
            key = f"rate_limit:ip:{client_ip}"
        
        # Check current count
        current_count = await redis.get(key)
        
        if current_count is None:
            # First request in the window
            await redis.set(key, "1", expire=60)
            return
        
        if int(current_count) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
            )
        
        # Increment counter
        await redis.increment(key)


def create_rate_limiter(requests_per_minute: int = 60):
    """Create a rate limiter with custom limit."""
    return RateLimiter(requests_per_minute)


async def log_request(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Log API request for monitoring."""
    from app.core.logging import request_logger
    
    request_logger.log_request(
        method=request.method,
        path=request.url.path,
        user_id=current_user.id if current_user else None,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )


# Common dependencies
CommonDeps = {
    "current_user": Depends(get_current_active_user),
    "db": Depends(get_db),
    "redis": Depends(get_redis),
}

AdminDeps = {
    "current_user": Depends(get_admin_user),
    "db": Depends(get_db),
    "redis": Depends(get_redis),
}

# Rate limited endpoints
rate_limit_standard = create_rate_limiter(60)  # 60 requests per minute
rate_limit_gateway = create_rate_limiter(120)  # 120 requests per minute for gateway
rate_limit_strict = create_rate_limiter(10)   # 10 requests per minute for admin operations