"""
LangGraph Server for Studio Visualization
This creates a local server that LangGraph Studio can connect to
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
from datetime import datetime

# Import our actual workflow components
try:
    from src.states import TransactionProcessingState, ProcessingStage
    from src.nodes import TransactionProcessingNodes
    print("Successfully imported actual workflow components")
except ImportError as e:
    print(f"Warning: Could not import workflow components: {e}")
    # Fallback to basic TypedDict
    from typing import TypedDict

    class TransactionProcessingState(TypedDict):
        workflow_id: str
        user_input: str
        current_stage: str
        extracted_transaction: Dict[str, Any]
        final_transaction: Dict[str, Any]
        processing_history: List[Dict[str, Any]]

# Initialize the transaction processing nodes
def create_transaction_workflow():
    """Create the actual transaction processing workflow"""
    try:
        # Try to use the actual nodes
        nodes = TransactionProcessingNodes()

        workflow = StateGraph(TransactionProcessingState)

        # Add actual workflow nodes
        workflow.add_node("Initialize", nodes.initialize_workflow_node)
        workflow.add_node("NL Processing", nodes.nl_processing_node)
        workflow.add_node("Ingestion", nodes.ingestion_node)
        workflow.add_node("NER Extraction", nodes.ner_extraction_node)
        workflow.add_node("Classification", nodes.classification_node)
        workflow.add_node("Validation", nodes.validation_node)
        workflow.add_node("Finalization", nodes.finalization_node)

        # Define the workflow flow
        workflow.set_entry_point("Initialize")
        workflow.add_edge("Initialize", "NL Processing")
        workflow.add_edge("NL Processing", "Ingestion")
        workflow.add_edge("Ingestion", "NER Extraction")
        workflow.add_edge("NER Extraction", "Classification")
        workflow.add_edge("Classification", "Validation")
        workflow.add_edge("Validation", "Finalization")
        workflow.add_edge("Finalization", END)

        print("Successfully created actual transaction processing workflow")
        return workflow

    except Exception as e:
        print(f"Failed to create actual workflow, using fallback: {e}")
        return create_fallback_workflow()

def create_fallback_workflow():
    """Create a simple fallback workflow"""
    def simple_process(state: TransactionProcessingState) -> TransactionProcessingState:
        """Simple processing for fallback"""
        user_input = state.get("user_input", "")

        # Basic processing
        state["extracted_transaction"] = {
            "description": user_input,
            "amount": None,
            "merchant": None,
            "category": "unknown"
        }

        state["final_transaction"] = state["extracted_transaction"]
        state["processing_history"] = [{
            "stage": "simple_processing",
            "timestamp": datetime.now().isoformat(),
            "input": user_input
        }]

        print(f"FALLBACK: Processed input: {user_input}")
        return state

    workflow = StateGraph(TransactionProcessingState)
    workflow.add_node("Simple Process", simple_process)
    workflow.set_entry_point("Simple Process")
    workflow.add_edge("Simple Process", END)

    return workflow

# Create the compiled app for LangGraph Studio
workflow = create_transaction_workflow()
app = workflow.compile()

if __name__ == "__main__":
    print("LangGraph Server for Studio Visualization")
    print("=" * 50)
    print("Transaction Processing Workflow created with 7 nodes:")
    print("   1. Initialize")
    print("   2. NL Processing")
    print("   3. Ingestion")
    print("   4. NER Extraction")
    print("   5. Classification")
    print("   6. Validation")
    print("   7. Finalization")
    print("\nReady for LangGraph Studio!")
    print("Use this file with LangGraph Studio to visualize the workflow")
