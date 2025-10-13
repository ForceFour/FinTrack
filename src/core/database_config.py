"""
Database Configuration for FinTrack
Supabase client integration for PostgreSQL with async support
"""

import os
import logging
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# SQLAlchemy Base for backward compatibility (to be removed after full migration)
Base = declarative_base()

class DatabaseSettings:
    """Database configuration settings for Supabase"""

    def __init__(self):
        # Supabase configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")
        if not self.supabase_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")

# Global database settings
db_settings = DatabaseSettings()

class DatabaseManager:
    """Supabase client manager"""

    def __init__(self, settings: DatabaseSettings = None):
        self.settings = settings or db_settings
        self.client: Optional[Client] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Supabase client"""
        if self._initialized:
            return

        try:
            self.client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_key
            )

            # Test connection
            await self.test_connection()

            self._initialized = True
            logger.info("Supabase client initialized successfully")

        except Exception as e:
            logger.error(f"❌ Supabase client initialization failed: {e}")
            raise

    async def test_connection(self):
        """Test Supabase connection"""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")

        try:
            # Test connection by trying to select from profiles table
            response = self.client.table("profiles").select("id").limit(1).execute()
            logger.info("Supabase connection test successful")
        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            raise

    async def close(self):
        """Close Supabase client connections"""
        if self.client:
            # Supabase client doesn't have explicit close method
            # but we can set it to None
            self.client = None
            logger.info("Supabase client connections closed")

    def get_client(self) -> Client:
        """Get Supabase client instance"""
        if not self._initialized or not self.client:
            raise RuntimeError("Database not initialized")
        return self.client

# Global database manager instance
db_manager = DatabaseManager()

async def get_db_client() -> Client:
    """
    Dependency for FastAPI to get Supabase client
    Usage: client: Client = Depends(get_db_client)
    """
    return db_manager.get_client()

async def get_db_session():
    """
    DEPRECATED: Use get_db_client() instead.
    This function is kept for backward compatibility during migration.
    """
    raise NotImplementedError("SQLAlchemy session is deprecated. Use get_db_client() for Supabase operations.")

async def init_database():
    """Initialize database for application startup"""
    try:
        await db_manager.initialize()
        logger.info("Supabase client startup complete")
    except Exception as e:
        logger.error(f"❌ Supabase client startup failed: {e}")
        raise

async def close_database():
    """Close database connections for application shutdown"""
    await db_manager.close()
    logger.info("Supabase client shutdown complete")

# Database health check
async def check_database_health() -> dict:
    """Check database health status"""
    try:
        client = db_manager.get_client()
        # Test connection
        response = client.table("profiles").select("id").limit(1).execute()

        return {
            "status": "healthy",
            "database_type": "supabase",
            "connection": "active"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database_type": "supabase",
            "error": str(e)
        }
