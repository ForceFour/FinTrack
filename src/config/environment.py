"""
Environment Configuration Management for FinTrack
Handles local vs shared environment variables securely
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EnvironmentManager:
    """Manages environment configuration with security best practices"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.env_files = [
            self.project_root / ".env.local",    # Local override (not in git)
            self.project_root / ".env.dev",      # Development environment
            self.project_root / ".env",          # Shared/default environment
        ]
        self.load_environment()

    def load_environment(self):
        """Load environment variables from multiple files in priority order"""
        loaded_files = []

        for env_file in self.env_files:
            if env_file.exists():
                load_dotenv(env_file, override=True)
                loaded_files.append(str(env_file))
                logger.info(f"✅ Loaded environment from: {env_file.name}")

        if not loaded_files:
            logger.warning("⚠️ No environment files found, using system environment only")

    def create_local_env_template(self):
        """Create a local environment template if it doesn't exist"""
        local_env_path = self.project_root / ".env.local"

        if local_env_path.exists():
            logger.info("📋 .env.local already exists")
            return

        # Template is already created in the previous step
        logger.info("📋 .env.local template should be manually created if needed")

class FinTrackSettings:
    """Application settings with environment variable support"""

    def __init__(self):
        # API Configuration
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))

        # Security
        self.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")
        self.allowed_origins = self._parse_allowed_origins(os.getenv("ALLOWED_ORIGINS", '["*"]'))

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/fintrack.log")

        # AI/LangChain Configuration
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
        self.langchain_project = os.getenv("LANGCHAIN_PROJECT", "fintrack-workflows")
        self.langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"

        # Workflow Configuration
        self.default_workflow_mode = os.getenv("DEFAULT_WORKFLOW_MODE", "full_pipeline")
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        self.workflow_timeout_seconds = int(os.getenv("WORKFLOW_TIMEOUT_SECONDS", "300"))

        # Feature Flags
        self.enable_background_processing = os.getenv("ENABLE_BACKGROUND_PROCESSING", "true").lower() == "true"
        self.enable_parallel_processing = os.getenv("ENABLE_PARALLEL_PROCESSING", "true").lower() == "true"
        self.enable_workflow_persistence = os.getenv("ENABLE_WORKFLOW_PERSISTENCE", "true").lower() == "true"
        self.enable_experimental_features = os.getenv("ENABLE_EXPERIMENTAL_FEATURES", "false").lower() == "true"

    def _parse_allowed_origins(self, v: str) -> List[str]:
        """Parse CORS allowed origins from string or list"""
        import json
        try:
            return json.loads(v)
        except:
            # Handle comma-separated string: "origin1,origin2"
            return [origin.strip() for origin in v.split(",")]

# Global settings instance
env_manager = EnvironmentManager()
settings = FinTrackSettings()

def get_settings() -> FinTrackSettings:
    """Get application settings"""
    return settings

def setup_environment():
    """Setup environment configuration for the application"""
    logger.info("🔧 Setting up environment configuration...")

    # Create local environment template
    env_manager.create_local_env_template()

    # Log configuration summary
    logger.info(f"✅ Environment setup complete:")
    logger.info(f"   - Debug mode: {settings.debug}")
    logger.info(f"   - API: {settings.api_host}:{settings.api_port}")
    logger.info(f"   - Log level: {settings.log_level}")
    logger.info(f"   - Workflow mode: {settings.default_workflow_mode}")
    logger.info(f"   - Background processing: {settings.enable_background_processing}")

if __name__ == "__main__":
    # Run environment setup
    setup_environment()
