"""Recommendation engine for generating financial suggestions"""

from typing import List, Dict, Any
from enum import Enum


class SuggestionType(str, Enum):
    """Types of financial suggestions"""
    BUDGET_ALERT = "budget_alert"
    SPENDING_REDUCTION = "spending_reduction"
    SUBSCRIPTION_ALERT = "subscription_alert"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    BUDGET_ADJUSTMENT = "budget_adjustment"


class SuggestionPriority(str, Enum):
    """Priority levels for suggestions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationEngine:
    """Engine for generating financial recommendations and suggestions"""

    def __init__(self):
        self.category_thresholds = {
            'food_dining': 500,
            'groceries': 400,
            'shopping': 300,
            'transportation': 200,
            'entertainment': 150
        }

    def generate_budget_alerts(self, insights: List[Dict[str, Any]], thresholds: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate budget alerts based on spending insights"""
        alerts = []

        for insight in insights:
            if insight.get('insight_type') == 'spike':
                category = insight.get('category')
                spike_amount = insight.get('metadata', {}).get('amount', 0)
                threshold = thresholds.get(category, 0)

                if spike_amount > threshold:
                    overspend_amount = spike_amount - threshold
                    overspend_percent = (overspend_amount / threshold * 100) if threshold > 0 else 0

                    alerts.append({
                        'type': SuggestionType.BUDGET_ALERT,
                        'category': category,
                        'title': f"Budget Alert: {category.replace('_', ' ').title()}",
                        'description': f"You've exceeded your {category} budget by ${overspend_amount:.2f} ({overspend_percent:.1f}%)",
                        'priority': SuggestionPriority.HIGH if overspend_percent > 50 else SuggestionPriority.MEDIUM,
                        'amount_exceeded': overspend_amount,
                        'percentage_exceeded': overspend_percent
                    })

        return alerts

    def generate_spending_reduction_suggestions(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate suggestions for reducing spending"""
        suggestions = []

        for insight in insights:
            metadata = insight.get('metadata', {})

            if insight.get('insight_type') == 'habit':
                if 'weekend' in insight.get('description', '').lower():
                    suggestions.append({
                        'type': SuggestionType.SPENDING_REDUCTION,
                        'title': "Reduce Weekend Spending",
                        'description': "Consider planning weekend activities with a budget to avoid overspending",
                        'priority': SuggestionPriority.MEDIUM,
                        'potential_savings': metadata.get('weekend', 0) * 0.2,  # Assume 20% reduction potential
                        'action_items': [
                            "Set a weekend spending limit",
                            "Plan free or low-cost activities",
                            "Cook at home instead of dining out"
                        ]
                    })

            elif insight.get('insight_type') == 'recurring':
                frequency = metadata.get('frequency_days', 0)
                amount = metadata.get('avg_amount', 0)

                if frequency <= 30 and amount > 5:  # Any recurring expense over $5
                    monthly_cost = amount * (30 / frequency) if frequency > 0 else 0
                    suggestions.append({
                        'type': SuggestionType.SPENDING_REDUCTION,
                        'title': f"Review Recurring Expense: {metadata.get('merchant', 'Unknown')}",
                        'description': f"This recurring expense costs ${monthly_cost:.2f}/month. Consider if it's necessary.",
                        'priority': SuggestionPriority.MEDIUM if amount > 20 else SuggestionPriority.LOW,
                        'potential_savings': monthly_cost * 0.5,  # Assume 50% could be saved if eliminated
                        'merchant': metadata.get('merchant'),
                        'monthly_cost': monthly_cost
                    })

        return suggestions

    def generate_subscription_alerts(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate alerts about subscription services"""
        alerts = []

        subscription_keywords = ['spotify', 'netflix', 'amazon prime', 'gym', 'subscription']

        for insight in insights:
            if insight.get('insight_type') == 'recurring':
                metadata = insight.get('metadata', {})
                merchant = metadata.get('merchant', '').lower()

                if any(keyword in merchant for keyword in subscription_keywords):
                    amount = metadata.get('avg_amount', 0)
                    frequency = metadata.get('frequency_days', 0)
                    annual_cost = amount * (365 / frequency) if frequency > 0 else 0

                    alerts.append({
                        'type': SuggestionType.SUBSCRIPTION_ALERT,
                        'title': f"Subscription Review: {metadata.get('merchant', 'Unknown')}",
                        'description': f"Annual cost: ${annual_cost:.2f}. Consider if you're getting value from this subscription.",
                        'priority': SuggestionPriority.LOW if annual_cost < 100 else SuggestionPriority.MEDIUM,
                        'merchant': metadata.get('merchant'),
                        'monthly_cost': amount * (30 / frequency) if frequency > 0 else 0,
                        'annual_cost': annual_cost,
                        'action_items': [
                            "Review usage frequency",
                            "Check for family/shared plans",
                            "Consider canceling if unused"
                        ]
                    })

        return alerts

    def generate_savings_opportunities(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential savings opportunities"""
        opportunities = []

        # Analyze spending patterns for savings opportunities
        category_spending = {}
        for insight in insights:
            if insight.get('insight_type') == 'spike':
                category = insight.get('category')
                amount = insight.get('metadata', {}).get('amount', 0)
                category_spending[category] = category_spending.get(category, 0) + amount

        # Generate savings opportunities based on high spending categories
        for category, amount in category_spending.items():
            if amount > 200:  # Significant spending
                savings_tips = self._get_category_savings_tips(category)

                opportunities.append({
                    'type': SuggestionType.SAVINGS_OPPORTUNITY,
                    'category': category,
                    'title': f"Save on {category.replace('_', ' ').title()}",
                    'description': f"You spent ${amount:.2f} on {category}. Here are ways to save:",
                    'priority': SuggestionPriority.LOW,
                    'potential_savings': amount * 0.15,  # Assume 15% savings potential
                    'tips': savings_tips,
                    'current_spending': amount
                })

        return opportunities

    def _get_category_savings_tips(self, category: str) -> List[str]:
        """Get category-specific savings tips"""
        tips_map = {
            'food_dining': [
                "Cook at home more often",
                "Use restaurant coupons and deals",
                "Consider lunch meal prep",
                "Limit expensive drinks and appetizers"
            ],
            'groceries': [
                "Make a shopping list and stick to it",
                "Buy generic brands",
                "Use store loyalty programs",
                "Shop sales and use coupons"
            ],
            'shopping': [
                "Wait 24 hours before non-essential purchases",
                "Compare prices online",
                "Look for discount codes",
                "Consider buying used or refurbished items"
            ],
            'transportation': [
                "Use public transportation",
                "Carpool when possible",
                "Combine errands into one trip",
                "Consider walking or biking for short distances"
            ],
            'entertainment': [
                "Look for free events in your area",
                "Use streaming services instead of movie theaters",
                "Take advantage of happy hour specials",
                "Host entertainment at home"
            ]
        }

        return tips_map.get(category, ["Look for discounts and deals", "Consider alternatives", "Budget carefully"])

    def generate_new_user_suggestions(self) -> List[Dict[str, Any]]:
        """
        No hardcoded suggestions for new users.
        Frontend will display appropriate onboarding message.
        Real suggestions will be generated after transactions are uploaded.
        """
        return []

    def prioritize_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort suggestions by priority and potential impact"""
        priority_order = {
            SuggestionPriority.CRITICAL: 4,
            SuggestionPriority.HIGH: 3,
            SuggestionPriority.MEDIUM: 2,
            SuggestionPriority.LOW: 1
        }

        def sort_key(suggestion):
            priority_score = priority_order.get(suggestion.get('priority'), 0)
            savings_score = suggestion.get('potential_savings', 0) / 100  # Normalize savings
            return (priority_score, savings_score)

        return sorted(suggestions, key=sort_key, reverse=True)

    def generate_budget_recommendations(self, insights: List[Dict[str, Any]], current_thresholds: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate budget adjustment recommendations"""
        recommendations = []

        # Analyze spending patterns to suggest budget adjustments
        category_actuals = {}
        for insight in insights:
            if insight.get('insight_type') == 'spike':
                category = insight.get('category')
                amount = insight.get('metadata', {}).get('amount', 0)
                category_actuals[category] = max(category_actuals.get(category, 0), amount)

        for category, actual_spending in category_actuals.items():
            current_budget = current_thresholds.get(category, 0)

            if actual_spending > current_budget * 1.2:  # Consistently over budget
                suggested_budget = actual_spending * 1.1  # 10% buffer

                recommendations.append({
                    'type': SuggestionType.BUDGET_ADJUSTMENT,
                    'category': category,
                    'title': f"Adjust {category.replace('_', ' ').title()} Budget",
                    'description': f"Consider increasing budget from ${current_budget} to ${suggested_budget:.2f}",
                    'priority': SuggestionPriority.MEDIUM,
                    'current_budget': current_budget,
                    'suggested_budget': suggested_budget,
                    'reason': "Consistently exceeding current budget"
                })

            elif actual_spending < current_budget * 0.7:  # Significantly under budget
                suggested_budget = actual_spending * 1.2  # 20% buffer

                recommendations.append({
                    'type': SuggestionType.BUDGET_ADJUSTMENT,
                    'category': category,
                    'title': f"Reduce {category.replace('_', ' ').title()} Budget",
                    'description': f"Consider reducing budget from ${current_budget} to ${suggested_budget:.2f}",
                    'priority': SuggestionPriority.LOW,
                    'current_budget': current_budget,
                    'suggested_budget': suggested_budget,
                    'reason': "Consistently under current budget"
                })

        # Handle income trend insights
        for insight in insights:
            if insight.get('insight_type') == 'trend':
                metadata = insight.get('metadata', {})
                trend_percentage = metadata.get('trend_percentage', 0)
                category = insight.get('category', 'income')

                if category == 'income' and trend_percentage < -20:  # Significant income decrease
                    recommendations.append({
                        'type': SuggestionType.BUDGET_ADJUSTMENT,
                        'category': 'overall',
                        'title': "Review Budget Due to Income Change",
                        'description': f"Your income has decreased by {abs(trend_percentage):.1f}%. Consider adjusting your overall budget.",
                        'priority': SuggestionPriority.HIGH,
                        'current_budget': 0,  # Not category-specific
                        'suggested_budget': 0,  # Not category-specific
                        'reason': f"Income decreased by {abs(trend_percentage):.1f}%"
                    })

        return recommendations
