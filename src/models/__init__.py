"""
Models Package - Export all data models
"""

from .user import User, UserCreate, UserUpdate, UserResponse, LoginRequest
from .auth import Token, TokenData, RefreshTokenRequest, SessionInfo
from .transaction import (
    Transaction, TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionType, TransactionStatus, TransactionSummary, TransactionFilter
)
from .analytics import (
    SpendingAnalytics, CategoryBreakdown, TrendAnalysis, AnalyticsPeriod, 
    AnalyticsMetric, BudgetPerformance, DashboardSummary
)
from .suggestion import (
    Suggestion, SuggestionCreate, SuggestionType, BudgetRecommendation,
    SavingsOpportunity, GoalRecommendation, SuggestionFeedback
)
from .agent import (
    AgentStatus, AgentTask, AgentResponse, WorkflowRequest, WorkflowStatus,
    AgentType, AgentState, TaskStatus, TaskPriority
)

__all__ = [
    # User models
    "User", "UserCreate", "UserUpdate", "UserResponse", "LoginRequest",
    
    # Auth models
    "Token", "TokenData", "RefreshTokenRequest", "SessionInfo",
    
    # Transaction models
    "Transaction", "TransactionCreate", "TransactionUpdate", "TransactionResponse",
    "TransactionType", "TransactionStatus", "TransactionSummary", "TransactionFilter",
    
    # Analytics models
    "SpendingAnalytics", "CategoryBreakdown", "TrendAnalysis", "AnalyticsPeriod",
    "AnalyticsMetric", "BudgetPerformance", "DashboardSummary",
    
    # Suggestion models
    "Suggestion", "SuggestionCreate", "SuggestionType", "BudgetRecommendation",
    "SavingsOpportunity", "GoalRecommendation", "SuggestionFeedback",
    
    # Agent models
    "AgentStatus", "AgentTask", "AgentResponse", "WorkflowRequest", "WorkflowStatus",
    "AgentType", "AgentState", "TaskStatus", "TaskPriority",
]
