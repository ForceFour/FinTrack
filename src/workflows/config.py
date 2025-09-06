"""
LangGraph Workflow Configuration
Centralized configuration for all workflow settings and agent initialization
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
import logging
from pydantic import BaseModel
from config.settings import get_settings

logger = logging.getLogger(__name__)

class WorkflowMode(Enum):
    """Workflow execution modes"""
    FULL_PIPELINE = "full_pipeline"           # Complete 7-agent pipeline
    QUICK_CLASSIFICATION = "quick_class"      # Skip pattern analysis
    INGESTION_ONLY = "ingestion_only"         # Only process and clean data
    VALIDATION_ONLY = "validation_only"       # Quick validation check
    BACKGROUND_PROCESSING = "background"      # Async background processing

class LangGraphConfig(BaseModel):
    """Configuration for LangGraph workflows"""
    
    # API Keys
    groq_api_key: Optional[str] = None
    langgraph_api_key: Optional[str] = None
    langsmith_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # LangSmith Tracing
    enable_tracing: bool = True
    langsmith_project: str = "fintrack-workflows"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    
    # Workflow Settings
    default_mode: WorkflowMode = WorkflowMode.FULL_PIPELINE
    enable_background_processing: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300
    
    # Agent Settings
    enable_parallel_processing: bool = True
    confidence_threshold: float = 0.7
    max_transactions_per_batch: int = 100
    
    # Database Settings
    enable_persistence: bool = True
    checkpoint_interval: int = 5  # Save state every 5 steps
    
    # Monitoring Settings
    enable_monitoring: bool = True
    log_level: str = "INFO"
    metrics_collection: bool = True

def load_workflow_config() -> LangGraphConfig:
    """
    Load workflow configuration from environment and settings
    """
    try:
        # Get base settings
        settings = get_settings()
        
        # Create configuration with environment overrides
        config = LangGraphConfig(
            groq_api_key=settings.groq_api_key,
            langgraph_api_key=getattr(settings, 'langgraph_api_key', None),
            langsmith_api_key=getattr(settings, 'langsmith_api_key', None),
            openai_api_key=getattr(settings, 'openai_api_key', None),
            
            # Override with environment variables if available
            enable_tracing=os.getenv('LANGCHAIN_TRACING_V2', 'true').lower() == 'true',
            langsmith_project=os.getenv('LANGCHAIN_PROJECT', 'fintrack-workflows'),
            langsmith_endpoint=os.getenv('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com'),
            
            # Workflow settings from environment
            default_mode=WorkflowMode(os.getenv('DEFAULT_WORKFLOW_MODE', 'full_pipeline')),
            enable_background_processing=os.getenv('ENABLE_BACKGROUND_PROCESSING', 'true').lower() == 'true',
            max_retries=int(os.getenv('MAX_WORKFLOW_RETRIES', '3')),
            timeout_seconds=int(os.getenv('WORKFLOW_TIMEOUT_SECONDS', '300')),
            
            # Agent settings
            enable_parallel_processing=os.getenv('ENABLE_PARALLEL_PROCESSING', 'true').lower() == 'true',
            confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', '0.7')),
            max_transactions_per_batch=int(os.getenv('MAX_TRANSACTIONS_PER_BATCH', '100')),
            
            # Database settings
            enable_persistence=os.getenv('ENABLE_WORKFLOW_PERSISTENCE', 'true').lower() == 'true',
            checkpoint_interval=int(os.getenv('CHECKPOINT_INTERVAL', '5')),
            
            # Monitoring settings
            enable_monitoring=os.getenv('ENABLE_WORKFLOW_MONITORING', 'true').lower() == 'true',
            log_level=os.getenv('WORKFLOW_LOG_LEVEL', 'INFO'),
            metrics_collection=os.getenv('ENABLE_METRICS_COLLECTION', 'true').lower() == 'true'
        )
        
        logger.info("✅ Workflow configuration loaded successfully")
        logger.info(f"🎯 LangSmith tracing: {'enabled' if config.enable_tracing else 'disabled'}")
        logger.info(f"⚡ Default mode: {config.default_mode.value}")
        logger.info(f"🔧 Parallel processing: {'enabled' if config.enable_parallel_processing else 'disabled'}")
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Failed to load workflow configuration: {e}")
        # Return default configuration
        return LangGraphConfig()

def get_agent_config(config: LangGraphConfig) -> Dict[str, Any]:
    """
    Convert workflow config to agent configuration format
    """
    return {
        'groq_api_key': config.groq_api_key,
        'langgraph_api_key': config.langgraph_api_key,
        'langsmith_api_key': config.langsmith_api_key,
        'openai_api_key': config.openai_api_key,
        'enable_tracing': config.enable_tracing,
        'confidence_threshold': config.confidence_threshold,
        'max_retries': config.max_retries,
        'timeout_seconds': config.timeout_seconds,
        'enable_parallel_processing': config.enable_parallel_processing
    }

def get_langgraph_config(config: LangGraphConfig) -> Dict[str, Any]:
    """
    Convert workflow config to LangGraph-specific configuration
    """
    langgraph_config = {
        "configurable": {
            "checkpoint_interval": config.checkpoint_interval,
            "enable_persistence": config.enable_persistence,
            "timeout": config.timeout_seconds,
            "max_retries": config.max_retries
        }
    }
    
    # Add tracing configuration if enabled
    if config.enable_tracing and config.langsmith_api_key:
        langgraph_config["callbacks"] = []
        langgraph_config["metadata"] = {
            "project": config.langsmith_project,
            "endpoint": config.langsmith_endpoint
        }
    
    return langgraph_config

def validate_workflow_config(config: LangGraphConfig) -> Dict[str, Any]:
    """
    Validate workflow configuration and return validation results
    """
    validation_results = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "recommendations": []
    }
    
    # Check API keys
    if not config.groq_api_key:
        validation_results["warnings"].append("Groq API key not configured - NL processing will use fallback methods")
    
    if config.enable_tracing and not config.langsmith_api_key:
        validation_results["warnings"].append("LangSmith tracing enabled but API key not configured")
    
    # Check thresholds
    if config.confidence_threshold < 0.1 or config.confidence_threshold > 1.0:
        validation_results["errors"].append("Confidence threshold must be between 0.1 and 1.0")
        validation_results["valid"] = False
    
    if config.max_transactions_per_batch < 1 or config.max_transactions_per_batch > 1000:
        validation_results["warnings"].append("Max transactions per batch should be between 1 and 1000")
    
    if config.timeout_seconds < 30:
        validation_results["warnings"].append("Workflow timeout is very low, may cause timeouts for complex processing")
    
    # Performance recommendations
    if config.enable_parallel_processing and config.max_transactions_per_batch > 50:
        validation_results["recommendations"].append("Consider reducing batch size when parallel processing is enabled")
    
    if not config.enable_persistence:
        validation_results["recommendations"].append("Enable persistence for production environments")
    
    return validation_results

# Global configuration instance
_workflow_config: Optional[LangGraphConfig] = None

def get_workflow_config() -> LangGraphConfig:
    """
    Get the global workflow configuration instance
    """
    global _workflow_config
    if _workflow_config is None:
        _workflow_config = load_workflow_config()
    return _workflow_config

def reset_workflow_config():
    """
    Reset the global configuration (useful for testing)
    """
    global _workflow_config
    _workflow_config = None

# Environment setup for LangChain/LangGraph
def setup_langchain_environment(config: LangGraphConfig):
    """
    Setup environment variables for LangChain/LangGraph
    """
    if config.enable_tracing and config.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = config.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = config.langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = config.langsmith_endpoint
        logger.info("🎯 LangChain environment configured for tracing")
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.info("📊 LangChain tracing disabled")

# Configuration presets
DEVELOPMENT_CONFIG = LangGraphConfig(
    enable_tracing=True,
    default_mode=WorkflowMode.QUICK_CLASSIFICATION,
    enable_background_processing=False,
    max_retries=1,
    timeout_seconds=60,
    enable_parallel_processing=False,
    confidence_threshold=0.5,
    max_transactions_per_batch=10,
    log_level="DEBUG"
)

PRODUCTION_CONFIG = LangGraphConfig(
    enable_tracing=True,
    default_mode=WorkflowMode.FULL_PIPELINE,
    enable_background_processing=True,
    max_retries=3,
    timeout_seconds=300,
    enable_parallel_processing=True,
    confidence_threshold=0.7,
    max_transactions_per_batch=100,
    enable_persistence=True,
    enable_monitoring=True,
    log_level="INFO"
)

TESTING_CONFIG = LangGraphConfig(
    enable_tracing=False,
    default_mode=WorkflowMode.INGESTION_ONLY,
    enable_background_processing=False,
    max_retries=1,
    timeout_seconds=30,
    enable_parallel_processing=False,
    confidence_threshold=0.3,
    max_transactions_per_batch=5,
    enable_persistence=False,
    enable_monitoring=False,
    log_level="WARNING"
)

def get_config_preset(preset_name: str) -> LangGraphConfig:
    """
    Get a predefined configuration preset
    """
    presets = {
        "development": DEVELOPMENT_CONFIG,
        "production": PRODUCTION_CONFIG,
        "testing": TESTING_CONFIG
    }
    
    return presets.get(preset_name.lower(), load_workflow_config())
