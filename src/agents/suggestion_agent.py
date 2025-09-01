"""
Suggestion Agent - Agent 5
Role: Generate actionable financial recommendations
"""

from typing import Dict, Any, List
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor
from pydantic import BaseModel, Field

from ..schemas.transaction_schemas import PatternInsight, Suggestion
from ..utils.recommendation_engine import RecommendationEngine


class SuggestionAgentInput(BaseModel):
    """Input schema for Suggestion Agent"""
    pattern_insights: List[PatternInsight] = Field(description="Detected spending patterns and insights")
    budget_thresholds: Dict[str, float] = Field(description="User-defined budget thresholds by category")
    user_preferences: Dict[str, Any] = Field(description="User preferences and financial goals")


class SuggestionAgentOutput(BaseModel):
    """Output schema for Suggestion Agent"""
    suggestions: List[Suggestion] = Field(description="Actionable financial recommendations")
    alerts: List[Dict[str, Any]] = Field(description="Budget alerts and warnings")
    savings_opportunities: List[Dict[str, Any]] = Field(description="Identified savings opportunities")


class SuggestionAgent:
    """
    Agent 5: Suggestion Agent
    
    Responsibilities:
    - Generate actionable recommendations based on pattern analysis
    - Compare spending against budget thresholds
    - Suggest areas for spending reduction
    - Alert users about high recurring subscriptions
    - Recommend budget adjustments
    - Identify savings opportunities
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.recommendation_engine = RecommendationEngine()
    
    def generate_budget_alerts(self, insights: List[PatternInsight], thresholds: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate alerts for budget threshold violations"""
        return self.recommendation_engine.generate_budget_alerts(
            [insight.dict() for insight in insights],
            thresholds
        )
    
    def suggest_spending_reductions(self, insights: List[PatternInsight]) -> List[Suggestion]:
        """Suggest areas where spending can be reduced"""
        raw_suggestions = self.recommendation_engine.generate_spending_reduction_suggestions(
            [insight.dict() for insight in insights]
        )
        
        # Convert raw suggestions to Suggestion objects
        return [
            Suggestion(
                title=sugg['title'],
                description=sugg['description'],
                category=sugg.get('category', 'general'),
                priority=sugg['priority'],
                potential_savings=sugg.get('potential_savings', 0),
                action_items=sugg.get('action_items', []),
                metadata={
                    'type': sugg['type'],
                    'merchant': sugg.get('merchant'),
                    'monthly_cost': sugg.get('monthly_cost')
                }
            )
            for sugg in raw_suggestions
        ]
    
    def identify_subscription_alerts(self, insights: List[PatternInsight]) -> List[Dict[str, Any]]:
        """Alert about high or forgotten recurring subscriptions"""
        return self.recommendation_engine.generate_subscription_alerts(
            [insight.dict() for insight in insights]
        )
    
    def recommend_budget_adjustments(self, insights: List[PatternInsight], thresholds: Dict[str, float]) -> List[Suggestion]:
        """Recommend budget threshold adjustments based on spending patterns"""
        raw_recommendations = self.recommendation_engine.generate_budget_recommendations(
            [insight.dict() for insight in insights],
            thresholds
        )
        
        # Convert raw recommendations to Suggestion objects
        return [
            Suggestion(
                title=rec['title'],
                description=rec['description'],
                category=rec['category'],
                priority=rec['priority'],
                potential_savings=0,  # Budget adjustments don't have direct savings
                action_items=[f"Update {rec['category']} budget to ${rec['suggested_budget']:.2f}"],
                metadata={
                    'type': rec['type'],
                    'current_budget': rec['current_budget'],
                    'suggested_budget': rec['suggested_budget'],
                    'reason': rec['reason']
                }
            )
            for rec in raw_recommendations
        ]
    
    def find_savings_opportunities(self, insights: List[PatternInsight]) -> List[Dict[str, Any]]:
        """Identify potential savings opportunities"""
        return self.recommendation_engine.generate_savings_opportunities(
            [insight.dict() for insight in insights]
        )
    
    def prioritize_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Prioritize suggestions based on impact and feasibility"""
        # Convert Suggestion objects to dicts for the recommendation engine
        suggestion_dicts = [
            {
                'title': sugg.title,
                'description': sugg.description,
                'category': sugg.category,
                'priority': sugg.priority,
                'potential_savings': sugg.potential_savings,
                'action_items': sugg.action_items,
                **sugg.metadata
            }
            for sugg in suggestions
        ]
        
        # Get prioritized suggestions
        prioritized_dicts = self.recommendation_engine.prioritize_suggestions(suggestion_dicts)
        
        # Convert back to Suggestion objects while maintaining the new order
        return [
            Suggestion(
                title=sugg['title'],
                description=sugg['description'],
                category=sugg.get('category', 'general'),
                priority=sugg['priority'],
                potential_savings=sugg.get('potential_savings', 0),
                action_items=sugg.get('action_items', []),
                metadata={k: v for k, v in sugg.items() if k not in 
                         ['title', 'description', 'category', 'priority', 'potential_savings', 'action_items']}
            )
            for sugg in prioritized_dicts
        ]
    
    def process(self, input_data: SuggestionAgentInput) -> SuggestionAgentOutput:
        """Main processing method for the Suggestion Agent"""
        # Generate all suggestions and alerts
        budget_alerts = self.generate_budget_alerts(
            input_data.pattern_insights,
            input_data.budget_thresholds
        )
        
        spending_suggestions = self.suggest_spending_reductions(
            input_data.pattern_insights
        )
        
        subscription_alerts = self.identify_subscription_alerts(
            input_data.pattern_insights
        )
        
        budget_suggestions = self.recommend_budget_adjustments(
            input_data.pattern_insights,
            input_data.budget_thresholds
        )
        
        savings_opportunities = self.find_savings_opportunities(
            input_data.pattern_insights
        )
        
        # Combine all suggestions
        all_suggestions = (
            [Suggestion(
                title=alert['title'],
                description=alert['description'],
                category=alert.get('category', 'general'),
                priority=alert['priority'],
                potential_savings=alert.get('amount_exceeded', 0),
                action_items=['Review budget', 'Reduce spending in this category'],
                metadata={'type': 'budget_alert', **{k: v for k, v in alert.items() 
                                                   if k not in ['title', 'description', 'category', 'priority']}}
            ) for alert in budget_alerts]
            + spending_suggestions
            + budget_suggestions
            + [Suggestion(
                title=opp['title'],
                description=opp['description'],
                category=opp.get('category', 'general'),
                priority=opp['priority'],
                potential_savings=opp.get('potential_savings', 0),
                action_items=opp.get('tips', []),
                metadata={'type': 'savings_opportunity', **{k: v for k, v in opp.items() 
                                                          if k not in ['title', 'description', 'category', 'priority', 'tips']}}
            ) for opp in savings_opportunities]
        )
        
        # Prioritize all suggestions
        prioritized_suggestions = self.prioritize_suggestions(all_suggestions)
        
        return SuggestionAgentOutput(
            suggestions=prioritized_suggestions,
            alerts=budget_alerts + subscription_alerts,
            savings_opportunities=savings_opportunities
        )
