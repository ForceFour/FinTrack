"""
LangGraph Server for Studio Visualization
This creates a local server that LangGraph Studio can connect to
"""
import os
import sys
from pathlib import Path
import uuid

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from typing import Dict, Any, List, TypedDict
from datetime import datetime

# Import our detailed workflow
class DetailedIngestionState(TypedDict):
    """State for detailed ingestion workflow"""
    input_text: str
    groq_extraction: Dict[str, Any]
    confidence_score: float
    extracted_amount: str
    extracted_merchant: str
    extracted_date: str
    preprocessed_transactions: List[Dict[str, Any]]
    validation_results: Dict[str, Any]
    final_output: Dict[str, Any]
    metadata: Dict[str, Any]

def receive_input(state: DetailedIngestionState) -> DetailedIngestionState:
    """Step 1: Receive and prepare natural language input"""
    print(f"🎯 RECEIVING: Processing natural language input")
    state["metadata"] = {
        "step": "input_received",
        "timestamp": datetime.now().isoformat(),
        "input_length": len(state["input_text"])
    }
    return state

def groq_extraction(state: DetailedIngestionState) -> DetailedIngestionState:
    """Step 2: Use Groq LLM to extract transaction data"""
    print(f"🤖 GROQ LLM: Extracting transaction details with Groq")
    
    # Simulate what the Groq LLM extraction does
    state["groq_extraction"] = {
        "raw_response": "Amount: $4.50, Merchant: Starbucks, Time: this morning",
        "extraction_method": "LLM",
        "model_used": "groq-llama"
    }
    state["metadata"]["groq_processing"] = True
    
    return state

def confidence_evaluation(state: DetailedIngestionState) -> DetailedIngestionState:
    """Step 3: Evaluate extraction confidence"""
    print(f"📊 CONFIDENCE: Evaluating extraction confidence")
    
    # Simulate confidence calculation
    state["confidence_score"] = 0.90
    state["metadata"]["confidence_threshold"] = 0.70
    state["metadata"]["confidence_met"] = True
    
    return state

def amount_processing(state: DetailedIngestionState) -> DetailedIngestionState:
    """Step 4: Process and normalize amount"""
    print(f"💰 AMOUNT: Processing transaction amount")
    
    state["extracted_amount"] = "$4.50"
    state["metadata"]["amount_normalized"] = 4.50
    state["metadata"]["currency"] = "USD"
    
    return state

def merchant_extraction(state: DetailedIngestionState) -> DetailedIngestionState:
    """Step 5: Extract and standardize merchant name"""
    print(f"🏪 MERCHANT: Extracting merchant information")
    
    state["extracted_merchant"] = "Starbucks"
    state["metadata"]["merchant_standardized"] = "Starbucks Corporation"
    state["metadata"]["merchant_category"] = "Coffee Shop"
    
    return state

def date_normalization(state: DetailedIngestionState) -> DetailedIngestionState:
    """Step 6: Normalize date information"""
    print(f"📅 DATE: Normalizing date and time")
    
    state["extracted_date"] = datetime.now().strftime("%Y-%m-%d")
    state["metadata"]["date_source"] = "inferred_today"
    state["metadata"]["time_reference"] = "this morning"
    
    return state

def data_preprocessing(state: DetailedIngestionState) -> DetailedIngestionState:
    """Step 7: Apply data preprocessing pipeline"""
    print(f"⚙️ PREPROCESSING: Applying data preprocessing pipeline")
    
    # Simulate preprocessing
    preprocessed_txn = {
        "id": f"txn_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "amount": 4.50,
        "merchant": "Starbucks",
        "date": state["extracted_date"],
        "category": "food_dining",
        "description_cleaned": "Coffee purchase at Starbucks"
    }
    
    state["preprocessed_transactions"] = [preprocessed_txn]
    state["metadata"]["preprocessing_complete"] = True
    
    return state

def validation_output(state: DetailedIngestionState) -> DetailedIngestionState:
    """Step 8: Validate and prepare final output"""
    print(f"✅ VALIDATION: Validating and finalizing output")
    
    state["validation_results"] = {
        "amount_valid": True,
        "merchant_valid": True,
        "date_valid": True,
        "overall_valid": True
    }
    
    state["final_output"] = {
        "transactions_processed": len(state["preprocessed_transactions"]),
        "confidence": state["confidence_score"],
        "status": "completed"
    }
    
    return state

# Build the workflow
def create_ingestion_workflow():
    """Create the ingestion workflow for Studio"""
    workflow = StateGraph(DetailedIngestionState)
    
    # Add nodes
    workflow.add_node("🎯 Receive NL Input", receive_input)
    workflow.add_node("🤖 Groq LLM Extraction", groq_extraction)
    workflow.add_node("📊 Confidence Evaluation", confidence_evaluation)
    workflow.add_node("💰 Amount Processing", amount_processing)
    workflow.add_node("🏪 Merchant Extraction", merchant_extraction)
    workflow.add_node("📅 Date Normalization", date_normalization)
    workflow.add_node("⚙️ Data Preprocessing", data_preprocessing)
    workflow.add_node("✅ Validation & Output", validation_output)
    
    # Define edges
    workflow.add_edge("🎯 Receive NL Input", "🤖 Groq LLM Extraction")
    workflow.add_edge("🤖 Groq LLM Extraction", "📊 Confidence Evaluation")
    workflow.add_edge("📊 Confidence Evaluation", "💰 Amount Processing")
    workflow.add_edge("💰 Amount Processing", "🏪 Merchant Extraction")
    workflow.add_edge("🏪 Merchant Extraction", "📅 Date Normalization")
    workflow.add_edge("📅 Date Normalization", "⚙️ Data Preprocessing")
    workflow.add_edge("⚙️ Data Preprocessing", "✅ Validation & Output")
    workflow.add_edge("✅ Validation & Output", END)
    
    # Set entry point
    workflow.set_entry_point("🎯 Receive NL Input")
    
    return workflow

# Create the compiled app without custom checkpointer for LangGraph Studio
workflow = create_ingestion_workflow()
# Remove the custom checkpointer - LangGraph API handles persistence automatically
app = workflow.compile()

if __name__ == "__main__":
    print("🚀 LangGraph Server for Studio Visualization")
    print("=" * 50)
    print("📊 Workflow created with 8 nodes:")
    print("   1. 🎯 Receive NL Input")
    print("   2. 🤖 Groq LLM Extraction") 
    print("   3. 📊 Confidence Evaluation")
    print("   4. 💰 Amount Processing")
    print("   5. 🏪 Merchant Extraction")
    print("   6. 📅 Date Normalization")
    print("   7. ⚙️ Data Preprocessing")
    print("   8. ✅ Validation & Output")
    print("\n✅ Ready for LangGraph Studio!")
    print("🌐 Use this file with LangGraph Studio to visualize the workflow")
