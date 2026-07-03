from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data schema."""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "username": "johndoe",
                    "full_name": "John Doe",
                    "role": "employee"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request schema."""
    refresh_token: Optional[str] = None


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str


class ApiKeyCreate(BaseModel):
    """API key creation schema."""
    name: str
    description: Optional[str] = None
    expires_in_days: Optional[int] = None


class ApiKeyResponse(BaseModel):
    """API key response schema."""
    id: int
    name: str
    description: Optional[str]
    key: str  # Only returned on creation
    key_preview: str  # Masked version for listing
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    last_used_at: Optional[datetime]
    
    class Config:
        orm_mode = True


class SessionInfo(BaseModel):
    """Session information schema."""
    user_id: int
    email: str
    role: str
    department_id: Optional[int]
    is_active: bool
    last_login: Optional[datetime]
    session_duration: int  # in seconds
    ip_address: Optional[str]
    user_agent: Optional[str]