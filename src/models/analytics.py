"""
Analytics Models - Data models for financial analytics and reporting
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from datetime import date as Date
from decimal import Decimal
from enum import Enum

class AnalyticsPeriod(str, Enum):
    """Analytics time periods"""
    DAILY = "daily"
    WEEKLY = "weekly" 
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class AnalyticsMetric(str, Enum):
    """Analytics metrics"""
    SPENDING = "spending"
    INCOME = "income"
    BALANCE = "balance"
    TRANSACTIONS = "transactions"

class SpendingAnalytics(BaseModel):
    """Comprehensive spending analytics"""
    period: AnalyticsPeriod
    total_spending: Decimal
    average_transaction: Decimal
    transaction_count: int
    top_category: Optional[str] = None
    spending_trend: str  # "increasing", "decreasing", "stable"
    period_comparison: Optional[Dict[str, Union[Decimal, float]]] = {}
    category_breakdown: Optional[Dict[str, Decimal]] = {}

class CategoryBreakdown(BaseModel):
    """Category spending breakdown"""
    period: AnalyticsPeriod
    categories: Dict[str, Dict[str, Union[Decimal, int, float]]]
    total_amount: Decimal
    category_count: int
    top_categories: List[Dict[str, Any]]

class TrendAnalysis(BaseModel):
    """Trend analysis data"""
    metric: AnalyticsMetric
    period: AnalyticsPeriod
    data_points: List[Dict[str, Union[Date, Decimal, int]]]
    trend_direction: str  # "up", "down", "stable"
    trend_strength: float  # 0.0 to 1.0
    forecast: Optional[List[Dict[str, Any]]] = []

class BudgetPerformance(BaseModel):
    """Budget vs actual performance"""
    period: AnalyticsPeriod
    categories: Dict[str, Dict[str, Decimal]]  # {category: {budget, actual, variance}}
    total_budget: Decimal
    total_spent: Decimal
    overall_variance: Decimal
    performance_score: float  # 0.0 to 1.0

class CashFlowAnalysis(BaseModel):
    """Cash flow analysis"""
    period: AnalyticsPeriod
    periods: List[Dict[str, Union[str, Decimal]]]  # [{period, income, expenses, net}]
    average_income: Decimal
    average_expenses: Decimal
    average_net: Decimal
    trend: str

class SpendingPattern(BaseModel):
    """Spending pattern analysis"""
    by_day_of_week: Dict[str, Decimal]
    by_hour_of_day: Dict[int, Decimal]
    by_month: Dict[str, Decimal]
    seasonal_trends: Dict[str, Any]
    peak_spending_times: List[Dict[str, Any]]

class FinancialGoalProgress(BaseModel):
    """Financial goal progress tracking"""
    goal_id: str
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    progress_percentage: float
    target_date: Date
    projected_completion: Optional[Date] = None
    on_track: bool

class DashboardSummary(BaseModel):
    """Dashboard summary data"""
    current_balance: Decimal
    monthly_spending: Decimal
    monthly_income: Decimal
    budget_utilization: float
    top_categories: List[Dict[str, Any]]
    recent_transactions: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    goals_progress: List[FinancialGoalProgress]

class MerchantAnalysis(BaseModel):
    """Merchant spending analysis"""
    merchant_name: str
    total_spent: Decimal
    transaction_count: int
    average_transaction: Decimal
    frequency: str  # "daily", "weekly", "monthly", etc.
    trend: str
    category: Optional[str] = None

class AnomalyDetection(BaseModel):
    """Spending anomaly detection"""
    transaction_id: str
    anomaly_type: str  # "amount", "frequency", "merchant", "category"
    risk_score: float  # 0.0 to 1.0
    description: str
    suggested_action: str
    confidence: float

class ForecastData(BaseModel):
    """Financial forecasting data"""
    forecast_type: str  # "spending", "income", "balance"
    period: AnalyticsPeriod
    historical_data: List[Dict[str, Any]]
    forecast_points: List[Dict[str, Any]]
    confidence_interval: Dict[str, float]
    methodology: str
    accuracy_score: Optional[float] = None
