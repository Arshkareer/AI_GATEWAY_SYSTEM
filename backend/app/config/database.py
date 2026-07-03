from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from .settings import settings

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Database:
    """Database connection manager."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        
    def create_all_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


# Global database instance
database = Database()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    yield from database.get_session()