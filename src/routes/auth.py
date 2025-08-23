"""
Backend API Routes - Authentication and User Management
Handles user authentication, registration, and profile management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.user import User, UserCreate, UserUpdate, UserResponse, LoginRequest
from ..models.auth import Token, TokenData
from ..services.auth_service import AuthService, get_current_user
from ..core.database import get_db_session
from ..core.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db = Depends(get_db_session)
):
    """
    Register a new user account
    """
    try:
        auth_service = AuthService(db)
        
        # Check if user already exists
        existing_user = await auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check username availability
        existing_username = await auth_service.get_user_by_username(user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        new_user = await auth_service.create_user(user_data)
        
        return UserResponse.from_orm(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login_user(
    login_data: LoginRequest,
    db = Depends(get_db_session)
):
    """
    Authenticate user and return access token
    """
    try:
        auth_service = AuthService(db)
        
        # Authenticate user
        user = await auth_service.authenticate_user(
            login_data.username, 
            login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Generate refresh token
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = auth_service.create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=refresh_token_expires
        )
        
        # Update last login
        await auth_service.update_last_login(user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": UserResponse.from_orm(user).dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token_data: Dict[str, str],
    db = Depends(get_db_session)
):
    """
    Refresh access token using refresh token
    """
    try:
        auth_service = AuthService(db)
        
        refresh_token = refresh_token_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required"
            )
        
        # Verify refresh token
        token_data = auth_service.verify_refresh_token(refresh_token)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user
        user = await auth_service.get_user_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Logout user and invalidate token
    """
    try:
        auth_service = AuthService(db)
        
        # Add token to blacklist
        await auth_service.blacklist_token(credentials.credentials)
        
        return {
            "status": "success",
            "message": "Successfully logged out"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user: User = Depends(get_current_user)
):
    """
    Get current user profile
    """
    return UserResponse.from_orm(user)

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Update current user profile
    """
    try:
        auth_service = AuthService(db)
        
        # If email is being updated, check if it's already taken
        if user_update.email and user_update.email != user.email:
            existing_user = await auth_service.get_user_by_email(user_update.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        
        # If username is being updated, check if it's already taken
        if user_update.username and user_update.username != user.username:
            existing_user = await auth_service.get_user_by_username(user_update.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        updated_user = await auth_service.update_user(
            user.id, 
            user_update.dict(exclude_unset=True)
        )
        
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/change-password")
async def change_password(
    password_data: Dict[str, str],
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Change user password
    """
    try:
        auth_service = AuthService(db)
        
        current_password = password_data.get("current_password")
        new_password = password_data.get("new_password")
        
        if not current_password or not new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password and new password are required"
            )
        
        # Verify current password
        if not auth_service.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        await auth_service.update_password(user.id, new_password)
        
        return {
            "status": "success",
            "message": "Password updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/forgot-password")
async def forgot_password(
    email_data: Dict[str, str],
    db = Depends(get_db_session)
):
    """
    Send password reset email
    """
    try:
        auth_service = AuthService(db)
        
        email = email_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        # Check if user exists
        user = await auth_service.get_user_by_email(email)
        if not user:
            # Don't reveal if email exists or not for security
            return {
                "status": "success",
                "message": "If the email exists, a reset link has been sent"
            }
        
        # Generate reset token
        reset_token = auth_service.create_password_reset_token(email)
        
        # In a real app, you would send an email here
        # For now, we'll just return the token (DON'T DO THIS IN PRODUCTION)
        return {
            "status": "success",
            "message": "Password reset token generated",
            "reset_token": reset_token  # Remove this in production
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/reset-password")
async def reset_password(
    reset_data: Dict[str, str],
    db = Depends(get_db_session)
):
    """
    Reset password using reset token
    """
    try:
        auth_service = AuthService(db)
        
        reset_token = reset_data.get("reset_token")
        new_password = reset_data.get("new_password")
        
        if not reset_token or not new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token and new password are required"
            )
        
        # Verify reset token
        email = auth_service.verify_password_reset_token(reset_token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Get user by email
        user = await auth_service.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        await auth_service.update_password(user.id, new_password)
        
        return {
            "status": "success",
            "message": "Password reset successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/account")
async def delete_account(
    confirmation_data: Dict[str, str],
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Delete user account (requires password confirmation)
    """
    try:
        auth_service = AuthService(db)
        
        password = confirmation_data.get("password")
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password confirmation is required"
            )
        
        # Verify password
        if not auth_service.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is incorrect"
            )
        
        # Delete user account
        await auth_service.delete_user(user.id)
        
        return {
            "status": "success",
            "message": "Account deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/sessions")
async def get_active_sessions(
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get active user sessions
    """
    try:
        auth_service = AuthService(db)
        
        sessions = await auth_service.get_user_sessions(user.id)
        
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Revoke a specific user session
    """
    try:
        auth_service = AuthService(db)
        
        success = await auth_service.revoke_session(session_id, user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {
            "status": "success",
            "message": "Session revoked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
