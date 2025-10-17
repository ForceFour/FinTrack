"""
User Settings API - Manage user preferences and spending limits
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ..core.database_config import get_db_client

router = APIRouter(prefix="/user-settings", tags=["user-settings"])


class UserSettingsUpdate(BaseModel):
    """User settings update schema"""
    spending_limits: Optional[Dict[str, float]] = None
    notifications: Optional[Dict[str, bool]] = None
    preferences: Optional[Dict[str, str]] = None


@router.get("/{user_id}")
async def get_user_settings(user_id: str):
    """
    Get user settings including spending limits
    """
    try:
        supabase = await get_db_client()

        # Get user profile which contains spending limits
        try:
            result = supabase.table("user_profile").select("*").eq("user_id", user_id).execute()

            if not result.data or len(result.data) == 0:
                # Return default settings for new users
                return {
                    "status": "success",
                    "user_id": user_id,
                    "spending_limits": {},
                    "notifications": {
                        "email_alerts": True,
                        "push_notifications": True
                    },
                    "preferences": {
                        "currency": "LKR",
                        "currency_symbol": "LKR"
                    }
                }

            # Extract spending limits and preferences from user profile
            user_data = result.data[0]  # Get first record
            spending_limits = user_data.get("spending_limits", {})
            preferences = user_data.get("preferences", {
                "currency": "LKR",
                "currency_symbol": "LKR"
            })

            return {
                "status": "success",
                "user_id": user_id,
                "spending_limits": spending_limits,
                "notifications": {
                    "email_alerts": True,
                    "push_notifications": True
                },
                "preferences": preferences
            }
        except Exception as query_error:
            # If table doesn't exist or query fails, return default settings
            return {
                "status": "success",
                "user_id": user_id,
                "spending_limits": {},
                "notifications": {
                    "email_alerts": True,
                    "push_notifications": True
                },
                "preferences": {
                    "currency": "LKR",
                    "currency_symbol": "LKR"
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user settings: {str(e)}")


@router.put("/{user_id}")
async def update_user_settings(user_id: str, settings: UserSettingsUpdate):
    """
    Update user settings including spending limits
    """
    try:
        supabase = await get_db_client()

        # Check if user profile exists
        existing = supabase.table("user_profile").select("*").eq("user_id", user_id).execute()

        update_data: Dict[str, Any] = {}

        if settings.spending_limits is not None:
            update_data["spending_limits"] = settings.spending_limits

        if settings.preferences is not None:
            update_data["preferences"] = settings.preferences

        if settings.notifications is not None:
            # Store notifications preferences if we add a column for it
            pass

        if not existing.data:
            # Create new user profile
            update_data["user_id"] = user_id
            update_data["total_transactions"] = 0
            update_data["categories_seen"] = []
            update_data["merchants_seen"] = []
            update_data["average_transaction_amount"] = 0.0

            result = supabase.table("user_profile").insert(update_data).execute()
        else:
            # Update existing profile
            result = supabase.table("user_profile").update(update_data).eq("user_id", user_id).execute()

        return {
            "status": "success",
            "message": "Settings updated successfully",
            "user_id": user_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user settings: {str(e)}")
