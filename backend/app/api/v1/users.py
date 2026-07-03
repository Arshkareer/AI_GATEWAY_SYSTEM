from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_current_active_user, get_admin_user, get_db, require_permission
from app.core.security import get_password_hash
from app.core.exceptions import ValidationException, ResourceNotFoundException
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, PasswordChange, UserStats

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(require_permission("read:users")),
    db: Session = Depends(get_db)
):
    """List users with filtering and pagination."""
    
    query = db.query(User)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.username.ilike(search_term))
        )
    
    if department_id is not None:
        query = query.filter(User.department_id == department_id)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Get users with pagination
    users = query.offset(skip).limit(limit).all()
    
    return users


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    
    # Users can only update certain fields for themselves
    allowed_fields = ["email", "username", "full_name"]
    
    update_data = user_update.dict(exclude_unset=True)
    
    # Remove fields that users cannot update themselves
    for field in list(update_data.keys()):
        if field not in allowed_fields:
            del update_data[field]
    
    # Check for duplicate email/username
    if "email" in update_data:
        existing = db.query(User).filter(
            User.email == update_data["email"],
            User.id != current_user.id
        ).first()
        if existing:
            raise ValidationException("Email already in use")
    
    if "username" in update_data:
        existing = db.query(User).filter(
            User.username == update_data["username"],
            User.id != current_user.id
        ).first()
        if existing:
            raise ValidationException("Username already taken")
    
    # Update user
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/me/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    
    from app.core.security import verify_password
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise ValidationException("Current password is incorrect")
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_permission("read:users")),
    db: Session = Depends(get_db)
):
    """Get specific user by ID."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException(f"User with ID {user_id} not found")
    
    return user


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission("write:users")),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    
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
        is_active=True,
        is_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_permission("write:users")),
    db: Session = Depends(get_db)
):
    """Update user (admin only)."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException(f"User with ID {user_id} not found")
    
    update_data = user_update.dict(exclude_unset=True)
    
    # Check for duplicate email/username
    if "email" in update_data:
        existing = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id
        ).first()
        if existing:
            raise ValidationException("Email already in use")
    
    if "username" in update_data:
        existing = db.query(User).filter(
            User.username == update_data["username"],
            User.id != user_id
        ).first()
        if existing:
            raise ValidationException("Username already taken")
    
    # Update user
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission("delete:users")),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)."""
    
    if user_id == current_user.id:
        raise ValidationException("Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException(f"User with ID {user_id} not found")
    
    # Soft delete - just deactivate the user
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.username} has been deactivated"}


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user usage statistics."""
    
    # Users can only view their own stats unless they're admin
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other users' statistics"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException(f"User with ID {user_id} not found")
    
    # TODO: Calculate real statistics from request logs
    # This will be implemented when we have the analytics engine
    
    return UserStats(
        user_id=user.id,
        total_requests=user.total_requests,
        successful_requests=user.total_requests,  # Placeholder
        failed_requests=0,  # Placeholder
        total_cost=user.total_cost,
        total_tokens=0,  # Placeholder
        avg_latency_ms=1200.0,  # Placeholder
        most_used_model="gpt-3.5-turbo",  # Placeholder
        most_used_provider="openai"  # Placeholder
    )


@router.post("/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    new_password: str,
    current_user: User = Depends(require_permission("write:users")),
    db: Session = Depends(get_db)
):
    """Reset user password (admin only)."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException(f"User with ID {user_id} not found")
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": f"Password reset for user {user.username}"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_permission("write:users")),
    db: Session = Depends(get_db)
):
    """Activate user account (admin only)."""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException(f"User with ID {user_id} not found")
    
    user.is_active = True
    db.commit()
    
    return {"message": f"User {user.username} has been activated"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_permission("write:users")),
    db: Session = Depends(get_db)
):
    """Deactivate user account (admin only)."""
    
    if user_id == current_user.id:
        raise ValidationException("Cannot deactivate your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException(f"User with ID {user_id} not found")
    
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.username} has been deactivated"}