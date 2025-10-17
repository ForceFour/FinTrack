"""
Analytics API endpoint - Provides pattern insights and analytics data
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..workflows.unified_workflow import UnifiedTransactionWorkflow
from ..core.database_config import get_db_client
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/patterns/{user_id}")
async def get_pattern_insights(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled for testing
):
    """Get pattern insights and analytics for user transactions"""
    try:
        supabase = await get_db_client()

        # Build query filters
        query = supabase.table("transactions").select("*").eq("user_id", user_id)

        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)

        # Get user transactions
        result = query.order("date", desc=True).execute()

        if not result.data:
            return {
                "patterns": [],
                "insights": [],
                "spending_summary": {},
                "recommendations": [],
                "security_alerts": []
            }

        # Convert transactions to expected format
        raw_transactions = []
        for tx in result.data:
            raw_transactions.append({
                "date": tx["date"],
                "amount": str(tx["amount"]),
                "description": tx["description"] or "",
                "payment_method": tx.get("payment_method", "unknown"),
                "merchant_name": tx.get("merchant_name", ""),
                "category": tx.get("category", "miscellaneous")
            })

        # Process through workflow to get insights
        workflow = UnifiedTransactionWorkflow()
        analysis_result = await workflow.execute_workflow(
            raw_transactions=raw_transactions,
            conversation_context={"user_id": user_id},
            user_input="Analyze my spending patterns",
            user_id=user_id
        )

        if analysis_result.get("status") != "success":
            raise HTTPException(status_code=500, detail="Analysis failed")

        workflow_data = analysis_result["result"]

        # Extract and format the data for frontend
        response_data = {
            "patterns": {
                "spending_patterns": workflow_data.get("spending_patterns", {}),
                "total_income": workflow_data.get("spending_patterns", {}).get("total_income", 0),
                "total_expenses": workflow_data.get("spending_patterns", {}).get("total_expenses", 0),
                "net_cashflow": workflow_data.get("spending_patterns", {}).get("net_cashflow", 0),
                "expenses_by_category": workflow_data.get("spending_patterns", {}).get("expenses_by_category", {}),
                "category_percentages": workflow_data.get("spending_patterns", {}).get("category_percentages", {})
            },
            "insights": workflow_data.get("pattern_insights", []),
            "recommendations": {
                "budget_recommendations": workflow_data.get("budget_recommendations", []),
                "spending_suggestions": workflow_data.get("spending_suggestions", [])
            },
            "security_alerts": workflow_data.get("security_alerts", []),
            "confidence": {
                "overall": workflow_data.get("pattern_confidence", 0),
                "pattern_analysis": workflow_data.get("pattern_confidence", 0),
                "suggestions": workflow_data.get("suggestion_confidence", 0),
                "security": workflow_data.get("safety_confidence", 0)
            },
            "metadata": {
                "total_transactions": len(raw_transactions),
                "analysis_date": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date,
                    "end": end_date
                }
            }
        }

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/suggestions/{user_id}")
async def get_suggestions(
    user_id: str,
    suggestion_type: Optional[str] = None,
    priority: Optional[str] = None,
    # current_user: dict = Depends(get_current_user)  # Temporarily disabled for testing
):
    """Get personalized suggestions for the user"""
    try:
        supabase = await get_db_client()

        # Get recent transactions for analysis
        recent_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        result = supabase.table("transactions").select("*").eq("user_id", user_id).gte("date", recent_date).execute()

        if not result.data:
            # Return empty suggestions for new users - no hardcoded data
            return {
                "suggestions": [],
                "total_count": 0,
                "high_priority_count": 0,
                "message": "No transactions found. Upload transactions to generate personalized suggestions."
            }

        # Convert and analyze transactions
        raw_transactions = []
        for tx in result.data:
            raw_transactions.append({
                "date": tx["date"],
                "amount": str(tx["amount"]),
                "description": tx["description"] or "",
                "payment_method": tx.get("payment_method", "unknown"),
                "merchant_name": tx.get("merchant_name", ""),
                "category": tx.get("category", "miscellaneous")
            })

        # Get suggestions from workflow
        workflow = UnifiedTransactionWorkflow()
        analysis_result = await workflow.execute_workflow(
            raw_transactions=raw_transactions,
            conversation_context={"user_id": user_id},
            user_input="Give me financial suggestions",
            user_id=user_id
        )

        if analysis_result.get("status") != "success":
            raise HTTPException(status_code=500, detail="Suggestion analysis failed")

        workflow_data = analysis_result["result"]

        # Combine all suggestions
        all_suggestions = []
        all_suggestions.extend(workflow_data.get("budget_recommendations", []))
        all_suggestions.extend(workflow_data.get("spending_suggestions", []))

        # Filter by type and priority if specified
        filtered_suggestions = all_suggestions
        if suggestion_type:
            filtered_suggestions = [s for s in filtered_suggestions if s.get("suggestion_type") == suggestion_type]
        if priority:
            filtered_suggestions = [s for s in filtered_suggestions if s.get("priority") == priority]

        # Count by priority
        high_priority_count = len([s for s in all_suggestions if s.get("priority") == "high"])
        medium_priority_count = len([s for s in all_suggestions if s.get("priority") == "medium"])
        low_priority_count = len([s for s in all_suggestions if s.get("priority") == "low"])

        return {
            "suggestions": filtered_suggestions,
            "total_count": len(all_suggestions),
            "filtered_count": len(filtered_suggestions),
            "priority_breakdown": {
                "high": high_priority_count,
                "medium": medium_priority_count,
                "low": low_priority_count
            },
            "confidence": workflow_data.get("suggestion_confidence", 0),
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

@router.post("/process-transactions/{user_id}")
async def process_transactions_for_analysis(
    user_id: str,
    transactions: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_user)
):
    """Process a batch of transactions and return full analytics"""
    try:
        # Process transactions through workflow
        workflow = UnifiedTransactionWorkflow()
        result = await workflow.execute_workflow(
            raw_transactions=transactions,
            conversation_context={"user_id": user_id},
            user_input="Analyze these transactions",
            user_id=user_id
        )

        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail="Transaction processing failed")

        workflow_data = result["result"]

        # Return comprehensive analysis
        return {
            "status": "success",
            "processed_transactions": len(transactions),
            "patterns": {
                "spending_patterns": workflow_data.get("spending_patterns", {}),
                "insights": workflow_data.get("pattern_insights", [])
            },
            "suggestions": {
                "budget_recommendations": workflow_data.get("budget_recommendations", []),
                "spending_suggestions": workflow_data.get("spending_suggestions", [])
            },
            "security": {
                "alerts": workflow_data.get("security_alerts", []),
                "risk_assessment": workflow_data.get("risk_assessment", {})
            },
            "confidence_scores": {
                "overall": result.get("overall_confidence", 0),
                "ingestion": workflow_data.get("ingestion_confidence", 0),
                "classification": workflow_data.get("category_confidence", 0),
                "pattern_analysis": workflow_data.get("pattern_confidence", 0),
                "suggestions": workflow_data.get("suggestion_confidence", 0),
                "security": workflow_data.get("safety_confidence", 0)
            },
            "metadata": {
                "execution_time": result.get("execution_time", 0),
                "workflow_id": workflow_data.get("workflow_id"),
                "processed_at": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process transactions: {str(e)}")
