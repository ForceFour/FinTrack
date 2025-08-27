"""
FastAPI routes for LangGraph Transaction Workflow
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from ..workflows.transaction_workflow import TransactionProcessingWorkflow
from ..states import ProcessingStage

logger = logging.getLogger(__name__)

# Initialize router
workflow_router = APIRouter(prefix="/api/workflow", tags=["workflow"])

# Initialize workflow (singleton pattern)
workflow_instance = None

def get_workflow_instance() -> TransactionProcessingWorkflow:
    """Get or create workflow instance"""
    global workflow_instance
    if workflow_instance is None:
        workflow_instance = TransactionProcessingWorkflow()
    return workflow_instance

class TransactionWorkflowRequest(BaseModel):
    """Request model for transaction workflow"""
    raw_input: str
    input_type: str = "unstructured"
    workflow_id: Optional[str] = None

class TransactionWorkflowResponse(BaseModel):
    """Response model for transaction workflow"""
    workflow_id: str
    status: str
    confidence_score: float
    extraction_method: str
    is_valid: bool
    processing_time: float
    final_transaction: Optional[Dict[str, Any]] = None
    processing_stages: int
    errors: list = []

@workflow_router.post("/process", response_model=TransactionWorkflowResponse)
async def process_transaction_workflow(request: TransactionWorkflowRequest):
    """
    Process a transaction through the complete LangGraph workflow
    """
    try:
        logger.info(f"🚀 Starting workflow for input: {request.raw_input[:50]}...")
        
        # Get workflow instance
        workflow = get_workflow_instance()
        
        # Process transaction
        result = workflow.process_transaction_sync(
            raw_input=request.raw_input,
            input_type=request.input_type
        )
        
        # Build response
        response = TransactionWorkflowResponse(
            workflow_id=result.get('workflow_id', 'unknown'),
            status=result.get('current_stage', ProcessingStage.ERROR).value if hasattr(result.get('current_stage'), 'value') else str(result.get('current_stage', 'error')),
            confidence_score=result.get('confidence_score', 0.0),
            extraction_method=result.get('extraction_method', 'unknown'),
            is_valid=result.get('is_valid', False),
            processing_time=result.get('total_processing_time', 0.0),
            final_transaction=result.get('final_transaction'),
            processing_stages=len(result.get('processing_history', [])),
            errors=[error.get('error', str(error)) for error in result.get('errors', [])]
        )
        
        logger.info(f"✅ Workflow completed: {response.workflow_id} with confidence {response.confidence_score:.2f}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Workflow processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow processing failed: {str(e)}")

@workflow_router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """
    Get the current status of a workflow
    """
    try:
        workflow = get_workflow_instance()
        status = workflow.get_workflow_status(workflow_id)
        
        if 'error' in status:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {status['error']}")
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@workflow_router.get("/visualize")
async def visualize_workflow():
    """
    Get a visual representation of the workflow
    """
    try:
        workflow = get_workflow_instance()
        diagram = workflow.visualize_workflow()
        
        return {
            "diagram": diagram,
            "nodes": [
                "initialize", "nl_processing", "ingestion", 
                "ner_extraction", "classification", "validation", 
                "finalization", "metrics"
            ],
            "features": [
                "LangChain/Groq NL Processing",
                "Enhanced Ingestion with Preprocessing",
                "NER Entity Extraction",
                "ML Classification",
                "Validation & Error Handling",
                "Human Review Capability",
                "Comprehensive Metrics"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to visualize workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to visualize workflow: {str(e)}")

@workflow_router.post("/bulk-process")
async def bulk_process_transactions(
    transactions: list[TransactionWorkflowRequest],
    background_tasks: BackgroundTasks
):
    """
    Process multiple transactions in bulk
    """
    try:
        workflow = get_workflow_instance()
        
        # Process all transactions
        results = []
        for transaction in transactions:
            result = workflow.process_transaction_sync(
                raw_input=transaction.raw_input,
                input_type=transaction.input_type
            )
            results.append(result)
        
        # Summary statistics
        total_processed = len(results)
        successful = sum(1 for r in results if r.get('is_valid', False))
        avg_confidence = sum(r.get('confidence_score', 0) for r in results) / total_processed if total_processed > 0 else 0
        
        return {
            "total_processed": total_processed,
            "successful": successful,
            "failed": total_processed - successful,
            "average_confidence": avg_confidence,
            "results": [
                {
                    "workflow_id": r.get('workflow_id'),
                    "confidence": r.get('confidence_score', 0),
                    "is_valid": r.get('is_valid', False),
                    "final_transaction": r.get('final_transaction')
                }
                for r in results
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Bulk processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk processing failed: {str(e)}")

# Health check for workflow
@workflow_router.get("/health")
async def workflow_health_check():
    """
    Check if the workflow system is healthy
    """
    try:
        workflow = get_workflow_instance()
        
        # Test with simple input
        test_result = workflow.process_transaction_sync(
            raw_input="Test transaction $1.00",
            input_type="unstructured"
        )
        
        return {
            "status": "healthy",
            "workflow_initialized": True,
            "langchain_available": test_result.get('extraction_method') == 'llm',
            "test_confidence": test_result.get('confidence_score', 0),
            "nodes_available": 8,  # Number of workflow nodes
            "timestamp": test_result.get('started_at')
        }
        
    except Exception as e:
        logger.error(f"❌ Workflow health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "workflow_initialized": False
        }


# Export the router with the expected name
router = workflow_router
