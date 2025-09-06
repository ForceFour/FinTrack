"""
Database Configuration and Session Management
Production-ready database setup with PostgreSQL/SQLite support
"""

# Re-export from the new database_config module
from .database_config import (
    DatabaseSettings,
    DatabaseManager,
    Base,
    db_manager,
    db_settings,
    get_db_session,
    init_database,
    close_database,
    check_database_health
)

__all__ = [
    "DatabaseSettings",
    "DatabaseManager",
    "Base",
    "db_manager",
    "db_settings",
    "get_db_session",
    "init_database",
    "close_database",
    "check_database_health"
]
