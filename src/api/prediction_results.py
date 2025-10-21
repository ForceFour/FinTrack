"""
Prediction Results API - Read-only access to processed prediction results
This endpoint ONLY reads from the database, never triggers the pipeline
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..core.database_config import get_db_client
import hashlib

router = APIRouter(prefix="/prediction-results", tags=["prediction-results"])


def _generate_suggestion_hash(suggestion: Dict[str, Any]) -> str:
    """Generate a unique hash for a suggestion based on its content"""
    # Use key fields to create a unique identifier
    # Normalize and clean the content to catch variations
    def clean_text(text):
        if not text:
            return ""
        # More aggressive normalization
        cleaned = str(text).lower().strip()
        # Remove extra whitespace
        cleaned = " ".join(cleaned.split())
        # Remove common punctuation that might vary
        cleaned = cleaned.replace(".", "").replace(",", "").replace("!", "").replace("?", "")
        return cleaned
    
    # Only use core content fields, exclude metadata that might vary between workflows
    core_fields = [
        clean_text(suggestion.get("title", "")),
        clean_text(suggestion.get("description", "")),
        clean_text(suggestion.get("category", "")),
        clean_text(suggestion.get("suggestion_type", "")),
    ]
    
    # For savings, round to nearest 10 to group similar amounts
    savings = suggestion.get("potential_savings", 0) or suggestion.get("potential_monthly_savings", 0)
    if savings:
        # Round to nearest 10 to group similar savings amounts
        rounded_savings = str(round(float(savings) / 10) * 10)
        core_fields.append(rounded_savings)
    
    # Create a normalized string and hash it
    content_string = "|".join(core_fields)
    hash_result = hashlib.md5(content_string.encode()).hexdigest()
    
    print(f"DEBUG: Hash input: {content_string}")
    print(f"DEBUG: Hash result: {hash_result[:8]}")
    
    return hash_result


def _deduplicate_suggestions(suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate suggestions based on content similarity"""
    seen_hashes = set()
    seen_titles = set()  # Additional check for title similarity
    unique_suggestions = []
    
    print(f"DEBUG: Processing {len(suggestions)} suggestions for deduplication")
    
    for i, suggestion in enumerate(suggestions):
        # Generate hash based on content
        suggestion_hash = _generate_suggestion_hash(suggestion)
        
        # Also check for title similarity (case-insensitive, normalized)
        title = str(suggestion.get("title", "")).lower().strip()
        normalized_title = " ".join(title.split())  # Normalize whitespace
        
        print(f"DEBUG: Suggestion {i+1}: hash={suggestion_hash[:8]}, title='{suggestion.get('title', 'NO_TITLE')[:50]}...'")
        
        # Check both hash and title similarity
        is_duplicate = (suggestion_hash in seen_hashes) or (normalized_title and normalized_title in seen_titles)
        
        if not is_duplicate:
            seen_hashes.add(suggestion_hash)
            if normalized_title:
                seen_titles.add(normalized_title)
            
            # Add a unique ID based on content hash for consistent frontend rendering
            suggestion["id"] = f"suggestion_{suggestion_hash[:16]}"
            unique_suggestions.append(suggestion)
            print(f"DEBUG: Added unique suggestion (total unique: {len(unique_suggestions)})")
        else:
            print(f"DEBUG: Skipped duplicate suggestion (hash duplicate: {suggestion_hash in seen_hashes}, title duplicate: {normalized_title in seen_titles})")
    
    print(f"DEBUG: Deduplication complete: {len(suggestions)} -> {len(unique_suggestions)} (removed {len(suggestions) - len(unique_suggestions)} duplicates)")
    
    return unique_suggestions

@router.get("/user/{user_id}/latest")
async def get_latest_predictions(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    status: Optional[str] = Query(default="completed")
):
    """
    Get latest prediction results for a user
    This ONLY reads from database, does NOT trigger pipeline
    """
    try:
        supabase = await get_db_client()

        query = supabase.table("prediction_results").select("*").eq("user_id", user_id)

        if status:
            query = query.eq("status", status)

        result = query.order("created_at", desc=True).limit(limit).execute()

        return {
            "status": "success",
            "count": len(result.data) if result.data else 0,
            "predictions": result.data or []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch predictions: {str(e)}")


@router.get("/user/{user_id}/workflow/{workflow_id}")
async def get_prediction_by_workflow(
    user_id: str,
    workflow_id: str
):
    """
    Get prediction result by workflow ID
    """
    try:
        supabase = await get_db_client()

        result = supabase.table("prediction_results").select("*").eq("user_id", user_id).eq("workflow_id", workflow_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Prediction not found")

        return {
            "status": "success",
            "prediction": result.data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch prediction: {str(e)}")


@router.get("/user/{user_id}/suggestions")
async def get_suggestions_from_predictions(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100)
):
    """
    Get all suggestions from stored prediction results
    This aggregates suggestions from all completed workflows
    """
    try:
        supabase = await get_db_client()

        # First check if user has any transactions
        tx_check = supabase.table("transactions").select("id").eq("user_id", user_id).limit(1).execute()
        
        # If no transactions exist, return empty suggestions (clear all suggestions)
        if not tx_check.data or len(tx_check.data) == 0:
            return {
                "status": "success",
                "suggestions": [],
                "budget_recommendations": [],
                "spending_suggestions": [],
                "savings_opportunities": [],
                "total_count": 0,
                "message": "No transactions found. Upload transactions to generate suggestions."
            }

       # Get completed predictions with suggestions - limit to recent workflows to reduce duplicates
        # Limit to last 5 workflows to get fresh suggestions without too much historical data
        recent_workflows_limit = min(5, limit)
        result = supabase.table("prediction_results").select(
            "workflow_id, budget_recommendations, spending_suggestions, savings_opportunities, suggestion_confidence, created_at"
        ).eq("user_id", user_id).eq("status", "completed").not_.is_("budget_recommendations", "null").order("created_at", desc=True).limit(recent_workflows_limit).execute()

        if not result.data:
            return {
                "status": "success",
                "suggestions": [],
                "budget_recommendations": [],
                "spending_suggestions": [],
                "savings_opportunities": [],
                "total_count": 0,
                "message": "No suggestions available. Upload transactions to generate suggestions."
            }

        # Aggregate all suggestions
        all_budget_recs = []
        all_spending_suggs = []
        all_savings_opps = []

        print(f"DEBUG: Processing {len(result.data)} workflows for suggestions")
        
        for i, prediction in enumerate(result.data):
            print(f"DEBUG: Processing workflow {i+1}: {prediction['workflow_id']}")

            if prediction.get("budget_recommendations"):
                for rec in prediction["budget_recommendations"]:
                    if rec and isinstance(rec, dict):
                        # Make a copy to avoid modifying the original
                        rec_copy = rec.copy()
                        rec_copy["workflow_id"] = prediction["workflow_id"]
                        rec_copy["generated_at"] = prediction["created_at"]
                        all_budget_recs.append(rec_copy)
                print(f"DEBUG: Added {len(prediction['budget_recommendations'])} budget recommendations")

            if prediction.get("spending_suggestions"):
                for sugg in prediction["spending_suggestions"]:
                    if sugg and isinstance(sugg, dict):
                      # Make a copy to avoid modifying the original
                        sugg_copy = sugg.copy()
                        sugg_copy["workflow_id"] = prediction["workflow_id"]
                        sugg_copy["generated_at"] = prediction["created_at"]
                        all_spending_suggs.append(sugg_copy)
                print(f"DEBUG: Added {len(prediction['spending_suggestions'])} spending suggestions")
  

            if prediction.get("savings_opportunities"):
                for opp in prediction["savings_opportunities"]:
                    if opp and isinstance(opp, dict):
                        # Make a copy to avoid modifying the original
                        opp_copy = opp.copy()
                        opp_copy["workflow_id"] = prediction["workflow_id"]
                        opp_copy["generated_at"] = prediction["created_at"]
                        all_savings_opps.append(opp_copy)
                print(f"DEBUG: Added {len(prediction['savings_opportunities'])} savings opportunities")

        # Combine all suggestions with type labeling
        all_suggestions = []
        for rec in all_budget_recs:
            all_suggestions.append({**rec, "suggestion_type": "budget_adjustment"})
        for sugg in all_spending_suggs:
            all_suggestions.append({**sugg, "suggestion_type": "spending_reduction"})
        for opp in all_savings_opps:
            all_suggestions.append({**opp, "suggestion_type": "savings_opportunity"})

        print(f"DEBUG: Total suggestions before deduplication: {len(all_suggestions)}")
        print(f"DEBUG: Budget: {len(all_budget_recs)}, Spending: {len(all_spending_suggs)}, Savings: {len(all_savings_opps)}")

        # Sort suggestions by generated_at timestamp (newest first) before deduplication
        # This ensures that if there are duplicates, we keep the most recent version
        all_suggestions.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

        # Deduplicate all suggestion lists based on content (title + category + description)
        def deduplicate_by_content(suggestions_list):
            """Remove duplicates based on title, category, and description."""
            seen = set()
            unique = []
            for item in suggestions_list:
                # Create unique key from title, category, and description
                key = f"{item.get('title', '')}|{item.get('category', '')}|{item.get('description', '')}"
                if key not in seen:
                    seen.add(key)
                    unique.append(item)
            return unique

        # Deduplicate suggestions based on content similarity
        unique_suggestions = _deduplicate_suggestions(all_suggestions)
        
        # Also deduplicate the individual lists to prevent duplicates in budget, spending, and savings
        unique_budget_recs = deduplicate_by_content(all_budget_recs)
        unique_spending_suggs = deduplicate_by_content(all_spending_suggs)
        unique_savings_opps = deduplicate_by_content(all_savings_opps)

        print(f"DEBUG: After deduplication - Budget: {len(unique_budget_recs)}, Spending: {len(unique_spending_suggs)}, Savings: {len(unique_savings_opps)}")

        return {
            "status": "success",
            "suggestions": unique_suggestions,
            "budget_recommendations": unique_budget_recs,
            "spending_suggestions": unique_spending_suggs,
            "savings_opportunities": unique_savings_opps,
           "total_count": len(unique_suggestions),
            "workflows_analyzed": len(result.data),
            "original_count": len(all_suggestions),
            "duplicates_removed": len(all_suggestions) - len(unique_suggestions)
        }
        

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch suggestions: {str(e)}")


@router.get("/user/{user_id}/analytics")
async def get_analytics_from_predictions(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100)
):
    """
    Get analytics data from stored prediction results
    This aggregates analytics from all completed workflows AND builds spending summary from transactions
    """
    try:
        supabase = await get_db_client()

        # Get completed predictions with analytics data (for pattern insights)
        result = supabase.table("prediction_results").select(
            "workflow_id, pattern_insights, created_at"
        ).eq("user_id", user_id).eq("status", "completed").order("created_at", desc=True).limit(limit).execute()

        # Get actual transactions to build spending summary
        tx_result = supabase.table("transactions").select(
            "category, merchant, amount, transaction_type"
        ).eq("user_id", user_id).execute()

        if not result.data and not tx_result.data:
            return {
                "status": "success",
                "spending_patterns": {
                    "total_transactions": 0,
                    "total_income": 0,
                    "total_expenses": 0,
                    "income_categories": {},
                    "expense_categories": {},
                    "categories": {},
                    "merchants": {},
                    "total_analyzed": 0
                },
                "pattern_insights": [],
                "transactions_analyzed": 0,
                "message": "No analytics data available. Upload transactions to generate analytics."
            }

        # Build spending summary from actual transactions
        categories = {}
        income_categories = {}
        expense_categories = {}
        merchants = {}
        total_income = 0
        total_expenses = 0

        for tx in (tx_result.data or []):
            try:
                # Build category summary
                cat = tx.get("category") or "uncategorized"
                tx_type = tx.get("transaction_type") or "expense"

                if cat not in categories:
                    categories[cat] = {"count": 0, "total_amount": 0, "type": tx_type}
                categories[cat]["count"] += 1

                # Safely parse amount
                amount_val = tx.get("amount")
                if amount_val is not None:
                    try:
                        amount = abs(float(amount_val))
                        categories[cat]["total_amount"] += amount

                        # Separate income vs expenses
                        if tx_type == "income":
                            total_income += amount
                            if cat not in income_categories:
                                income_categories[cat] = {"count": 0, "total_amount": 0}
                            income_categories[cat]["count"] += 1
                            income_categories[cat]["total_amount"] += amount
                        else:
                            total_expenses += amount
                            if cat not in expense_categories:
                                expense_categories[cat] = {"count": 0, "total_amount": 0}
                            expense_categories[cat]["count"] += 1
                            expense_categories[cat]["total_amount"] += amount
                    except (ValueError, TypeError):
                        # Skip invalid amounts
                        pass

                # Build merchant summary
                merchant = tx.get("merchant") or "Unknown"
                if merchant not in merchants:
                    merchants[merchant] = {"count": 0, "total_amount": 0, "type": tx_type}
                merchants[merchant]["count"] += 1

                # Add amount to merchant
                if amount_val is not None:
                    try:
                        amount = abs(float(amount_val))
                        merchants[merchant]["total_amount"] += amount
                    except (ValueError, TypeError):
                        # Skip invalid amounts
                        pass
            except Exception as tx_error:
                # Skip problematic transactions
                print(f"Error processing transaction: {tx_error}")
                continue

        # Build spending patterns summary
        spending_patterns = {
            "total_transactions": len(tx_result.data) if tx_result.data else 0,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "income_categories": income_categories,
            "expense_categories": expense_categories,
            "categories": categories,
            "merchants": merchants,
            "total_analyzed": len(result.data) if result.data else 0
        }

        # Collect all pattern insights from prediction results
        all_insights = []
        for prediction in (result.data or []):
            if prediction.get("pattern_insights"):
                for insight in prediction["pattern_insights"]:
                    if insight and isinstance(insight, dict):
                        insight["workflow_id"] = prediction["workflow_id"]
                        all_insights.append(insight)

        return {
            "status": "success",
            "spending_patterns": spending_patterns,
            "pattern_insights": all_insights,
            "transactions_analyzed": len(tx_result.data) if tx_result.data else 0,
            "workflows_analyzed": len(result.data) if result.data else 0
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in get_analytics_from_predictions: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")


@router.get("/user/{user_id}/security")
async def get_security_from_predictions(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100)
):
    """
    Get security alerts from stored prediction results
    """
    try:
        supabase = await get_db_client()

        # Get predictions with security data
        result = supabase.table("prediction_results").select(
            "workflow_id, security_alerts, risk_assessment, fraud_score, anomaly_score, "
            "requires_human_review, created_at"
        ).eq("user_id", user_id).eq("status", "completed").order("created_at", desc=True).limit(limit).execute()

        if not result.data:
            return {
                "status": "success",
                "security_alerts": [],
                "total_alerts": 0,
                "message": "No security data available."
            }

        # Aggregate security alerts
        all_alerts = []
        high_risk_count = 0

        for prediction in result.data:
            if prediction.get("security_alerts"):
                for alert in prediction["security_alerts"]:
                    if alert and isinstance(alert, dict):
                        alert["workflow_id"] = prediction["workflow_id"]
                        alert["detected_at"] = prediction["created_at"]
                        all_alerts.append(alert)

                        if alert.get("severity") in ["high", "critical"]:
                            high_risk_count += 1

        return {
            "status": "success",
            "security_alerts": all_alerts,
            "total_alerts": len(all_alerts),
            "high_risk_count": high_risk_count,
            "workflows_analyzed": len(result.data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch security data: {str(e)}")


@router.get("/user/{user_id}/grouped-by-workflow")
async def get_grouped_by_workflow(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Get prediction results grouped by workflow_id
    Shows all transactions processed in each workflow batch
    """
    try:
        supabase = await get_db_client()

        # Get predictions grouped by workflow
        result = supabase.table("prediction_results").select(
            "workflow_id, status, predicted_category, merchant_name, "
            "final_transaction, created_at, completed_at, raw_transaction_count"
        ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()

        if not result.data:
            return {
                "status": "success",
                "workflows": [],
                "total_workflows": 0,
                "message": "No workflows found."
            }

        # Group by workflow_id
        workflows = {}
        for prediction in result.data:
            wf_id = prediction["workflow_id"]
            if wf_id not in workflows:
                workflows[wf_id] = {
                    "workflow_id": wf_id,
                    "status": prediction["status"],
                    "created_at": prediction["created_at"],
                    "completed_at": prediction.get("completed_at"),
                    "transaction_count": prediction.get("raw_transaction_count", 0),
                    "transactions": []
                }

            # Add transaction details
            if prediction.get("final_transaction"):
                workflows[wf_id]["transactions"].append({
                    "category": prediction.get("predicted_category"),
                    "merchant": prediction.get("merchant_name"),
                    "details": prediction["final_transaction"]
                })

        return {
            "status": "success",
            "workflows": list(workflows.values()),
            "total_workflows": len(workflows)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch grouped workflows: {str(e)}")
