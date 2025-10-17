"""
Agentic Expense Tracker - Multi-Agent AI Financial Analysis System
Main FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime

# Import route modules
from src.routes import api_router
from src.core.database_config import init_database, close_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting Agentic Expense Tracker API...")
    logger.info("Initializing multi-agent system...")

    # Initialize database connections, agents, etc.
    try:
        await init_database()
        # TODO: Start agent orchestrator
        # TODO: Initialize ML models
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"❌ Application startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Agentic Expense Tracker API...")
    try:
        await close_database()
        # TODO: Stop agent orchestrator
        # TODO: Save state if needed
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"❌ Application shutdown failed: {e}")

# Create FastAPI application
app = FastAPI(
    title="Agentic Expense Tracker API",
    description="Multi-agent AI-powered expense tracking and financial analysis system with LangChain/LangGraph integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",  # Streamlit default port
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:8501",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Include analytics API directly for frontend integration (without v1 prefix)
from src.api.analytics import router as frontend_analytics_router
app.include_router(frontend_analytics_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Welcome to Agentic Expense Tracker API",
        "version": "1.0.0",
        "description": "Multi-agent AI-powered expense tracking system",
        "documentation": "/docs",
        "health_check": "/api/v1/health",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "ai_categorization": "✅ Enabled",
            "fraud_detection": "✅ Enabled",
            "personalized_suggestions": "✅ Enabled",
            "advanced_analytics": "✅ Enabled",
            "multi_agent_workflows": "✅ Enabled",
            "real_time_updates": "✅ Enabled"
        }
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat(),
        "path": str(request.url)
    }

# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """
    Custom 404 handler
    """
    return {
        "error": "Not found",
        "message": f"The requested endpoint {request.url.path} was not found",
        "available_endpoints": [
            "/api/v1/auth/*",
            "/api/v1/transactions/*",
            "/api/v1/analytics/*",
            "/api/v1/suggestions/*",
            "/api/v1/agents/*"
        ],
        "documentation": "/docs"
    }

def main():
    """
    Main application entry point
    """
    print("🚀 Starting Agentic Expense Tracker...")
    print("📊 Multi-Agent AI Financial Analysis System")
    print("🔗 Powered by LangChain & LangGraph")
    print("=" * 50)

    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
