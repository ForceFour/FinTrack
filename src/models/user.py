"""
User Models - Data models for user management and authentication
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    """Base user model with common fields"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False

class UserCreate(UserBase):
    """User creation model with password"""
    password: str
    confirm_password: Optional[str] = None

class UserUpdate(BaseModel):
    """User update model - all fields optional"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """User response model - safe for API responses"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class User(UserBase):
    """Complete user model including internal fields"""
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = {}
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str
    confirm_password: str

class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str
    confirm_password: str
