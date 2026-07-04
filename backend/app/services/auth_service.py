from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password, get_password_hash
from app.core.exceptions import AuthenticationException


class AuthService:
    """Authentication service for user management."""
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    def create_user(
        db: Session,
        email: str,
        username: str,
        full_name: str,
        password: str,
        **kwargs
    ) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(password)
        
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            **kwargs
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def update_password(db: Session, user: User, new_password: str) -> bool:
        """Update user password."""
        try:
            user.hashed_password = get_password_hash(new_password)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False