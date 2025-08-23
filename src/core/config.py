"""
Configuration Settings
TODO: Implement proper configuration management with environment variables
"""

import os
from typing import Optional

class Settings:
    """Application settings"""
    
    # Server settings
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    DEBUG: bool = True
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"  # TODO: Use env var
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./fintrack.db"  # TODO: Use env var
    
    # LLM API settings
    OPENAI_API_KEY: Optional[str] = None  # TODO: Load from env
    ANTHROPIC_API_KEY: Optional[str] = None  # TODO: Load from env
    
    # Agent settings
    MAX_CONCURRENT_AGENTS: int = 5
    AGENT_TIMEOUT: int = 300  # seconds
    
    # Feature flags
    ENABLE_AI_CATEGORIZATION: bool = True
    ENABLE_FRAUD_DETECTION: bool = True
    ENABLE_SUGGESTIONS: bool = True
    
    def __init__(self):
        """Load settings from environment variables"""
        # TODO: Implement proper environment variable loading
        self.SECRET_KEY = os.getenv("SECRET_KEY", self.SECRET_KEY)
        self.DATABASE_URL = os.getenv("DATABASE_URL", self.DATABASE_URL)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        
        # Parse boolean environment variables
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
        self.ENABLE_AI_CATEGORIZATION = os.getenv("ENABLE_AI_CATEGORIZATION", "true").lower() == "true"
        self.ENABLE_FRAUD_DETECTION = os.getenv("ENABLE_FRAUD_DETECTION", "true").lower() == "true"
        self.ENABLE_SUGGESTIONS = os.getenv("ENABLE_SUGGESTIONS", "true").lower() == "true"

# Global settings instance
settings = Settings()
