"""
LangGraph Exports for API Server
Simple, direct exports of compiled workflows for LangGraph API
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

# Set up logging
logger = logging.getLogger(__name__)

# Import required components
try:
    from ..states import TransactionProcessingState, ProcessingStage
    from ..nodes import TransactionProcessingNodes
    logger.info("✅ Successfully imported states and nodes")
except Exception as e:
    logger.error(f"❌ Failed to import required components: {e}")
    # Create minimal fallback types
    from typing import TypedDict
    from enum import Enum

    class ProcessingStage(Enum):
        INITIAL = "initial"
        COMPLETED = "completed"
        ERROR = "error"

    class TransactionProcessingState(TypedDict):
        workflow_id: str
        user_input: str
        current_stage: str
        output: Dict[str, Any]

def create_simple_workflow() -> StateGraph:
    """Create a simple workflow for testing/fallback"""
    logger.info("Creating simple fallback workflow")

    def simple_node(state: TransactionProcessingState) -> TransactionProcessingState:
        """Simple processing node"""
        state["output"] = {
            "status": "processed",
            "message": "Simple workflow executed successfully",
            "workflow_id": state.get("workflow_id", "simple")
        }
        return state

    workflow = StateGraph(TransactionProcessingState)
    workflow.add_node("simple_process", simple_node)
    workflow.set_entry_point("simple_process")
    workflow.add_edge("simple_process", END)

    return workflow

def create_full_pipeline_workflow() -> StateGraph:
    """Create the full pipeline workflow"""
    try:
        logger.info("Creating full pipeline workflow")

        # Initialize nodes with minimal config
        nodes = TransactionProcessingNodes(config={})

        workflow = StateGraph(TransactionProcessingState)

        # Add nodes
        workflow.add_node("initialize", nodes.initialize_workflow_node)
        workflow.add_node("nl_processing", nodes.nl_processing_node)
        workflow.add_node("ingestion", nodes.ingestion_node)
        workflow.add_node("ner_extraction", nodes.ner_extraction_node)
        workflow.add_node("classification", nodes.classification_node)
        workflow.add_node("validation", nodes.validation_node)
        workflow.add_node("finalization", nodes.finalization_node)

        # Define flow
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "nl_processing")
        workflow.add_edge("nl_processing", "ingestion")
        workflow.add_edge("ingestion", "ner_extraction")
        workflow.add_edge("ner_extraction", "classification")
        workflow.add_edge("classification", "validation")
        workflow.add_edge("validation", "finalization")
        workflow.add_edge("finalization", END)

        logger.info("✅ Full pipeline workflow created successfully")
        return workflow

    except Exception as e:
        logger.error(f"❌ Failed to create full pipeline workflow: {e}")
        return create_simple_workflow()

def create_quick_classification_workflow() -> StateGraph:
    """Create quick classification workflow"""
    try:
        logger.info("Creating quick classification workflow")

        nodes = TransactionProcessingNodes(config={})

        workflow = StateGraph(TransactionProcessingState)

        # Add essential nodes only
        workflow.add_node("initialize", nodes.initialize_workflow_node)
        workflow.add_node("nl_processing", nodes.nl_processing_node)
        workflow.add_node("ingestion", nodes.ingestion_node)
        workflow.add_node("classification", nodes.classification_node)
        workflow.add_node("finalization", nodes.finalization_node)

        # Quick flow
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "nl_processing")
        workflow.add_edge("nl_processing", "ingestion")
        workflow.add_edge("ingestion", "classification")
        workflow.add_edge("classification", "finalization")
        workflow.add_edge("finalization", END)

        logger.info("✅ Quick classification workflow created successfully")
        return workflow

    except Exception as e:
        logger.error(f"❌ Failed to create quick classification workflow: {e}")
        return create_simple_workflow()

def create_ingestion_only_workflow() -> StateGraph:
    """Create ingestion-only workflow"""
    try:
        logger.info("Creating ingestion-only workflow")

        nodes = TransactionProcessingNodes(config={})

        workflow = StateGraph(TransactionProcessingState)

        # Add ingestion nodes only
        workflow.add_node("initialize", nodes.initialize_workflow_node)
        workflow.add_node("nl_processing", nodes.nl_processing_node)
        workflow.add_node("ingestion", nodes.ingestion_node)
        workflow.add_node("finalization", nodes.finalization_node)

        # Ingestion flow
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "nl_processing")
        workflow.add_edge("nl_processing", "ingestion")
        workflow.add_edge("ingestion", "finalization")
        workflow.add_edge("finalization", END)

        logger.info("✅ Ingestion-only workflow created successfully")
        return workflow

    except Exception as e:
        logger.error(f"❌ Failed to create ingestion-only workflow: {e}")
        return create_simple_workflow()

def create_background_processing_workflow() -> StateGraph:
    """Create background processing workflow"""
    try:
        logger.info("Creating background processing workflow")

        nodes = TransactionProcessingNodes(config={})

        def background_init(state: TransactionProcessingState) -> TransactionProcessingState:
            """Background initialization"""
            state["background_processing"] = True
            return nodes.initialize_workflow_node(state)

        workflow = StateGraph(TransactionProcessingState)

        # Add background nodes
        workflow.add_node("background_init", background_init)
        workflow.add_node("nl_processing", nodes.nl_processing_node)
        workflow.add_node("ingestion", nodes.ingestion_node)
        workflow.add_node("classification", nodes.classification_node)
        workflow.add_node("finalization", nodes.finalization_node)

        # Background flow
        workflow.set_entry_point("background_init")
        workflow.add_edge("background_init", "nl_processing")
        workflow.add_edge("nl_processing", "ingestion")
        workflow.add_edge("ingestion", "classification")
        workflow.add_edge("classification", "finalization")
        workflow.add_edge("finalization", END)

        logger.info("✅ Background processing workflow created successfully")
        return workflow

    except Exception as e:
        logger.error(f"❌ Failed to create background processing workflow: {e}")
        return create_simple_workflow()

# Create and compile workflows
try:
    logger.info("🚀 Creating and compiling workflows for LangGraph API...")

    # Create workflow graphs
    _full_pipeline_graph = create_full_pipeline_workflow()
    _quick_classification_graph = create_quick_classification_workflow()
    _ingestion_only_graph = create_ingestion_only_workflow()
    _background_processing_graph = create_background_processing_workflow()

    # Compile workflows (without checkpointer for API compatibility)
    full_pipeline = _full_pipeline_graph.compile()
    quick_classification = _quick_classification_graph.compile()
    ingestion_only = _ingestion_only_graph.compile()
    background_processing = _background_processing_graph.compile()

    logger.info("✅ All workflows compiled successfully for LangGraph API")

except Exception as e:
    logger.error(f"❌ Failed to compile workflows: {e}")

    # Create minimal fallback workflows
    simple_graph = create_simple_workflow()
    full_pipeline = simple_graph.compile()
    quick_classification = simple_graph.compile()
    ingestion_only = simple_graph.compile()
    background_processing = simple_graph.compile()

    logger.warning("⚠️ Using fallback simple workflows due to compilation errors")

# Export compiled workflows
__all__ = [
    'full_pipeline',
    'quick_classification',
    'ingestion_only',
    'background_processing'
]

logger.info(f"📦 Exported {len(__all__)} compiled workflows for LangGraph API")
