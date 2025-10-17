"""
FastAPI routes for Unified LangGraph Transaction Workflow
Complete 7-agent integration with advanced processing modes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..workflows.unified_workflow import UnifiedTransactionWorkflow, get_workflow_instance
from ..workflows.config import WorkflowMode, get_workflow_config
from ..schemas.transaction_schemas import RawTransaction

logger = logging.getLogger(__name__)

# Initialize router
workflow_router = APIRouter(prefix="/workflow", tags=["workflow"])

class TransactionWorkflowRequest(BaseModel):
    """Request model for transaction workflow"""
    user_input: Optional[str] = None
    raw_transactions: Optional[List[Dict[str, Any]]] = None
    mode: str = "full_pipeline"
    user_id: str = "default"
    conversation_context: Optional[Dict[str, Any]] = None
    custom_config: Optional[Dict[str, Any]] = None

class TransactionWorkflowResponse(BaseModel):
    """Response model for transaction workflow"""
    workflow_id: str
    status: str
    mode: str
    execution_time: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    stages_completed: int = 0
    transactions_processed: int = 0
    confidence_scores: List[float] = []
    user_id: str

@workflow_router.post("/process", response_model=TransactionWorkflowResponse)
async def process_transaction_workflow(request: TransactionWorkflowRequest):
    """
    Process transactions through the unified LangGraph 7-agent workflow
    """
    try:
        logger.info(f"🚀 Starting unified workflow for mode: {request.mode}")

        # Get workflow instance
        workflow = get_workflow_instance()

        # Validate mode
        try:
            mode = WorkflowMode(request.mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode '{request.mode}'. Available: {[m.value for m in WorkflowMode]}"
            )

        # Execute unified workflow
        result = await workflow.execute_workflow(
            mode=mode,
            user_input=request.user_input,
            raw_transactions=request.raw_transactions,
            user_id=request.user_id,
            conversation_context=request.conversation_context,
            custom_config=request.custom_config
        )

        # Build response
        response = TransactionWorkflowResponse(
            workflow_id=result["workflow_id"],
            status=result["status"],
            mode=result["mode"],
            execution_time=result["execution_time"],
            result=result.get("result"),
            error=result.get("error"),
            stages_completed=result.get("stages_completed", 0),
            transactions_processed=result.get("transactions_processed", 0),
            confidence_scores=result.get("confidence_scores", []),
            user_id=result["user_id"]
        )

        logger.info(f"✅ Unified workflow completed: {response.workflow_id} in {response.execution_time:.2f}s")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unified workflow processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow processing failed: {str(e)}")

@workflow_router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """
    Get the current status of a workflow
    """
    try:
        workflow = get_workflow_instance()
        status = workflow.get_workflow_status(workflow_id)

        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@workflow_router.get("/background/{task_id}")
async def get_background_task_status(task_id: str):
    """
    Get the status of a background task
    """
    try:
        workflow = get_workflow_instance()
        status = workflow.get_background_task_status(task_id)

        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Background task {task_id} not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get background task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get background task status: {str(e)}")

@workflow_router.get("/visualize")
async def visualize_unified_workflow():
    """
    Get a visual representation of the unified 7-agent workflow
    """
    try:
        workflow = get_workflow_instance()
        config = get_workflow_config()

        return {
            "workflow_architecture": {
                "name": "Unified Transaction Processing Workflow",
                "version": "2.0",
                "agents": [
                    {
                        "name": "Workflow Initializer",
                        "step": "initialize_workflow_node",
                        "description": "Initialize workflow state and metadata",
                        "inputs": ["user_input", "raw_transactions", "user_context"],
                        "outputs": ["workflow_metadata", "initial_state"]
                    },
                    {
                        "name": "Natural Language Processor",
                        "step": "nl_processing_node",
                        "description": "Process natural language input with Groq LLM",
                        "inputs": ["user_input", "conversation_context"],
                        "outputs": ["extracted_transaction", "nl_confidence", "language_insights"]
                    },
                    {
                        "name": "Enhanced Ingestion Agent",
                        "step": "ingestion_node",
                        "description": "Data preprocessing, cleaning, and validation",
                        "inputs": ["extracted_transaction", "raw_transactions"],
                        "outputs": ["preprocessed_transactions", "ingestion_metadata", "data_quality_scores"]
                    },
                    {
                        "name": "NER Extraction Agent",
                        "step": "ner_extraction_node",
                        "description": "Named Entity Recognition for merchant and location extraction",
                        "inputs": ["preprocessed_transactions"],
                        "outputs": ["ner_entities", "merchant_info", "location_info"]
                    },
                    {
                        "name": "Classification Agent",
                        "step": "classification_node",
                        "description": "Advanced transaction category classification",
                        "inputs": ["preprocessed_transactions", "ner_entities"],
                        "outputs": ["predicted_category", "category_confidence", "classification_metadata"]
                    },
                    {
                        "name": "Validation Agent",
                        "step": "validation_node",
                        "description": "Transaction validation and quality assurance",
                        "inputs": ["classified_transactions"],
                        "outputs": ["validation_results", "is_valid", "validation_errors"]
                    },
                    {
                        "name": "Finalization Agent",
                        "step": "finalization_node",
                        "description": "Final processing and result compilation",
                        "inputs": ["validated_transactions"],
                        "outputs": ["final_transaction", "workflow_summary", "processing_metrics"]
                    }
                ],
                "routing_logic": {
                    "name": "Intelligent Router",
                    "description": "Conditional routing based on confidence and errors",
                    "conditions": [
                        "errors_detected -> skip to finalization",
                        "no_transactions -> skip to validation",
                        "low_confidence -> skip advanced processing",
                        "normal -> continue full pipeline"
                    ]
                }
            },
            "execution_modes": [
                {
                    "mode": "full_pipeline",
                    "description": "Complete 7-agent processing pipeline with routing",
                    "agents_used": 7,
                    "features": ["All agents", "Intelligent routing", "Complete analysis", "Full insights"],
                    "use_cases": ["Complete transaction analysis", "Full feature extraction", "Production processing"]
                },
                {
                    "mode": "quick_classification",
                    "description": "Fast classification without advanced processing",
                    "agents_used": 5,
                    "features": ["Core processing", "Fast execution", "Essential categorization"],
                    "use_cases": ["Quick categorization", "Real-time processing", "Mobile apps"]
                },
                {
                    "mode": "ingestion_only",
                    "description": "Data preprocessing and cleaning only",
                    "agents_used": 3,
                    "features": ["Data cleaning", "Preprocessing", "Validation", "Quality scoring"],
                    "use_cases": ["Data import", "Batch preprocessing", "Quality assessment"]
                },
                {
                    "mode": "validation_only",
                    "description": "Quick validation and quality checks",
                    "agents_used": 3,
                    "features": ["Fast validation", "Quality checks", "Error detection"],
                    "use_cases": ["Data validation", "Quality assurance", "Error checking"]
                },
                {
                    "mode": "background_processing",
                    "description": "Asynchronous complete processing",
                    "agents_used": 7,
                    "features": ["Background execution", "Non-blocking", "Notification support"],
                    "use_cases": ["Batch processing", "Large datasets", "Background analysis"]
                }
            ],
            "features": {
                "langgraph_integration": "✅ Complete StateGraph orchestration",
                "langsmith_tracing": f"✅ Enabled: {config.enable_tracing}",
                "conditional_routing": "✅ Intelligent agent flow with confidence-based routing",
                "error_handling": "✅ Comprehensive error management and recovery",
                "background_processing": f"✅ Async support: {config.enable_background_processing}",
                "multi_mode_execution": "✅ 5 different processing modes",
                "ai_powered": f"✅ Groq LLM integration: {bool(config.groq_api_key)}",
                "persistence": f"✅ Workflow checkpointing: {config.enable_persistence}",
                "monitoring": f"✅ Performance metrics: {config.enable_monitoring}",
                "parallel_processing": f"✅ Parallel agents: {config.enable_parallel_processing}"
            },
            "configuration": {
                "confidence_threshold": config.confidence_threshold,
                "timeout_seconds": config.timeout_seconds,
                "max_batch_size": config.max_transactions_per_batch,
                "default_mode": config.default_mode.value,
                "tracing_project": config.langsmith_project
            },
            "system_status": workflow.get_all_workflows_status()
        }

    except Exception as e:
        logger.error(f"Failed to visualize workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to visualize workflow: {str(e)}")

@workflow_router.post("/bulk-process")
async def bulk_process_transactions(
    transactions: List[TransactionWorkflowRequest],
    background_tasks: BackgroundTasks
):
    """
    Process multiple transactions in bulk through the unified workflow
    """
    try:
        workflow = get_workflow_instance()

        # Process all transactions
        results = []
        total_execution_time = 0

        for transaction in transactions:
            try:
                mode = WorkflowMode(transaction.mode)
            except ValueError:
                mode = WorkflowMode.FULL_PIPELINE

            result = await workflow.execute_workflow(
                mode=mode,
                user_input=transaction.user_input,
                raw_transactions=transaction.raw_transactions,
                user_id=transaction.user_id,
                conversation_context=transaction.conversation_context,
                custom_config=transaction.custom_config
            )
            results.append(result)
            total_execution_time += result["execution_time"]

        # Summary statistics
        total_processed = len(results)
        successful = sum(1 for r in results if r["status"] == "success")
        failed = total_processed - successful

        return {
            "total_processed": total_processed,
            "successful": successful,
            "failed": failed,
            "total_execution_time": total_execution_time,
            "average_execution_time": total_execution_time / total_processed if total_processed > 0 else 0,
            "results": [
                {
                    "workflow_id": r["workflow_id"],
                    "status": r["status"],
                    "mode": r["mode"],
                    "execution_time": r["execution_time"],
                    "stages_completed": r.get("stages_completed", 0),
                    "transactions_processed": r.get("transactions_processed", 0),
                    "user_id": r["user_id"],
                    "error": r.get("error")
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Bulk processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk processing failed: {str(e)}")

@workflow_router.post("/background-process")
async def start_background_workflow(request: TransactionWorkflowRequest):
    """
    Start workflow processing in background
    """
    try:
        workflow = get_workflow_instance()

        task_id = await workflow.execute_background_workflow(
            user_input=request.user_input,
            raw_transactions=request.raw_transactions,
            user_id=request.user_id
        )

        return {
            "status": "background_started",
            "task_id": task_id,
            "mode": "background_processing",
            "message": "Workflow started in background",
            "user_id": request.user_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Background workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Background workflow failed: {str(e)}")

# Monitoring and statistics endpoints
@workflow_router.get("/stats")
async def get_workflow_statistics():
    """
    Get comprehensive workflow statistics
    """
    try:
        workflow = get_workflow_instance()
        return {
            "system_stats": workflow.get_all_workflows_status(),
            "agent_performance": workflow.get_agent_performance_stats(),
            "metrics": workflow.export_workflow_metrics()
        }

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@workflow_router.post("/cleanup")
async def cleanup_old_workflows(hours: int = 24):
    """
    Clean up old completed workflows
    """
    try:
        workflow = get_workflow_instance()
        cleaned_count = workflow.cleanup_completed_workflows(older_than_hours=hours)

        return {
            "status": "success",
            "cleaned_workflows": cleaned_count,
            "older_than_hours": hours,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Health check for unified workflow
@workflow_router.get("/health")
async def unified_workflow_health_check():
    """
    Check if the unified workflow system is healthy
    """
    try:
        workflow = get_workflow_instance()
        config = get_workflow_config()

        # Test with simple input
        test_result = await workflow.execute_workflow(
            mode=WorkflowMode.QUICK_CLASSIFICATION,
            user_input="Test transaction $1.00",
            user_id="health_check"
        )

        return {
            "status": "healthy",
            "workflow_initialized": True,
            "agents_available": 7,
            "modes_available": len([mode.value for mode in WorkflowMode]),
            "langgraph_integrated": True,
            "langsmith_tracing": config.enable_tracing,
            "test_workflow_successful": test_result["status"] == "success",
            "test_execution_time": test_result["execution_time"],
            "available_modes": [mode.value for mode in WorkflowMode],
            "configuration": {
                "confidence_threshold": config.confidence_threshold,
                "timeout_seconds": config.timeout_seconds,
                "max_batch_size": config.max_transactions_per_batch,
                "persistence_enabled": config.enable_persistence,
                "monitoring_enabled": config.enable_monitoring
            },
            "timestamp": datetime.now().isoformat(),
            "features": {
                "unified_workflow": "✅ Complete 7-Agent Pipeline",
                "intelligent_routing": "✅ Confidence-Based Flow Control",
                "multi_mode_processing": "✅ 5 Execution Modes",
                "langgraph_orchestration": "✅ StateGraph Implementation",
                "langsmith_tracing": f"✅ {'Enabled' if config.enable_tracing else 'Disabled'}",
                "background_processing": f"✅ {'Enabled' if config.enable_background_processing else 'Disabled'}",
                "error_handling": "✅ Comprehensive Recovery",
                "performance_monitoring": f"✅ {'Enabled' if config.enable_monitoring else 'Disabled'}",
                "workflow_persistence": f"✅ {'Enabled' if config.enable_persistence else 'Disabled'}",
                "parallel_processing": f"✅ {'Enabled' if config.enable_parallel_processing else 'Disabled'}"
            }
        }

    except Exception as e:
        logger.error(f"Unified workflow health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "workflow_initialized": False,
            "timestamp": datetime.now().isoformat()
        }

# Export the router
router = workflow_router
