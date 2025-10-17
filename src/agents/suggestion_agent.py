"""
Suggestion Agent - Agent 5
Role: Generate actionable financial recommendations based on pattern insights and user preferences
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
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
    budget_recommendations: List[Dict[str, Any]] = Field(description="Budget adjustment recommendations")
    spending_suggestions: List[Dict[str, Any]] = Field(description="Spending reduction suggestions")
    alerts: List[Dict[str, Any]] = Field(description="Budget alerts and warnings")
    savings_opportunities: List[Dict[str, Any]] = Field(description="Identified savings opportunities")
    confidence_score: float = Field(description="Confidence score for suggestions (0-1)")


class SuggestionAgent:
    """
    Agent 5: Suggestion Agent

    Responsibilities:
    - Generate personalized actionable financial recommendations based on pattern analysis
    - Compare spending against budget thresholds
    - Suggest areas for spending reduction and optimization
    - Alert users about high recurring subscriptions and anomalies
    - Recommend budget threshold adjustments
    - Identify savings opportunities and windfalls
    - Produce Pydantic Suggestion objects for frontend consumption
    - Generate personalized suggestions for ALL users regardless of transaction count

    Integration pattern:
    - Used by suggestion_node in workflow pipeline
    - Takes pattern insights from PatternAnalyzerAgent as input
    - Outputs suggestions stored in prediction_results for frontend access
    - Works with both bulk CSV uploads and conversational chat inputs
    """

    def __init__(self, config: Dict[str, Any] = None, transaction_service=None):
        self.config = config or {}
        self.recommendation_engine = RecommendationEngine()
        self.transaction_service = transaction_service

    async def _get_user_spending_profile(self, user_id: str, user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Retrieve user's spending profile from database for personalized suggestions

        Returns enriched spending profile with transaction count, categories, and financial metrics
        """
        # ALWAYS try database first if transaction_service is available
        if self.transaction_service:
            try:
                spending_profile = await self.transaction_service.get_user_spending_profile(user_id)
                transaction_count = spending_profile.get("total_transactions", 0)
                print(f"AGENT: ✅ Retrieved user profile from DB - Total transactions: {transaction_count}")
                return {
                    "transaction_count": transaction_count,
                    "spending_profile": spending_profile
                }
            except Exception as e:
                print(f"AGENT: ⚠️ Error checking user profile from database: {e}")
                # Fall through to use user_preferences as fallback

        # Fallback: Use user_preferences if database query failed or no transaction_service
        if user_preferences:
            transaction_count = user_preferences.get('transaction_count', 0)
            print(f"AGENT: Using fallback transaction_count from user_preferences: {transaction_count}")
            return {
                "transaction_count": transaction_count,
                "spending_profile": user_preferences
            }

        # Last resort: No data available - use empty profile
        print(f"AGENT: ⚠️ No transaction data available, using empty profile")
        return {"transaction_count": 0, "spending_profile": {}}

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



    def _generate_personalized_suggestions(self, user_preferences: Dict[str, Any], transaction_count: int) -> List[Suggestion]:
        """Generate personalized suggestions for all users based on their spending profile and transaction data"""
        suggestions = []

        # Get user spending categories and monthly spending
        spending_categories = user_preferences.get('spending_categories', [])
        avg_monthly_spending = user_preferences.get('avg_monthly_spending', 0)
        total_income = user_preferences.get('total_income', 0)
        total_spending = user_preferences.get('total_spending', 0)

        # Get category-level spending data for calculating actual savings
        recent_summary = user_preferences.get('recent_summary', {})
        category_spending = recent_summary.get('categories', {}) if recent_summary else {}

        print(f"SUGGESTION: Generating personalized suggestions - Categories: {spending_categories}, Monthly: ${avg_monthly_spending:.2f}, Category Spending: {len(category_spending)} categories")

        # Category-specific suggestions based on actual spending
        # Check for various forms of dining/food categories and calculate actual savings
        dining_categories = ['food_dining', 'dining', 'food', 'restaurants', 'restaurant']
        dining_spending = 0
        for cat_name, cat_data in category_spending.items():
            if any(dining_cat.lower() in cat_name.lower() for dining_cat in dining_categories):
                dining_spending += abs(cat_data.get('total', 0))

        if any(cat.lower() in [sc.lower() for sc in spending_categories] for cat in dining_categories):
            # Calculate potential savings: 20-30% reduction in dining expenses
            potential_dining_savings = (dining_spending * 0.25) / 3 if dining_spending > 0 else 200.0  # Monthly average
            suggestions.append(Suggestion(
                suggestion_type='spending_optimization',
                title='Optimize Your Dining Expenses',
                description=f'Based on your transaction history, you have recurring dining expenses{f" totaling ${dining_spending:.2f}" if dining_spending > 0 else ""}. Consider meal planning or cooking at home more often to reduce costs by 20-30%.',
                category='food_dining',
                priority='medium',
                potential_savings=potential_dining_savings,
                action_required=True,
                implementation_difficulty='medium',
                metadata={
                    'personalized': True,
                    'based_on': 'dining_history',
                    'current_spending': dining_spending,
                    'reduction_percentage': 25
                }
            ))

        shopping_categories = ['shopping', 'retail', 'clothes', 'electronics']
        shopping_spending = 0
        for cat_name, cat_data in category_spending.items():
            if any(shop_cat.lower() in cat_name.lower() for shop_cat in shopping_categories):
                shopping_spending += abs(cat_data.get('total', 0))

        if any(cat.lower() in [sc.lower() for sc in spending_categories] for cat in shopping_categories):
            # Calculate potential savings: 15-20% reduction
            potential_shopping_savings = (shopping_spending * 0.175) / 3 if shopping_spending > 0 else 150.0
            suggestions.append(Suggestion(
                suggestion_type='spending_reduction',
                title='Review Your Shopping Habits',
                description=f'You have regular shopping expenses{f" totaling ${shopping_spending:.2f}" if shopping_spending > 0 else ""}. Try the 30-day rule: wait 30 days before making non-essential purchases to reduce impulse buying by 15-20%.',
                category='shopping',
                priority='medium',
                potential_savings=potential_shopping_savings,
                action_required=True,
                implementation_difficulty='easy',
                metadata={
                    'personalized': True,
                    'based_on': 'shopping_history',
                    'current_spending': shopping_spending,
                    'reduction_percentage': 17.5
                }
            ))

        entertainment_categories = ['entertainment', 'subscriptions', 'streaming', 'movies']
        entertainment_spending = 0
        for cat_name, cat_data in category_spending.items():
            if any(ent_cat.lower() in cat_name.lower() for ent_cat in entertainment_categories):
                entertainment_spending += abs(cat_data.get('total', 0))

        if any(cat.lower() in [sc.lower() for sc in spending_categories] for cat in entertainment_categories):
            # Calculate potential savings: 30-40% reduction by canceling unused subscriptions
            potential_entertainment_savings = (entertainment_spending * 0.35) / 3 if entertainment_spending > 0 else 250.0
            suggestions.append(Suggestion(
                suggestion_type='subscription_review',
                title='Audit Your Subscriptions',
                description=f'Review your entertainment and subscription services{f" (currently ${entertainment_spending:.2f})" if entertainment_spending > 0 else ""}. Cancel unused subscriptions to save 30-40% monthly.',
                category='entertainment',
                priority='high',
                potential_savings=potential_entertainment_savings,
                action_required=True,
                implementation_difficulty='easy',
                metadata={
                    'personalized': True,
                    'based_on': 'subscription_analysis',
                    'current_spending': entertainment_spending,
                    'reduction_percentage': 35
                }
            ))

        # Spending level-based suggestions with calculated savings
        if avg_monthly_spending > 3000:
            # High spender: potential 10-15% reduction
            potential_budget_savings = avg_monthly_spending * 0.125
            suggestions.append(Suggestion(
                suggestion_type='budget_review',
                title='High Spending Alert - Review Your Budget',
                description=f'With ${avg_monthly_spending:.2f} monthly spending, consider reviewing budget allocations for better control. A 10-15% reduction could save you ${potential_budget_savings:.2f} monthly.',
                category='budgeting',
                priority='high',
                potential_savings=potential_budget_savings,
                action_required=True,
                implementation_difficulty='medium',
                metadata={
                    'personalized': True,
                    'based_on': 'spending_level',
                    'monthly_spending': avg_monthly_spending,
                    'target_reduction_percentage': 12.5
                }
            ))
        elif avg_monthly_spending > 2000:
            # Moderate spender: potential 8-12% reduction
            potential_budget_savings = avg_monthly_spending * 0.10
            suggestions.append(Suggestion(
                suggestion_type='budget_optimization',
                title='Optimize Your Budget Allocation',
                description=f'Your monthly spending is ${avg_monthly_spending:.2f}. Fine-tune your budget categories to maximize savings potential. Target a 10% reduction to save ${potential_budget_savings:.2f} monthly.',
                category='budgeting',
                priority='medium',
                potential_savings=potential_budget_savings,
                action_required=True,
                implementation_difficulty='medium',
                metadata={
                    'personalized': True,
                    'based_on': 'spending_level',
                    'monthly_spending': avg_monthly_spending,
                    'target_reduction_percentage': 10
                }
            ))

        # Income vs Spending analysis
        if total_income > 0 and total_spending > 0:
            savings_rate = ((total_income - total_spending) / total_income) * 100 if total_income > total_spending else 0
            if savings_rate < 10:
                suggestions.append(Suggestion(
                    suggestion_type='savings_increase',
                    title='Increase Your Savings Rate',
                    description=f'Your current savings rate is {savings_rate:.1f}%. Aim for at least 20% of your income to build financial security.',
                    category='savings',
                    priority='high',
                    potential_savings=total_income * 0.1,  # Suggest saving 10% more
                    action_required=True,
                    implementation_difficulty='medium',
                    metadata={'personalized': True, 'current_savings_rate': savings_rate, 'target_rate': 20}
                ))

        # Always include foundational personalized suggestions
        # Adapt messaging based on transaction volume
        if transaction_count > 0:
            suggestions.extend([
                Suggestion(
                    suggestion_type='spending_analysis',
                    title='Analyze Your Spending Patterns',
                    description=f'Based on your {transaction_count} transaction(s), identify your spending habits and discover opportunities for optimization.',
                    category='analytics',
                    priority='high',
                    potential_savings=200.0,
                    action_required=True,
                    implementation_difficulty='easy',
                    metadata={'personalized': True, 'based_on': 'transaction_volume', 'transaction_count': transaction_count}
                ),
                Suggestion(
                    suggestion_type='goal_setting',
                    title='Set Specific Financial Goals',
                    description='Define clear, actionable financial goals tailored to your spending history. Use the SMART framework: Specific, Measurable, Achievable, Relevant, Time-bound.',
                    category='planning',
                    priority='medium',
                    potential_savings=500.0,
                    action_required=True,
                    implementation_difficulty='medium',
                    metadata={'personalized': True, 'based_on': 'user_profile'}
                )
            ])

        # Add category analysis if we haven't found specific patterns yet
        if len(suggestions) <= 2 and spending_categories:
            suggestions.insert(0, Suggestion(
                suggestion_type='category_analysis',
                title='Review Your Spending Categories',
                description=f'You have transactions in {len(spending_categories)} categories. Dive deeper into each to find optimization opportunities.',
                category='analytics',
                priority='high',
                potential_savings=350.0,
                action_required=True,
                implementation_difficulty='easy',
                metadata={'personalized': True, 'based_on': 'category_data', 'categories': spending_categories}
            ))

        # Ensure we always have at least one suggestion
        if not suggestions:
            suggestions.append(Suggestion(
                suggestion_type='financial_overview',
                title='Get Your Financial Overview',
                description='Start by understanding your income and expenses. Track all transactions consistently to build a comprehensive financial picture.',
                category='getting_started',
                priority='high',
                potential_savings=0.0,
                action_required=True,
                implementation_difficulty='easy',
                metadata={'personalized': True, 'based_on': 'initial_setup'}
            ))

        return suggestions

    async def process(self, input_data: SuggestionAgentInput) -> SuggestionAgentOutput:
        """
        Main processing method for the Suggestion Agent

        Flow Logic:
        1. Retrieve user's spending profile from database
        2. Generate personalized suggestions based on spending patterns and insights
        3. Works for ALL users regardless of transaction count
        4. Adapts to both bulk uploads (CSV) and conversational chat inputs
        """
        print(f"SUGGESTION: Received {len(input_data.pattern_insights)} pattern insights")
        for i, insight in enumerate(input_data.pattern_insights[:3]):  # Log first 3 insights
            print(f"  Insight {i}: type={insight.insight_type}, desc={insight.description[:50]}...")

        # Get user spending profile from database
        user_profile = await self._get_user_spending_profile(input_data.user_id, input_data.user_preferences)
        actual_transaction_count = user_profile["transaction_count"]

        print(f"SUGGESTION: User {input_data.user_id} - Transaction count: {actual_transaction_count} - generating personalized suggestions")

        # Look for meaningful spending patterns
        # Updated to recognize actual pattern types from pattern analyzer agent
        meaningful_patterns = [
            insight for insight in input_data.pattern_insights
            if insight.insight_type in [
                # Original expected types
                'spike', 'trend', 'category_shift', 'seasonal', 'recurring',
                'budget_alert', 'spending_pattern', 'anomaly',
                # Actual types from pattern analyzer agent
                'category_trend',  # Category-specific spending trends
                'income_trend',    # Income trend analysis
                'expense_trend',   # Expense trend analysis
                'monthly_pattern', # Monthly spending patterns
                'weekly_pattern',  # Weekly spending patterns
                'seasonal_pattern' # Seasonal variations
            ]
        ]

        print(f"SUGGESTION: Found {len(meaningful_patterns)} meaningful patterns from {len(input_data.pattern_insights)} total insights")

        # Use spending profile data from database for personalized suggestions
        spending_profile = user_profile.get("spending_profile", {})
        recent_summary = spending_profile.get("recent_summary", {})

        # Extract spending categories from multiple sources
        spending_categories = []
        total_spending = 0
        total_income = 0

        # 1. Extract from pattern insights (primary source)
        for insight in input_data.pattern_insights:
            if insight.category and insight.category not in spending_categories:
                spending_categories.append(insight.category)

        # 2. Extract from recent summary (secondary source)
        if recent_summary:
            # Get categories and separate income/expenses
            categories = recent_summary.get("categories", {})
            for category, stats in categories.items():
                category_total = stats.get("total", 0)
                if category_total < 0:  # Negative = expense
                    if category not in spending_categories:
                        spending_categories.append(category)
                    total_spending += abs(category_total)
                elif category_total > 0:  # Positive = income
                    total_income += category_total

            # If no categories found, check recent transactions for spending patterns
            if not spending_categories:
                recent_transactions = spending_profile.get("recent_transactions", [])
                transaction_categories = set()
                for tx in recent_transactions:
                    if tx.get("amount", 0) < 0:  # Expense
                        category = tx.get("category", "miscellaneous")
                        transaction_categories.add(category)
                spending_categories = list(transaction_categories)

        # Calculate average monthly spending (assuming 3 months of data)
        avg_monthly_spending = total_spending / 3 if total_spending > 0 else 0

        # Create enriched user preferences for personalized suggestions
        enriched_preferences = {
            **input_data.user_preferences,
            "spending_categories": spending_categories,
            "avg_monthly_spending": avg_monthly_spending,
            "total_income": total_income,
            "total_spending": total_spending
        }

        # Generate personalized suggestions for all users
        personalized_suggestions = self._generate_personalized_suggestions(
            enriched_preferences,
            actual_transaction_count
        )

        # If we have meaningful patterns, generate additional pattern-based suggestions
        if len(meaningful_patterns) > 0:
            print(f"SUGGESTION: Generating pattern-based suggestions from {len(meaningful_patterns)} patterns")

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

            print(f"SUGGESTION: Pattern-based - alerts: {len(budget_alerts)}, spending: {len(spending_suggestions)}, subscriptions: {len(subscription_alerts)}, budget: {len(budget_suggestions)}, savings: {len(savings_opportunities)}")

            # Combine pattern-based suggestions with personalized ones
            pattern_based_suggestions = (
                [Suggestion(
                    suggestion_type=alert.get('type', 'budget_alert'),
                    title=alert['title'],
                    description=alert['description'],
                    category=alert.get('category', 'general'),
                    priority=alert['priority'],
                    potential_savings=alert.get('amount_exceeded', 0),
                    action_required=True,
                    implementation_difficulty='medium',
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
                    implementation_difficulty='easy',
                    metadata={'type': 'savings_opportunity', **{k: v for k, v in opp.items()
                                                              if k not in ['title', 'description', 'category', 'priority', 'tips']}}
                ) for opp in savings_opportunities]
            )

            # Merge with personalized suggestions
            all_suggestions = personalized_suggestions + pattern_based_suggestions

            # Prioritize combined suggestions
            prioritized_suggestions = self.prioritize_suggestions(all_suggestions)

            # Calculate total potential monthly savings
            total_potential_savings = sum(s.potential_savings for s in prioritized_suggestions)

            print(f"SUGGESTION: Total potential monthly savings from {len(prioritized_suggestions)} suggestions: ${total_potential_savings:.2f}")

            return SuggestionAgentOutput(
                suggestions=prioritized_suggestions,
                budget_recommendations=[{
                    'title': s.title,
                    'description': s.description,
                    'category': s.category,
                    'priority': s.priority,
                    'potential_savings': s.potential_savings,
                    'potential_monthly_savings': s.potential_savings,  # Add this field
                    'metadata': s.metadata
                } for s in budget_suggestions],
                spending_suggestions=[{
                    **s.dict(),
                    'potential_monthly_savings': s.potential_savings  # Add this field
                } for s in spending_suggestions],
                alerts=budget_alerts + subscription_alerts,
                savings_opportunities=[{
                    **opp,
                    'potential_monthly_savings': opp.get('potential_savings', 0)  # Add this field
                } for opp in savings_opportunities],
                confidence_score=0.85  # High confidence with patterns
            )

        # No patterns available but user has enough transactions - use profile-based suggestions
        print(f"SUGGESTION: No patterns, using profile-based suggestions only")

        # Generate budget recommendations from personalized suggestions
        budget_recs = [
            {
                'title': s.title,
                'description': s.description,
                'category': s.category,
                'priority': s.priority,
                'potential_savings': s.potential_savings,
                'potential_monthly_savings': s.potential_savings,  # Add monthly savings field
                'metadata': s.metadata
            }
            for s in personalized_suggestions
            if 'budget' in s.suggestion_type.lower() or 'budget' in s.title.lower()
        ]

        # Generate spending suggestions (non-budget ones)
        spending_suggs = [
            {
                **s.dict(),
                'potential_monthly_savings': s.potential_savings  # Add monthly savings field
            }
            for s in personalized_suggestions
            if 'budget' not in s.suggestion_type.lower() and 'budget' not in s.title.lower()
        ]

        # Create savings opportunities from all suggestions with potential savings
        savings_opps = [
            {
                'type': s.suggestion_type,
                'title': s.title,
                'description': s.description,
                'category': s.category,
                'priority': s.priority,
                'potential_savings': s.potential_savings,
                'potential_monthly_savings': s.potential_savings,  # Add monthly savings field
                'tips': [
                    f"Reduce {s.metadata.get('current_spending', 'spending')} by {s.metadata.get('reduction_percentage', 10)}%",
                    "Track progress weekly",
                    "Set specific monthly targets"
                ] if s.potential_savings > 0 else ["Track your spending regularly"]
            }
            for s in personalized_suggestions
            if s.potential_savings > 0
        ]

        # Calculate total potential monthly savings
        total_potential_savings = sum(s.potential_savings for s in personalized_suggestions)

        print(f"SUGGESTION: Generated {len(budget_recs)} budget recommendations, {len(spending_suggs)} spending suggestions, {len(savings_opps)} savings opportunities")
        print(f"SUGGESTION: Total potential monthly savings: ${total_potential_savings:.2f}")

        return SuggestionAgentOutput(
            suggestions=personalized_suggestions,
            alerts=[{
                'type': 'profile_based',
                'title': 'Personalized Financial Recommendations',
                'description': f'Based on your spending profile, you could potentially save ${total_potential_savings:.2f} monthly by implementing these suggestions.',
                'priority': 'medium',
                'category': 'personalized'
            }],
            savings_opportunities=savings_opps,
            budget_recommendations=budget_recs,
            spending_suggestions=spending_suggs,
            confidence_score=0.75  # Medium-high confidence with profile data
        )
