"""
LangGraph Studio Server for FinTrack - Complete 7-Agent Pipeline
Includes the new Suggestion Agent for full workflow visualization
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

# Import the complete unified workflow
try:
    from src.workflows.unified_workflow import UnifiedTransactionWorkflow, WorkflowMode
    from src.states import TransactionProcessingState
    print("✅ Successfully imported unified workflow with Suggestion Agent")
except ImportError as e:
    print(f"❌ Failed to import unified workflow: {e}")
    sys.exit(1)

def create_studio_workflow():
    """Create the complete workflow for LangGraph Studio visualization"""
    try:
        # Initialize the unified workflow
        workflow_manager = UnifiedTransactionWorkflow()

        # Get the full pipeline workflow (includes Suggestion Agent)
        workflow = workflow_manager._build_full_pipeline()

        print("✅ Created complete 10-node workflow with Suggestion Agent")
        print("   Nodes: Initialize → NL Processing → Ingestion → NER → Classification →")
        print("          Pattern Analysis → Suggestion → Safety Guard → Validation → Finalization")

        return workflow

    except Exception as e:
        print(f"❌ Failed to create workflow: {e}")
        raise

# Create the compiled app for LangGraph Studio
try:
    workflow = create_studio_workflow()
    app = workflow.compile()
    print("🎉 Workflow compiled successfully for LangGraph Studio!")
except Exception as e:
    print(f"❌ Failed to compile workflow: {e}")
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 LangGraph Studio Server for FinTrack")
    print("=" * 50)
    print("🎯 Complete 7-Agent Pipeline with Suggestion Agent")
    print("📊 10 Workflow Nodes:")
    print("   1. 🔧 Initialize")
    print("   2. 🧠 NL Processing")
    print("   3. 🚀 Ingestion")
    print("   4. 🏷️ NER Extraction")
    print("   5. 📊 Classification")
    print("   6. 📈 Pattern Analysis")
    print("   7. 💡 Suggestion ← NEW!")
    print("   8. 🛡️ Safety Guard")
    print("   9. ✅ Validation")
    print("   10. 🎯 Finalization")
    print()
    print("🌐 Ready for LangGraph Studio!")
    print("   1. Open LangGraph Studio")
    print("   2. Connect to this server")
    print("   3. Run workflow to see Suggestion Agent in action")
    print("   4. Check LangSmith for detailed traces")
    print()
    print("💡 Test Input: 'I spent $50 at Starbucks'")
    print("=" * 50)
