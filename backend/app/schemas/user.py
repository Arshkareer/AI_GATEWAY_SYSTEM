from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str
    full_name: str
    role: UserRole = UserRole.EMPLOYEE
    department_id: Optional[int] = None
    monthly_budget: float = 0.0


class UserCreate(UserBase):
    """User creation schema."""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department_id: Optional[int] = None
    monthly_budget: Optional[float] = None
    is_active: Optional[bool] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if not v.isalnum():
                raise ValueError('Username must contain only alphanumeric characters')
        return v


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    is_verified: bool
    total_requests: int
    total_cost: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v


class UserStats(BaseModel):
    """User statistics schema."""
    user_id: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_cost: float
    total_tokens: int
    avg_latency_ms: float
    most_used_model: Optional[str]
    most_used_provider: Optional[str]
    
    class Config:
        orm_mode = True