"""
Authentication Models - JWT tokens and authentication data
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """JWT token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: Optional[Dict[str, Any]] = None

class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    scopes: Optional[list] = []
    
class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

class TokenBlacklist(BaseModel):
    """Blacklisted token model"""
    token: str
    blacklisted_at: datetime
    expires_at: datetime
    user_id: str

class SessionInfo(BaseModel):
    """User session information"""
    session_id: str
    user_id: str
    created_at: datetime
    last_accessed: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
