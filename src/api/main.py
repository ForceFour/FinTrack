"""FastAPI application for FinTrack transaction processing"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from datetime import datetime
import uvicorn
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.workflows.unified_workflow import UnifiedTransactionWorkflow, WorkflowMode, get_workflow_instance
from src.schemas.transaction_schemas import RawTransaction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FinTrack API",
    description="Financial Transaction Analysis and Processing System with LangGraph",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("🚀 Starting FinTrack API...")
    try:
        # Initialize database (simplified for now)
        logger.info("✅ FinTrack API startup complete")
    except Exception as e:
        logger.error(f"❌ Failed to start FinTrack API: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down FinTrack API...")
    logger.info("✅ FinTrack API shutdown complete")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "FinTrack API - Financial Transaction Analysis System"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fintrack-api"}

@app.get("/api/health/full")
async def full_health_check():
    """Full system health check"""
    try:
        # Check workflow system
        try:
            workflow = get_workflow_instance()
            workflow_health = {"status": "healthy", "workflow": "operational"}
        except Exception as e:
            workflow_health = {"status": "unhealthy", "error": str(e)}

        return {
            "status": "healthy" if workflow_health["status"] == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "workflow": workflow_health
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.post("/api/v1/transactions/process")
async def process_transaction(
    transaction: RawTransaction,
    mode: str = "full_pipeline",
    user_id: str = "api_user"
):
    """Process a single transaction through the workflow"""
    try:
        workflow = get_workflow_instance()

        # Convert mode string to WorkflowMode enum
        try:
            workflow_mode = WorkflowMode(mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workflow mode: {mode}. Valid modes: {[m.value for m in WorkflowMode]}"
            )

        # Execute workflow
        result = await workflow.execute_workflow(
            mode=workflow_mode,
            user_input=transaction.description,
            user_id=user_id,
            amount=transaction.amount,
            date=transaction.date,
            merchant=transaction.merchant
        )

        return {
            "status": "success",
            "message": "Transaction processed successfully",
            "workflow_id": result.get("workflow_id"),
            "execution_time": result.get("execution_time"),
            "result": result.get("result", {})
        }

    except Exception as e:
        logger.error(f"Transaction processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Transaction processing failed: {str(e)}")

@app.get("/api/v1/workflow/modes")
async def get_workflow_modes():
    """Get available workflow modes"""
    try:
        modes = [{"value": mode.value, "name": mode.value.replace("_", " ").title()} for mode in WorkflowMode]
        return {
            "status": "success",
            "modes": modes,
            "default_mode": "full_pipeline"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow modes: {str(e)}")

@app.get("/api/v1/workflow/status")
async def get_workflow_status():
    """Get workflow system status and statistics"""
    try:
        workflow = get_workflow_instance()
        stats = workflow.get_all_workflows_status()

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_statistics": stats
        }
    except Exception as e:
        logger.error(f"Workflow status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@app.get("/api/v1/agents/performance")
async def get_agent_performance():
    """Get agent performance statistics"""
    try:
        workflow = get_workflow_instance()
        performance_stats = workflow.get_agent_performance_stats()

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "agent_performance": performance_stats
        }
    except Exception as e:
        logger.error(f"Agent performance error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent performance: {str(e)}")

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
