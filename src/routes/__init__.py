"""
Main API Router - Combines all route modules
"""

from fastapi import APIRouter
from .transactions import router as transactions_router
from .analytics import router as analytics_router
from .suggestions import router as suggestions_router
from .auth import router as auth_router
from .agents import router as agents_router
from .workflow import router as workflow_router

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(auth_router)
api_router.include_router(transactions_router)
api_router.include_router(analytics_router)
api_router.include_router(suggestions_router)
api_router.include_router(agents_router)
api_router.include_router(workflow_router)

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """
    Health check endpoint for API status
    """
    return {
        "status": "healthy",
        "service": "Agentic Expense Tracker API",
        "version": "2.0.0",
        "components": {
            "authentication": "operational",
            "transactions": "operational", 
            "analytics": "operational",
            "suggestions": "operational",
            "agents": "operational",
            "workflows": "operational"
        }
    }

# API info endpoint
@api_router.get("/info")
async def api_info():
    """
    API information and available endpoints
    """
    return {
        "name": "Agentic Expense Tracker API",
        "version": "2.0.0",
        "description": "Multi-agent AI-powered expense tracking and financial analysis system with LangGraph workflows",
        "endpoints": {
            "authentication": "/api/auth/*",
            "transactions": "/api/transactions/*",
            "analytics": "/api/analytics/*", 
            "suggestions": "/api/suggestions/*",
            "agents": "/api/agents/*",
            "workflows": "/api/workflow/*"
        },
        "features": [
            "AI-powered transaction categorization",
            "Fraud detection and security monitoring",
            "Personalized financial suggestions",
            "Advanced analytics and reporting",
            "Multi-agent workflow orchestration with LangGraph",
            "Real-time WebSocket updates",
            "LangSmith tracing and monitoring",
            "Background processing capabilities",
            "Intelligent workflow routing"
        ]
    }
