"""Configuration settings for FinTrack application"""

import os
from typing import Dict, Any, List
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # API Settings
    api_title: str = "FinTrack API"
    api_version: str = "0.1.0"
    api_description: str = "Financial Transaction Analysis and Processing System"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # OpenAI Settings
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = "gpt-3.5-turbo"
    
    # Groq Settings
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    
    # LangGraph Settings
    langgraph_api_key: str = Field(default="", env="LANGGRAPH_API_KEY")
    
    # LangChain/LangSmith Settings
    langchain_tracing_v2: str = Field(default="false", env="LANGCHAIN_TRACING_V2")
    langchain_endpoint: str = Field(default="https://api.smith.langchain.com", env="LANGCHAIN_ENDPOINT")
    langchain_api_key: str = Field(default="", env="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="fintrack-workflows", env="LANGCHAIN_PROJECT")
    langsmith_api_key: str = Field(default="", env="LANGSMITH_API_KEY")
    
    # Security Settings
    secret_key: str = Field(default="your_secret_key_here", env="SECRET_KEY")
    
    # Database Settings (for future use)
    database_url: str = Field(default="sqlite:///./fintrack.db", env="DATABASE_URL")
    
    # Model Settings
    model_path: str = "models/"
    category_model_path: str = "models/category_classifier.joblib"
    anomaly_model_path: str = "models/anomaly_detector.joblib"
    
    # Feature Engineering Settings
    max_tfidf_features: int = 100
    merchant_frequency_threshold: int = 2
    
    # Processing Settings
    batch_size: int = 100
    max_transactions_per_request: int = 1000
    
    # Security Settings
    allowed_origins: List[str] = ["*"]
    
    # Logging Settings
    log_level: str = "INFO"
    log_file: str = "logs/fintrack.log"
    
    # Agent Configuration
    agent_configs: Dict[str, Any] = {
        "ingestion_agent": {
            "timeout": 30,
            "retry_attempts": 3
        },
        "ner_merchant_agent": {
            "confidence_threshold": 0.8,
            "unknown_merchant_label": "Unknown Merchant"
        },
        "classifier_agent": {
            "confidence_threshold": 0.7,
            "default_category": "miscellaneous"
        },
        "pattern_analyzer_agent": {
            "lookback_days": 90,
            "min_transactions_for_pattern": 3
        },
        "suggestion_agent": {
            "max_suggestions": 10,
            "priority_threshold": 0.8
        },
        "safety_guard_agent": {
            "anomaly_threshold": 0.9,
            "alert_severity_threshold": "medium"
        }
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get configuration for a specific agent"""
    return settings.agent_configs.get(agent_name, {})
