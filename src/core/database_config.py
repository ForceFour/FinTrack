"""
Database Configuration for FinTrack
Supports PostgreSQL, SQLite with async support and proper session management
"""

import os
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseSettings:
    """Database configuration settings"""

    def __init__(self):
        # Database connection settings
        self.db_type = os.getenv("DB_TYPE", "sqlite")
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "5432"))
        self.db_user = os.getenv("DB_USER", "")
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.db_name = os.getenv("DB_NAME", "fintrack")

        # Connection settings
        self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.db_pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.db_pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))

        # Environment-specific URL override
        self.database_url = self._build_database_url()

    def _build_database_url(self) -> str:
        """Build database URL if not provided directly"""
        # Check for direct URL first
        direct_url = os.getenv("DATABASE_URL")
        if direct_url:
            return direct_url

        if self.db_type == "sqlite":
            return "sqlite+aiosqlite:///./data/fintrack.db"

        elif self.db_type == "postgresql":
            # URL encode password to handle special characters
            if self.db_password:
                password = quote_plus(self.db_password)
                auth = f"{self.db_user}:{password}@"
            elif self.db_user:
                auth = f"{self.db_user}@"
            else:
                auth = ""

            return f"postgresql+asyncpg://{auth}{self.db_host}:{self.db_port}/{self.db_name}"

        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

# Global database settings
db_settings = DatabaseSettings()

# SQLAlchemy base class
Base = declarative_base()

# Import models to ensure they're registered with Base
# This is crucial for table creation
try:
    from ..db.models.transaction import TransactionORM
    from ..db.models.user import UserORM
    logger.info("✅ SQLAlchemy ORM models imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import ORM models: {e}")
    # Models might not exist yet during initial setup

class DatabaseManager:
    """Database connection and session manager"""

    def __init__(self, settings: DatabaseSettings = None):
        self.settings = settings or db_settings
        self.engine = None
        self.session_factory = None
        self._initialized = False

    async def initialize(self):
        """Initialize database engine and session factory"""
        if self._initialized:
            return

        try:
            # Create async engine
            self.engine = create_async_engine(
                self.settings.database_url,
                pool_size=self.settings.db_pool_size,
                max_overflow=self.settings.db_max_overflow,
                pool_timeout=self.settings.db_pool_timeout,
                pool_recycle=self.settings.db_pool_recycle,
                echo=os.getenv("DEBUG", "false").lower() == "true",
                future=True
            )

            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )

            # Test connection
            await self.test_connection()

            self._initialized = True
            logger.info(f"✅ Database initialized: {self.settings.db_type}")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    async def test_connection(self):
        """Test database connection"""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")

        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("✅ Database connection test successful")
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            raise

    async def create_tables(self):
        """Create all database tables"""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created/updated")
        except Exception as e:
            logger.error(f"❌ Failed to create database tables: {e}")
            raise

    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ Database connections closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup"""
        if not self._initialized:
            await self.initialize()

        if not self.session_factory:
            raise RuntimeError("Database session factory not initialized")

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()

# Global database manager instance
db_manager = DatabaseManager()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session
    Usage: session: AsyncSession = Depends(get_db_session)
    """
    async with db_manager.get_session() as session:
        yield session

async def init_database():
    """Initialize database for application startup"""
    try:
        await db_manager.initialize()
        await db_manager.create_tables()
        logger.info("🚀 Database startup complete")
    except Exception as e:
        logger.error(f"❌ Database startup failed: {e}")
        raise

async def close_database():
    """Close database connections for application shutdown"""
    await db_manager.close()
    logger.info("🛑 Database shutdown complete")

# Database health check
async def check_database_health() -> dict:
    """Check database health status"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.fetchone()

        return {
            "status": "healthy",
            "database_type": db_settings.db_type,
            "connection": "active"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database_type": db_settings.db_type,
            "error": str(e)
        }
