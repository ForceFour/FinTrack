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
            result = supabase.table("profiles").select("*").eq("id", user_id).execute()

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
                        "currency_symbol": "Rs."
                    }
                }

            # Extract spending limits and preferences from user profile
            user_data = result.data[0]  # Get first record
            spending_limits = user_data.get("spending_limits", {})
            preferences = user_data.get("preferences", {
                "currency": "LKR",
                "currency_symbol": "Rs."
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
            print(f"Error querying profiles: {query_error}")
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
                    "currency_symbol": "Rs."
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
        existing = supabase.table("profiles").select("*").eq("id", user_id).execute()

        update_data: Dict[str, Any] = {}

        if settings.spending_limits is not None:
            update_data["spending_limits"] = settings.spending_limits

        if settings.preferences is not None:
            update_data["preferences"] = settings.preferences

        if settings.notifications is not None:
            # Store notifications preferences if we add a column for it
            pass

        if not existing.data:
            # User profile doesn't exist - this shouldn't happen but return error
            raise HTTPException(status_code=404, detail="User profile not found")
        else:
            # Update existing profile
            result = supabase.table("profiles").update(update_data).eq("id", user_id).execute()

        return {
            "status": "success",
            "message": "Settings updated successfully",
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user settings: {str(e)}")
