from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import get_db, get_current_user, get_redis, rate_limit_standard
from app.config import settings
from app.config.redis import RedisClient
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.exceptions import AuthenticationException, ValidationException
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    RefreshTokenRequest,
    LogoutRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    SessionInfo
)
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    _: Any = Depends(rate_limit_standard)
):
    """Authenticate user and return tokens."""
    
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise AuthenticationException("Incorrect email or password")
    
    if not user.is_active:
        raise AuthenticationException("Account is disabled")
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if login_data.remember_me:
        access_token_expires = timedelta(days=7)  # Longer expiry for "remember me"
    
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user.id, "email": user.email}
    )
    
    # Store refresh token in Redis
    await redis.set(f"refresh_token:{user.id}", refresh_token, expire=604800)  # 7 days
    
    # Update user's last login (in a real app, you might track this)
    # user.last_login = datetime.utcnow()
    # db.commit()
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_token_expires.total_seconds()),
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "department_id": user.department_id,
            "is_active": user.is_active
        }
    )


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: Any = Depends(rate_limit_standard)
):
    """Register a new user."""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise ValidationException("Email already registered")
        else:
            raise ValidationException("Username already taken")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        department_id=user_data.department_id,
        monthly_budget=user_data.monthly_budget,
        is_active=True,  # Auto-activate for now
        is_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    _: Any = Depends(rate_limit_standard)
):
    """Refresh access token using refresh token."""
    
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise AuthenticationException("Invalid refresh token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Invalid refresh token payload")
    
    # Check if refresh token exists in Redis
    stored_token = await redis.get(f"refresh_token:{user_id}")
    if not stored_token or stored_token != refresh_data.refresh_token:
        raise AuthenticationException("Refresh token not found or expired")
    
    # Get user
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise AuthenticationException("User not found or disabled")
    
    # Create new access token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role}
    )
    
    # Create new refresh token
    new_refresh_token = create_refresh_token(
        data={"sub": user.id, "email": user.email}
    )
    
    # Update refresh token in Redis
    await redis.set(f"refresh_token:{user.id}", new_refresh_token, expire=604800)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "department_id": user.department_id,
            "is_active": user.is_active
        }
    )


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    redis: RedisClient = Depends(get_redis),
    _: Any = Depends(rate_limit_standard)
):
    """Logout user and invalidate tokens."""
    
    # Remove refresh token from Redis
    await redis.delete(f"refresh_token:{current_user.id}")
    
    # In a more sophisticated implementation, you might maintain a blacklist
    # of revoked access tokens until they expire
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.get("/session", response_model=SessionInfo)
async def get_session_info(
    current_user: User = Depends(get_current_user),
    redis: RedisClient = Depends(get_redis)
):
    """Get current session information."""
    
    # Check if refresh token exists (indicates active session)
    has_refresh_token = await redis.exists(f"refresh_token:{current_user.id}")
    
    return SessionInfo(
        user_id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        department_id=current_user.department_id,
        is_active=current_user.is_active,
        last_login=None,  # Would need to be tracked in User model
        session_duration=0,  # Would need session start time
        ip_address=None,  # Would need to be passed from request
        user_agent=None   # Would need to be passed from request
    )


@router.post("/password-reset/request")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
    _: Any = Depends(rate_limit_standard)
):
    """Request password reset."""
    
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    # Always return success to prevent email enumeration
    message = "If the email exists, a password reset link has been sent"
    
    if user and user.is_active:
        # In a real implementation, you would:
        # 1. Generate a secure reset token
        # 2. Store it with expiration (Redis or database)
        # 3. Send email with reset link
        pass
    
    return {"message": message}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
    _: Any = Depends(rate_limit_standard)
):
    """Confirm password reset with token."""
    
    # In a real implementation, you would:
    # 1. Verify the reset token
    # 2. Check if it's not expired
    # 3. Update the user's password
    # 4. Invalidate the reset token
    
    # For now, return a placeholder response
    return {"message": "Password reset functionality not implemented"}


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db),
    _: Any = Depends(rate_limit_standard)
):
    """Verify email address with token."""
    
    # In a real implementation, you would:
    # 1. Verify the email verification token
    # 2. Mark user as verified
    
    return {"message": "Email verification functionality not implemented"}