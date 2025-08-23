"""FastAPI application for FinTrack transaction processing"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import uvicorn

from ..workflows.transaction_workflow import TransactionWorkflow
from ..schemas.transaction_schemas import RawTransaction


# Initialize FastAPI app
app = FastAPI(
    title="FinTrack API",
    description="Financial Transaction Analysis and Processing System",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize workflow
workflow = TransactionWorkflow()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "FinTrack API - Financial Transaction Analysis System"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fintrack-api"}


@app.post("/transactions/process")
async def process_transactions(transactions: List[RawTransaction]):
    """
    Process raw transactions through the complete 6-agent pipeline
    
    Args:
        transactions: List of raw transaction data
        
    Returns:
        Complete processing results including classifications, insights, and suggestions
    """
    try:
        result = await workflow.process_transactions(transactions)
        return {
            "status": "success",
            "data": result,
            "transactions_processed": len(transactions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/transactions/ingest")
async def ingest_transactions(transactions: List[RawTransaction]):
    """
    Process transactions only through Ingestion Agent (Agent 1)
    """
    try:
        ingestion_agent = workflow.ingestion_agent
        result = ingestion_agent.process(transactions)
        return {
            "status": "success",
            "data": result,
            "stage": "ingestion_complete"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/transactions/classify")
async def classify_transactions(transactions: List[Dict[str, Any]]):
    """
    Classify preprocessed transactions (Agents 2-3: NER/Merchant + Classifier)
    """
    try:
        # Process through NER/Merchant Agent
        ner_result = workflow.ner_merchant_agent.process(transactions)
        
        # Process through Classifier Agent
        classifier_result = workflow.classifier_agent.process(ner_result)
        
        return {
            "status": "success",
            "data": classifier_result,
            "stage": "classification_complete"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/transactions/analyze")
async def analyze_patterns(transactions: List[Dict[str, Any]]):
    """
    Analyze spending patterns (Agent 4: Pattern Analyzer)
    """
    try:
        result = workflow.pattern_analyzer_agent.process(transactions)
        return {
            "status": "success",
            "data": result,
            "stage": "pattern_analysis_complete"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pattern analysis failed: {str(e)}")


@app.post("/transactions/suggest")
async def generate_suggestions(pattern_insights: List[Dict[str, Any]], budget_thresholds: Dict[str, float] = None):
    """
    Generate financial suggestions (Agent 5: Suggestion Agent)
    """
    try:
        input_data = {
            "pattern_insights": pattern_insights,
            "budget_thresholds": budget_thresholds or {},
            "user_preferences": {}
        }
        result = workflow.suggestion_agent.process(input_data)
        return {
            "status": "success",
            "data": result,
            "stage": "suggestions_complete"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion generation failed: {str(e)}")


@app.post("/transactions/security-check")
async def security_check(transactions: List[Dict[str, Any]], user_profile: Dict[str, Any] = None):
    """
    Perform security and anomaly checks (Agent 6: Safety Guard)
    """
    try:
        input_data = {
            "classified_transactions": transactions,
            "user_profile": user_profile or {}
        }
        result = workflow.safety_guard_agent.process(input_data)
        return {
            "status": "success",
            "data": result,
            "stage": "security_check_complete"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Security check failed: {str(e)}")


@app.get("/agents/status")
async def get_agents_status():
    """
    Get status of all agents in the pipeline
    """
    return {
        "agents": [
            {"name": "Ingestion Agent", "status": "active", "description": "Normalizes raw transaction data"},
            {"name": "NER/Merchant Agent", "status": "active", "description": "Extracts merchant information"},
            {"name": "Classifier Agent", "status": "active", "description": "Predicts expense categories"},
            {"name": "Pattern Analyzer Agent", "status": "active", "description": "Detects spending patterns"},
            {"name": "Suggestion Agent", "status": "active", "description": "Generates financial recommendations"},
            {"name": "Safety Guard Agent", "status": "active", "description": "Flags anomalies and security issues"}
        ],
        "workflow_status": "ready"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
