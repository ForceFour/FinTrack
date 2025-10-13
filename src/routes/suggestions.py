"""
Backend API Routes - Suggestions and Recommendations
Handles AI-powered suggestions and financial recommendations
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from ..models.user import User
from ..models.suggestion import (
    Suggestion, SuggestionType, SuggestionCreate,
    BudgetRecommendation, SavingsOpportunity
)
from ..services.suggestion_service import SuggestionService
from ..services.auth_service import get_current_user
from ..core.database import get_db_session

router = APIRouter(prefix="/suggestions", tags=["suggestions"])

@router.get("/{suggestion_type}", response_model=Dict[str, Any])
async def get_suggestions(
    suggestion_type: str = "all",
    limit: int = Query(default=10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get AI-generated suggestions for the user
    Types: all, budget, savings, spending, goals, categories
    """
    try:
        suggestion_service = SuggestionService(db)

        # Validate suggestion type
        valid_types = ["all", "budget", "savings", "spending", "goals", "categories", "merchants"]
        if suggestion_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid suggestion type. Valid types: {valid_types}"
            )

        suggestions = await suggestion_service.get_suggestions(
            user_id=user.id,
            suggestion_type=suggestion_type,
            limit=limit
        )

        return {
            "suggestions": suggestions,
            "type": suggestion_type,
            "count": len(suggestions),
            "generated_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/budget", response_model=BudgetRecommendation)
async def get_budget_recommendations(
    income_data: Dict[str, Any],
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get personalized budget recommendations based on income and spending patterns
    """
    try:
        suggestion_service = SuggestionService(db)

        # Validate income data
        required_fields = ["monthly_income"]
        for field in required_fields:
            if field not in income_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        recommendations = await suggestion_service.generate_budget_recommendations(
            user_id=user.id,
            income_data=income_data
        )

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/savings", response_model=Dict[str, Any])
async def get_savings_opportunities(
    analysis_data: Optional[Dict[str, Any]] = None,
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Identify savings opportunities based on spending patterns
    """
    try:
        suggestion_service = SuggestionService(db)

        opportunities = await suggestion_service.identify_savings_opportunities(
            user_id=user.id,
            analysis_data=analysis_data or {}
        )

        return {
            "opportunities": opportunities,
            "total_potential_savings": sum(
                opp.get("potential_monthly_savings", 0) for opp in opportunities
            ),
            "analysis_period": "last_30_days",
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spending/optimization", response_model=Dict[str, Any])
async def get_spending_optimization(
    category: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get spending optimization suggestions for specific categories or overall
    """
    try:
        suggestion_service = SuggestionService(db)

        optimization = await suggestion_service.get_spending_optimization(
            user_id=user.id,
            category=category
        )

        return optimization

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/goals/recommendations", response_model=Dict[str, Any])
async def get_goal_recommendations(
    goal_data: Dict[str, Any],
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get recommendations for achieving financial goals
    """
    try:
        suggestion_service = SuggestionService(db)

        # Validate goal data
        required_fields = ["goal_type", "target_amount", "target_date"]
        for field in required_fields:
            if field not in goal_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        recommendations = await suggestion_service.generate_goal_recommendations(
            user_id=user.id,
            goal_data=goal_data
        )

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/optimization", response_model=Dict[str, Any])
async def get_category_optimization(
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get suggestions for optimizing spending categories
    """
    try:
        suggestion_service = SuggestionService(db)

        optimization = await suggestion_service.get_category_optimization(
            user_id=user.id
        )

        return optimization

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/merchants/alternatives", response_model=Dict[str, Any])
async def get_merchant_alternatives(
    merchant: str = Query(..., description="Merchant name to find alternatives for"),
    category: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get alternative merchants that might offer better value
    """
    try:
        suggestion_service = SuggestionService(db)

        alternatives = await suggestion_service.find_merchant_alternatives(
            user_id=user.id,
            merchant=merchant,
            category=category
        )

        return {
            "original_merchant": merchant,
            "alternatives": alternatives,
            "category": category,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/personalized", response_model=Dict[str, Any])
async def get_personalized_suggestions(
    preferences: Dict[str, Any],
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get personalized suggestions based on user preferences and behavior
    """
    try:
        suggestion_service = SuggestionService(db)

        suggestions = await suggestion_service.generate_personalized_suggestions(
            user_id=user.id,
            preferences=preferences
        )

        return {
            "suggestions": suggestions,
            "personalization_factors": [
                "spending_patterns",
                "income_level",
                "financial_goals",
                "risk_tolerance",
                "user_preferences"
            ],
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends/actionable", response_model=Dict[str, Any])
async def get_actionable_insights(
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get actionable insights based on spending trends and patterns
    """
    try:
        suggestion_service = SuggestionService(db)

        insights = await suggestion_service.generate_actionable_insights(
            user_id=user.id
        )

        return insights

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback", response_model=Dict[str, Any])
async def submit_suggestion_feedback(
    feedback_data: Dict[str, Any],
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Submit feedback on suggestions to improve AI recommendations
    """
    try:
        suggestion_service = SuggestionService(db)

        # Validate feedback data
        required_fields = ["suggestion_id", "rating", "feedback_type"]
        for field in required_fields:
            if field not in feedback_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        result = await suggestion_service.record_suggestion_feedback(
            user_id=user.id,
            feedback_data=feedback_data
        )

        return {
            "status": "success",
            "message": "Feedback recorded successfully",
            "feedback_id": result.get("feedback_id"),
            "thank_you": "Your feedback helps improve our AI recommendations!"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=Dict[str, Any])
async def get_suggestion_history(
    limit: int = Query(default=50, ge=1, le=100),
    suggestion_type: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get history of suggestions provided to the user
    """
    try:
        suggestion_service = SuggestionService(db)

        history = await suggestion_service.get_suggestion_history(
            user_id=user.id,
            limit=limit,
            suggestion_type=suggestion_type
        )

        return {
            "history": history,
            "total_suggestions": len(history),
            "filter_type": suggestion_type,
            "limit": limit
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-generate", response_model=Dict[str, Any])
async def batch_generate_suggestions(
    generation_config: Dict[str, Any],
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Generate multiple types of suggestions in batch for dashboard
    """
    try:
        suggestion_service = SuggestionService(db)

        batch_suggestions = await suggestion_service.batch_generate_suggestions(
            user_id=user.id,
            config=generation_config
        )

        return {
            "suggestions": batch_suggestions,
            "generated_types": list(batch_suggestions.keys()),
            "total_suggestions": sum(
                len(suggestions) for suggestions in batch_suggestions.values()
            ),
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
