"""
Suggestion Models - Data models for AI-powered suggestions and recommendations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from datetime import date as Date
from decimal import Decimal
from enum import Enum

class SuggestionType(str, Enum):
    """Types of suggestions"""
    BUDGET = "budget"
    SAVINGS = "savings"
    SPENDING = "spending"
    GOAL = "goal"
    CATEGORY = "category"
    MERCHANT = "merchant"
    SECURITY = "security"

class SuggestionPriority(str, Enum):
    """Suggestion priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SuggestionStatus(str, Enum):
    """Suggestion status"""
    ACTIVE = "active"
    IMPLEMENTED = "implemented"
    DISMISSED = "dismissed"
    EXPIRED = "expired"

class Suggestion(BaseModel):
    """Base suggestion model"""
    id: Optional[str] = None
    type: SuggestionType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    priority: SuggestionPriority = SuggestionPriority.MEDIUM
    status: SuggestionStatus = SuggestionStatus.ACTIVE
    potential_savings: Optional[Decimal] = None
    implementation_difficulty: str = "medium"  # "easy", "medium", "hard"
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}

class SuggestionCreate(BaseModel):
    """Suggestion creation model"""
    type: SuggestionType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    priority: SuggestionPriority = SuggestionPriority.MEDIUM
    potential_savings: Optional[Decimal] = None
    implementation_difficulty: str = "medium"
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class BudgetRecommendation(BaseModel):
    """Budget recommendation model"""
    monthly_income: Decimal
    recommended_budget: Dict[str, Decimal]  # {category: amount}
    current_spending: Optional[Dict[str, Decimal]] = {}
    adjustments: List[Dict[str, Any]]
    savings_potential: Decimal
    confidence_score: float
    methodology: str = "ai_analysis"

class SavingsOpportunity(BaseModel):
    """Savings opportunity model"""
    opportunity_type: str  # "reduce_spending", "switch_merchant", "optimize_category"
    title: str
    description: str
    current_spending: Decimal
    potential_savings: Decimal
    savings_percentage: float
    difficulty: str
    timeframe: str  # "immediate", "short_term", "long_term"
    action_steps: List[str]
    confidence: float

class GoalRecommendation(BaseModel):
    """Financial goal recommendation"""
    goal_type: str  # "savings", "debt_payoff", "investment"
    target_amount: Decimal
    recommended_monthly_amount: Decimal
    timeframe_months: int
    current_progress: Optional[Decimal] = Decimal('0')
    adjustments_needed: List[Dict[str, Any]]
    success_probability: float
    alternative_strategies: List[Dict[str, Any]]

class MerchantAlternative(BaseModel):
    """Alternative merchant suggestion"""
    current_merchant: str
    alternative_merchant: str
    category: str
    potential_savings: Decimal
    quality_comparison: str  # "similar", "better", "lower"
    distance_comparison: str  # "closer", "similar", "farther"
    rating: Optional[float] = None
    reasons: List[str]

class SpendingOptimization(BaseModel):
    """Spending optimization suggestion"""
    category: str
    current_spending: Decimal
    optimal_spending: Decimal
    optimization_strategies: List[Dict[str, Any]]
    impact_assessment: Dict[str, Any]
    priority_score: float

class PersonalizedSuggestion(BaseModel):
    """Personalized suggestion based on user behavior"""
    user_id: str
    personalization_factors: List[str]
    suggestions: List[Suggestion]
    confidence_score: float
    generation_method: str
    last_updated: datetime

class SuggestionFeedback(BaseModel):
    """User feedback on suggestions"""
    suggestion_id: str
    user_id: str
    rating: int = Field(..., ge=1, le=5)  # 1-5 star rating
    feedback_type: str  # "helpful", "not_helpful", "irrelevant", "implemented"
    comments: Optional[str] = Field(None, max_length=500)
    implementation_status: Optional[str] = None
    created_at: Optional[datetime] = None

class SuggestionHistory(BaseModel):
    """Suggestion history tracking"""
    user_id: str
    suggestion_id: str
    action: str  # "generated", "viewed", "implemented", "dismissed"
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = {}

class ActionableInsight(BaseModel):
    """Actionable insights from data analysis"""
    insight_type: str
    title: str
    description: str
    data_points: List[Dict[str, Any]]
    recommended_actions: List[str]
    potential_impact: str
    urgency: SuggestionPriority
    confidence: float

class SuggestionBatch(BaseModel):
    """Batch of suggestions for dashboard"""
    user_id: str
    suggestions_by_type: Dict[str, List[Suggestion]]
    total_potential_savings: Decimal
    priority_suggestions: List[Suggestion]
    generated_at: datetime
    expires_at: datetime
