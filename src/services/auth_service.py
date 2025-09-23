"""
Authentication Service - User authentication and JWT management
Complete implementation with database integration
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
import os
from passlib.context import CryptContext

from ..models.user import User, UserCreate, UserResponse
from ..db.models.user import UserORM
from ..core.database_config import get_db_session

# Configuration from environment
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    """Complete authentication service with database integration"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT refresh token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    async def get_user_by_email(self, email: str) -> Optional[UserORM]:
        """Get user by email from database"""
        try:
            result = await self.db.execute(
                select(UserORM).where(UserORM.email == email)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def get_user_by_username(self, username: str) -> Optional[UserORM]:
        """Get user by username from database"""
        try:
            result = await self.db.execute(
                select(UserORM).where(UserORM.username == username)
            )
            user = result.scalar_one_or_none()
            if user:
                # Ensure all attributes are loaded
                await self.db.refresh(user)
            return user
        except Exception:
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[UserORM]:
        """Get user by ID from database"""
        try:
            result = await self.db.execute(
                select(UserORM).where(UserORM.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def create_user(self, user_data: UserCreate) -> UserORM:
        """Create new user in database"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        existing_username = await self.get_user_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )

        # Create new user
        hashed_password = self.get_password_hash(user_data.password)

        db_user = UserORM(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        return db_user

    async def authenticate_user(self, username: str, password: str) -> Optional[UserORM]:
        """Authenticate user credentials"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def update_last_login(self, user_id: str):
        """Update last login timestamp"""
        try:
            user = await self.get_user_by_id(user_id)
            if user:
                user.last_login = datetime.utcnow()
                await self.db.commit()
                await self.db.refresh(user)
        except Exception as e:
            # Log error but don't fail the login
            print(f"Failed to update last login: {e}")

    def create_password_reset_token(self, email: str) -> str:
        """Create password reset token"""
        data = {"email": email, "type": "reset"}
        expire = datetime.utcnow() + timedelta(hours=1)
        data.update({"exp": expire})
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify password reset token and return email"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") == "reset":
                return payload.get("email")
        except jwt.JWTError:
            pass
        return None

# Dependency for getting current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> UserORM:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    auth_service = AuthService(db)

    payload = auth_service.verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user

# Optional dependency for getting current user (returns None if not authenticated)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[UserORM]:
    """Get current authenticated user or None if not authenticated"""
    if not credentials:
        return None

    try:
        auth_service = AuthService(db)
        payload = auth_service.verify_token(credentials.credentials)
        if payload is None:
            return None

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        user = await auth_service.get_user_by_id(user_id)
        return user
    except Exception:
        return None
