"""
Backend API Routes - Analytics
Handles analytics and reporting endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum

from ..models.user import User
from ..models.analytics import (
    SpendingAnalytics, CategoryBreakdown, TrendAnalysis,
    AnalyticsPeriod, AnalyticsMetric
)
from ..services.analytics_service import AnalyticsService
from ..services.auth_service import get_current_user
from ..core.database import get_db_session

router = APIRouter(prefix="/analytics", tags=["analytics"])

class PeriodType(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"

class MetricType(str, Enum):
    spending = "spending"
    income = "income"
    balance = "balance"
    transactions = "transactions"

@router.get("/spending", response_model=SpendingAnalytics)
async def get_spending_analytics(
    period: PeriodType = Query(default=PeriodType.monthly),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    categories: Optional[List[str]] = Query(default=None),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get comprehensive spending analytics
    """
    try:
        analytics_service = AnalyticsService(db)

        # Set default date range if not provided
        if not start_date:
            if period == PeriodType.monthly:
                start_date = date.today().replace(day=1)
            elif period == PeriodType.weekly:
                start_date = date.today() - timedelta(days=7)
            elif period == PeriodType.yearly:
                start_date = date.today().replace(month=1, day=1)
            else:
                start_date = date.today() - timedelta(days=30)

        if not end_date:
            end_date = date.today()

        analytics = await analytics_service.get_spending_analytics(
            user_id=user.id,
            period=period.value,
            start_date=start_date,
            end_date=end_date,
            categories=categories
        )

        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/{period}", response_model=CategoryBreakdown)
async def get_category_breakdown(
    period: PeriodType,
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get spending breakdown by categories
    """
    try:
        analytics_service = AnalyticsService(db)

        # Set default date range based on period
        if not start_date:
            if period == PeriodType.monthly:
                start_date = date.today().replace(day=1)
            elif period == PeriodType.weekly:
                start_date = date.today() - timedelta(days=7)
            elif period == PeriodType.yearly:
                start_date = date.today().replace(month=1, day=1)
            else:
                start_date = date.today() - timedelta(days=30)

        if not end_date:
            end_date = date.today()

        breakdown = await analytics_service.get_category_breakdown(
            user_id=user.id,
            period=period.value,
            start_date=start_date,
            end_date=end_date
        )

        return breakdown

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends", response_model=TrendAnalysis)
async def get_trends(
    metric: MetricType = Query(default=MetricType.spending),
    period: PeriodType = Query(default=PeriodType.daily),
    lookback_days: int = Query(default=30, ge=7, le=365),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get trend analysis for various metrics
    """
    try:
        analytics_service = AnalyticsService(db)

        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        trends = await analytics_service.get_trend_analysis(
            user_id=user.id,
            metric=metric.value,
            period=period.value,
            start_date=start_date,
            end_date=end_date
        )

        return trends

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/dashboard", response_model=Dict[str, Any])
async def get_dashboard_summary(
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get comprehensive dashboard summary with key metrics
    """
    try:
        analytics_service = AnalyticsService(db)

        # Get current month data
        current_month_start = date.today().replace(day=1)
        current_month_end = date.today()

        # Get previous month data for comparison
        if current_month_start.month == 1:
            prev_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
        else:
            prev_month_start = current_month_start.replace(month=current_month_start.month - 1)

        prev_month_end = current_month_start - timedelta(days=1)

        # Get all dashboard data
        dashboard_data = await analytics_service.get_dashboard_summary(
            user_id=user.id,
            current_period_start=current_month_start,
            current_period_end=current_month_end,
            previous_period_start=prev_month_start,
            previous_period_end=prev_month_end
        )

        return dashboard_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/merchants/top", response_model=Dict[str, Any])
async def get_top_merchants(
    limit: int = Query(default=10, ge=1, le=50),
    period_days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get top merchants by spending
    """
    try:
        analytics_service = AnalyticsService(db)

        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        top_merchants = await analytics_service.get_top_merchants(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )

        return {
            "merchants": top_merchants,
            "period_days": period_days,
            "total_merchants": len(top_merchants)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/spending/forecast", response_model=Dict[str, Any])
async def get_spending_forecast(
    forecast_days: int = Query(default=30, ge=7, le=90),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get spending forecast based on historical data
    """
    try:
        analytics_service = AnalyticsService(db)

        forecast = await analytics_service.get_spending_forecast(
            user_id=user.id,
            forecast_days=forecast_days
        )

        return forecast

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/budget/performance", response_model=Dict[str, Any])
async def get_budget_performance(
    period: PeriodType = Query(default=PeriodType.monthly),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get budget performance analysis
    """
    try:
        analytics_service = AnalyticsService(db)

        # Set date range based on period
        if period == PeriodType.monthly:
            start_date = date.today().replace(day=1)
        elif period == PeriodType.weekly:
            start_date = date.today() - timedelta(days=7)
        elif period == PeriodType.yearly:
            start_date = date.today().replace(month=1, day=1)
        else:
            start_date = date.today() - timedelta(days=30)

        end_date = date.today()

        budget_performance = await analytics_service.get_budget_performance(
            user_id=user.id,
            period=period.value,
            start_date=start_date,
            end_date=end_date
        )

        return budget_performance

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cash-flow", response_model=Dict[str, Any])
async def get_cash_flow_analysis(
    period: PeriodType = Query(default=PeriodType.monthly),
    lookback_periods: int = Query(default=12, ge=3, le=24),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get cash flow analysis (income vs expenses over time)
    """
    try:
        analytics_service = AnalyticsService(db)

        cash_flow = await analytics_service.get_cash_flow_analysis(
            user_id=user.id,
            period=period.value,
            lookback_periods=lookback_periods
        )

        return cash_flow

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns/spending", response_model=Dict[str, Any])
async def get_spending_patterns(
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get spending patterns analysis (day of week, time of day, etc.)
    """
    try:
        analytics_service = AnalyticsService(db)

        patterns = await analytics_service.get_spending_patterns(user_id=user.id)

        return patterns

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison/categories", response_model=Dict[str, Any])
async def get_category_comparison(
    compare_periods: int = Query(default=2, ge=2, le=12),
    period_type: PeriodType = Query(default=PeriodType.monthly),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Compare spending across categories over multiple periods
    """
    try:
        analytics_service = AnalyticsService(db)

        comparison = await analytics_service.get_category_comparison(
            user_id=user.id,
            compare_periods=compare_periods,
            period_type=period_type.value
        )

        return comparison

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomalies", response_model=Dict[str, Any])
async def get_spending_anomalies(
    lookback_days: int = Query(default=30, ge=7, le=90),
    sensitivity: float = Query(default=2.0, ge=1.0, le=5.0),
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Detect spending anomalies using statistical analysis
    """
    try:
        analytics_service = AnalyticsService(db)

        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        anomalies = await analytics_service.detect_spending_anomalies(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            sensitivity=sensitivity
        )

        return anomalies

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/goals/progress", response_model=Dict[str, Any])
async def get_goal_progress(
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Get progress on financial goals
    """
    try:
        analytics_service = AnalyticsService(db)

        goal_progress = await analytics_service.get_goal_progress(user_id=user.id)

        return goal_progress

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report/custom", response_model=Dict[str, Any])
async def generate_custom_report(
    report_config: Dict[str, Any],
    user: User = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    Generate custom analytics report based on user configuration
    """
    try:
        analytics_service = AnalyticsService(db)

        custom_report = await analytics_service.generate_custom_report(
            user_id=user.id,
            config=report_config
        )

        return custom_report

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
