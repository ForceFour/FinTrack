"""
Suggestion Agent - Agent 5
Role: Generate actionable financial recommendations
"""

from typing import Dict, Any, List, Optional
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
    user_id: str = Field(description="User ID for database queries")


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

    def __init__(self, config: Dict[str, Any] = None, transaction_service=None):
        self.config = config or {}
        self.recommendation_engine = RecommendationEngine()
        self.transaction_service = transaction_service

    async def _check_user_profile_from_db(self, user_id: str) -> Dict[str, Any]:
        """Check user's actual transaction history from database"""
        if not self.transaction_service:
            # Fallback to default behavior if no transaction service available
            return {"is_new_user": True, "transaction_count": 0, "spending_profile": {}}

        try:
            spending_profile = await self.transaction_service.get_user_spending_profile(user_id)
            transaction_count = spending_profile.get("total_transactions", 0)

            # User is considered "new" if they have fewer than 10 transactions
            # This gives us enough data to provide meaningful personalized suggestions
            is_new_user = transaction_count < 10

            return {
                "is_new_user": is_new_user,
                "transaction_count": transaction_count,
                "spending_profile": spending_profile
            }
        except Exception as e:
            print(f"Error checking user profile from database: {e}")
            return {"is_new_user": True, "transaction_count": 0, "spending_profile": {}}

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
                suggestion_type=sugg.get('type', 'spending_reduction'),
                title=sugg['title'],
                description=sugg['description'],
                category=sugg.get('category', 'general'),
                priority=sugg['priority'],
                potential_savings=sugg.get('potential_savings', 0),
                action_required=True,
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
                suggestion_type=rec.get('type', 'budget_adjustment'),
                title=rec['title'],
                description=rec['description'],
                category=rec['category'],
                priority=rec['priority'],
                potential_savings=0,  # Budget adjustments don't have direct savings
                action_required=True,
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
                'action_items': [],  # Default empty list since it's not in schema
                **sugg.metadata
            }
            for sugg in suggestions
        ]

        # Get prioritized suggestions
        prioritized_dicts = self.recommendation_engine.prioritize_suggestions(suggestion_dicts)

        # Convert back to Suggestion objects while maintaining the new order
        return [
            Suggestion(
                suggestion_type=sugg.get('type', 'general'),
                title=sugg['title'],
                description=sugg['description'],
                category=sugg.get('category', 'general'),
                priority=sugg['priority'],
                potential_savings=sugg.get('potential_savings', 0),
                action_required=True,
                metadata={k: v for k, v in sugg.items() if k not in
                         ['title', 'description', 'category', 'priority', 'potential_savings', 'action_items']}
            )
            for sugg in prioritized_dicts
        ]

    def _generate_personalized_suggestions_for_existing_user(self, user_preferences: Dict[str, Any]) -> List[Suggestion]:
        """Generate personalized suggestions for existing users based on their profile"""
        suggestions = []

        # Get user spending categories and monthly spending
        spending_categories = user_preferences.get('spending_categories', [])
        avg_monthly_spending = user_preferences.get('avg_monthly_spending', 0)

        # Personalized suggestions based on spending profile
        if 'food_dining' in spending_categories:
            suggestions.append(Suggestion(
                suggestion_type='spending_optimization',
                title='Optimize Your Dining Expenses',
                description=f'Consider meal planning or cooking at home more often to reduce dining costs.',
                category='food_dining',
                priority='medium',
                potential_savings=200.0,
                action_required=True,
                metadata={'personalized': True, 'based_on': 'dining_history'}
            ))

        if avg_monthly_spending > 2000:
            suggestions.append(Suggestion(
                suggestion_type='budget_review',
                title='Review Your Budget Categories',
                description=f'With ${avg_monthly_spending} monthly spending, consider reviewing budget allocations for better control.',
                category='budgeting',
                priority='high',
                potential_savings=300.0,
                action_required=True,
                metadata={'personalized': True, 'based_on': 'spending_level'}
            ))

        # Always include these for existing users
        suggestions.extend([
            Suggestion(
                suggestion_type='spending_analysis',
                title='Analyze Your Spending Trends',
                description='Review your transaction history to identify areas for improvement.',
                category='analytics',
                priority='medium',
                potential_savings=150.0,
                action_required=True,
                metadata={'personalized': True, 'based_on': 'existing_user_status'}
            ),
            Suggestion(
                suggestion_type='goal_setting',
                title='Set Financial Goals',
                description='Based on your spending history, set specific savings or debt reduction goals.',
                category='planning',
                priority='medium',
                potential_savings=400.0,
                action_required=True,
                metadata={'personalized': True, 'based_on': 'user_profile'}
            )
        ])

        return suggestions

    async def process(self, input_data: SuggestionAgentInput) -> SuggestionAgentOutput:
        """Main processing method for the Suggestion Agent"""
        # Check user profile from database for accurate transaction history
        user_profile = await self._check_user_profile_from_db(input_data.user_id)

        # Check if this is a new user scenario based on actual database transaction count
        # Look for actual spending patterns, not just generic insights
        meaningful_patterns = [
            insight for insight in input_data.pattern_insights
            if insight.insight_type in [
                'spike', 'trend', 'category_shift', 'seasonal', 'recurring',
                'budget_alert', 'spending_pattern', 'anomaly'
            ]
        ]

        # Use database transaction count as primary indicator
        is_new_user = user_profile["is_new_user"]
        actual_transaction_count = user_profile["transaction_count"]

        print(f"SUGGESTION: User {input_data.user_id} - Transaction count: {actual_transaction_count}, Is new user: {is_new_user}")

        if is_new_user:
            # New user scenario - return empty suggestions
            # Frontend will display appropriate onboarding message
            return SuggestionAgentOutput(
                suggestions=[],
                alerts=[],
                savings_opportunities=[]
            )

        # Existing user - generate personalized suggestions based on their profile and patterns
        # Even without current patterns, we can provide personalized advice based on user preferences

        # If no patterns available, generate suggestions based on user profile
        if len(meaningful_patterns) == 0:
            # Generate personalized suggestions for existing users without current patterns
            personalized_suggestions = self._generate_personalized_suggestions_for_existing_user(input_data.user_preferences)

            # Convert suggestions to dict format for savings_opportunities
            savings_opps = [sugg.dict() for sugg in personalized_suggestions[-2:]] if len(personalized_suggestions) >= 2 else [sugg.dict() for sugg in personalized_suggestions]

            return SuggestionAgentOutput(
                suggestions=personalized_suggestions,
                alerts=[{
                    'type': 'profile_based',
                    'title': 'Personalized Recommendations',
                    'description': 'Based on your spending profile, here are some targeted suggestions.',
                    'priority': 'medium',
                    'category': 'personalized'
                }],
                savings_opportunities=savings_opps
            )

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
                suggestion_type=alert.get('type', 'budget_alert'),
                title=alert['title'],
                description=alert['description'],
                category=alert.get('category', 'general'),
                priority=alert['priority'],
                potential_savings=alert.get('amount_exceeded', 0),
                action_required=True,
                metadata={'type': 'budget_alert', **{k: v for k, v in alert.items()
                                                   if k not in ['title', 'description', 'category', 'priority']}}
            ) for alert in budget_alerts]
            + spending_suggestions
            + budget_suggestions
            + [Suggestion(
                suggestion_type=opp.get('type', 'savings_opportunity'),
                title=opp['title'],
                description=opp['description'],
                category=opp.get('category', 'general'),
                priority=opp['priority'],
                potential_savings=opp.get('potential_savings', 0),
                action_required=True,
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
