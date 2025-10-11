"""
SQLAlchemy ORM Model for Users
Database table definition for user storage
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
import uuid

from ...core.database_config import Base


class UserORM(Base):
    """
    SQLAlchemy ORM model for profiles table (Supabase auth.users integration)
    """
    __tablename__ = "profiles"

    # Primary key - matches Supabase auth.users.id
    id = Column(
        String,
        primary_key=True,
        index=True
    )

    # User profile
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=True)

    def __repr__(self):
        return f"<UserORM(id='{self.id}', username='{self.username}', email='{self.email}')>"

    def to_dict(self):
        """Convert to dictionary for API responses (excluding sensitive data)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
