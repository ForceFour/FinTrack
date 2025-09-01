"""
Suggestion Service - AI-powered financial recommendations
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from ..models.suggestion import (
    Suggestion, BudgetRecommendation, SavingsOpportunity, GoalRecommendation,
    MerchantAlternative, SpendingOptimization, PersonalizedSuggestion,
    SuggestionType, SuggestionPriority, SuggestionStatus, SuggestionCreate,
    ActionableInsight, SuggestionBatch
)
from ..agents.suggestion_agent import SuggestionAgent, SuggestionAgentInput
from ..schemas.transaction_schemas import PatternInsight
from ..utils.recommendation_engine import RecommendationEngine

class SuggestionService:
    """Service for generating and managing financial suggestions"""
    
    def __init__(self, db):
        self.db = db
        self.suggestion_agent = SuggestionAgent()
        self.recommendation_engine = RecommendationEngine()

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from database"""
        preferences = await self.db.users.find_one(
            {"_id": user_id},
            {"preferences": 1}
        )
        return preferences.get("preferences", {}) if preferences else {}

    async def get_user_transactions(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get user transactions from database"""
        start_date = datetime.now() - timedelta(days=days)
        transactions = await self.db.transactions.find(
            {
                "user_id": user_id,
                "date": {"$gte": start_date}
            }
        ).to_list(None)
        return transactions

    async def get_suggestions(self, user_id: str, suggestion_type: str = None, limit: int = 10) -> List[Suggestion]:
        """Get suggestions for a user"""
        query = {"user_id": user_id, "status": SuggestionStatus.ACTIVE}
        if suggestion_type:
            query["type"] = suggestion_type

        suggestions = await self.db.suggestions.find(query).limit(limit).to_list(None)
        return [Suggestion(**sugg) for sugg in suggestions]

    async def generate_budget_recommendations(self, user_id: str, income_data: Dict[str, Any]) -> BudgetRecommendation:
        """Generate budget recommendations based on income and spending patterns"""
        transactions = await self.get_user_transactions(user_id)
        preferences = await self.get_user_preferences(user_id)

        # Calculate current spending by category
        current_spending = {}
        for txn in transactions:
            category = txn.get("category", "other")
            amount = Decimal(str(txn.get("amount", 0)))
            if amount < 0:  # Only consider expenses
                current_spending[category] = current_spending.get(category, Decimal(0)) - amount

        # Generate recommended budget
        monthly_income = Decimal(str(income_data["monthly_income"]))
        recommended_budget = {}
        adjustments = []

        # Default budget allocation percentages
        default_allocations = {
            "housing": Decimal("0.30"),
            "food": Decimal("0.15"),
            "transportation": Decimal("0.10"),
            "utilities": Decimal("0.10"),
            "savings": Decimal("0.20"),
            "entertainment": Decimal("0.05"),
            "healthcare": Decimal("0.05"),
            "miscellaneous": Decimal("0.05")
        }

        # Adjust based on user's actual spending patterns
        for category, allocation in default_allocations.items():
            recommended_amount = monthly_income * allocation
            current_amount = current_spending.get(category, Decimal(0))
            
            recommended_budget[category] = recommended_amount
            
            if current_amount > recommended_amount:
                adjustments.append({
                    "category": category,
                    "current_amount": current_amount,
                    "recommended_amount": recommended_amount,
                    "difference": current_amount - recommended_amount,
                    "type": "reduction",
                    "priority": "high" if (current_amount / recommended_amount) > Decimal("1.5") else "medium"
                })

        # Calculate potential savings
        total_current_spending = sum(current_spending.values())
        recommended_total = sum(recommended_budget.values())
        savings_potential = max(Decimal(0), total_current_spending - recommended_total)

        return BudgetRecommendation(
            monthly_income=monthly_income,
            recommended_budget=recommended_budget,
            current_spending=current_spending,
            adjustments=adjustments,
            savings_potential=savings_potential,
            confidence_score=0.85
        )

    async def identify_savings_opportunities(self, user_id: str, analysis_data: Dict[str, Any]) -> List[SavingsOpportunity]:
        """Identify savings opportunities from spending patterns"""
        transactions = await self.get_user_transactions(user_id)
        pattern_insights = [PatternInsight(**insight) for insight in analysis_data.get("insights", [])]

        # Get suggestions from agent
        agent_input = SuggestionAgentInput(
            pattern_insights=pattern_insights,
            budget_thresholds=analysis_data.get("thresholds", {}),
            user_preferences=await self.get_user_preferences(user_id)
        )
        agent_output = self.suggestion_agent.process(agent_input)

        # Convert agent suggestions to SavingsOpportunity objects
        opportunities = []
        for suggestion in agent_output.suggestions:
            if suggestion.potential_savings and suggestion.potential_savings > 0:
                opp = SavingsOpportunity(
                    opportunity_type="reduce_spending",
                    title=suggestion.title,
                    description=suggestion.description,
                    current_spending=Decimal(str(suggestion.metadata.get("current_spending", 0))),
                    potential_savings=Decimal(str(suggestion.potential_savings)),
                    savings_percentage=float(suggestion.potential_savings / suggestion.metadata.get("current_spending", 1) * 100),
                    difficulty=suggestion.metadata.get("difficulty", "medium"),
                    timeframe="short_term",
                    action_steps=suggestion.action_items,
                    confidence=0.85
                )
                opportunities.append(opp)

        return opportunities

    async def get_spending_optimization(self, user_id: str, category: str = None) -> SpendingOptimization:
        """Get spending optimization suggestions"""
        transactions = await self.get_user_transactions(user_id)
        
        # Filter by category if specified
        if category:
            transactions = [t for t in transactions if t.get("category") == category]

        # Calculate current spending
        current_spending = sum(Decimal(str(t["amount"])) for t in transactions if t["amount"] < 0)
        
        # Get optimization strategies from recommendation engine
        strategies = self.recommendation_engine.generate_spending_reduction_suggestions(transactions)
        
        return SpendingOptimization(
            category=category or "all",
            current_spending=abs(current_spending),
            optimal_spending=abs(current_spending) * Decimal("0.8"),  # Target 20% reduction
            optimization_strategies=strategies,
            impact_assessment={
                "savings_potential": str(abs(current_spending) * Decimal("0.2")),
                "difficulty": "medium",
                "timeline": "1-2 months"
            },
            priority_score=0.75
        )

    async def generate_goal_recommendations(self, user_id: str, goal_data: Dict[str, Any]) -> GoalRecommendation:
        """Generate personalized financial goal recommendations"""
        preferences = await self.get_user_preferences(user_id)
        transactions = await self.get_user_transactions(user_id, days=90)  # Get 3 months of data

        # Calculate monthly savings capacity
        monthly_income = sum(Decimal(str(t["amount"])) for t in transactions if t["amount"] > 0) / 3
        monthly_expenses = sum(Decimal(str(t["amount"])) for t in transactions if t["amount"] < 0) / 3
        savings_capacity = monthly_income + monthly_expenses  # expenses are negative

        target_amount = Decimal(str(goal_data.get("target_amount", 0)))
        current_progress = Decimal(str(goal_data.get("current_progress", 0)))
        
        # Calculate recommended monthly amount
        months_to_goal = int(goal_data.get("timeframe_months", 12))
        required_monthly = (target_amount - current_progress) / months_to_goal

        # Determine feasibility and adjustments
        adjustments_needed = []
        if required_monthly > savings_capacity:
            adjustments_needed.append({
                "type": "increase_savings",
                "amount": required_monthly - savings_capacity,
                "suggestion": "Reduce discretionary spending to meet goal"
            })

        return GoalRecommendation(
            goal_type=goal_data["goal_type"],
            target_amount=target_amount,
            recommended_monthly_amount=required_monthly,
            timeframe_months=months_to_goal,
            current_progress=current_progress,
            adjustments_needed=adjustments_needed,
            success_probability=min(1.0, float(savings_capacity / required_monthly)) if required_monthly > 0 else 1.0,
            alternative_strategies=[
                {
                    "strategy": "Extend timeline",
                    "new_monthly_amount": (target_amount - current_progress) / (months_to_goal * 1.5),
                    "new_timeframe": int(months_to_goal * 1.5)
                },
                {
                    "strategy": "Adjust target",
                    "new_target": target_amount * Decimal("0.8"),
                    "new_monthly_amount": (target_amount * Decimal("0.8") - current_progress) / months_to_goal
                }
            ]
        )

    async def find_merchant_alternatives(self, user_id: str, merchant: str, category: str = None) -> List[MerchantAlternative]:
        """Find alternative merchants with potential savings"""
        transactions = await self.get_user_transactions(user_id)
        
        # Get transactions for the specific merchant
        merchant_transactions = [t for t in transactions if t.get("merchant") == merchant]
        if not merchant_transactions:
            return []

        # Calculate average transaction amount
        avg_amount = sum(Decimal(str(t["amount"])) for t in merchant_transactions) / len(merchant_transactions)
        
        # Get alternatives from recommendation engine
        alternatives = self.recommendation_engine.generate_merchant_alternatives(
            merchant, category, abs(avg_amount)
        )
        
        return [MerchantAlternative(**alt) for alt in alternatives]

    async def generate_personalized_suggestions(self, user_id: str, preferences: Dict[str, Any]) -> PersonalizedSuggestion:
        """Generate personalized suggestions based on user preferences"""
        transactions = await self.get_user_transactions(user_id)
        pattern_insights = []  # Get from pattern analysis service
        
        # Get suggestions from agent
        agent_input = SuggestionAgentInput(
            pattern_insights=pattern_insights,
            budget_thresholds=preferences.get("budget_thresholds", {}),
            user_preferences=preferences
        )
        agent_output = self.suggestion_agent.process(agent_input)
        
        return PersonalizedSuggestion(
            user_id=user_id,
            personalization_factors=list(preferences.keys()),
            suggestions=[Suggestion(**s.dict()) for s in agent_output.suggestions],
            confidence_score=0.85,
            generation_method="ai_analysis",
            last_updated=datetime.now()
        )

    async def generate_actionable_insights(self, user_id: str) -> List[ActionableInsight]:
        """Generate actionable insights from spending patterns"""
        transactions = await self.get_user_transactions(user_id)
        pattern_insights = []  # Get from pattern analysis service
        
        insights = []
        for pattern in pattern_insights:
            insight = ActionableInsight(
                insight_type=pattern.insight_type,
                title=pattern.title,
                description=pattern.description,
                data_points=pattern.data_points,
                recommended_actions=pattern.suggested_actions,
                potential_impact=pattern.impact_level,
                urgency=SuggestionPriority.HIGH if pattern.is_significant else SuggestionPriority.MEDIUM,
                confidence=pattern.confidence
            )
            insights.append(insight)
        
        return insights

    async def record_suggestion_feedback(self, user_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record user feedback on suggestions"""
        feedback_id = await self.db.suggestion_feedback.insert_one({
            "user_id": user_id,
            "suggestion_id": feedback_data["suggestion_id"],
            "rating": feedback_data["rating"],
            "feedback_type": feedback_data["feedback_type"],
            "comments": feedback_data.get("comments"),
            "implementation_status": feedback_data.get("implementation_status"),
            "created_at": datetime.now()
        })
        
        # Update suggestion status if implemented
        if feedback_data.get("feedback_type") == "implemented":
            await self.db.suggestions.update_one(
                {"_id": feedback_data["suggestion_id"]},
                {"$set": {"status": SuggestionStatus.IMPLEMENTED}}
            )
        
        return {"feedback_id": str(feedback_id.inserted_id), "recorded": True}

    async def get_suggestion_history(self, user_id: str, limit: int = 10, suggestion_type: str = None) -> List[Dict[str, Any]]:
        """Get historical suggestions and their outcomes"""
        query = {"user_id": user_id}
        if suggestion_type:
            query["type"] = suggestion_type

        history = await self.db.suggestion_history.find(query).limit(limit).to_list(None)
        
        # Enrich with feedback data
        for item in history:
            feedback = await self.db.suggestion_feedback.find_one({"suggestion_id": item["suggestion_id"]})
            if feedback:
                item["feedback"] = feedback
        
        return history

    async def batch_generate_suggestions(self, user_id: str, config: Dict[str, Any]) -> SuggestionBatch:
        """Generate a batch of suggestions for the dashboard"""
        transactions = await self.get_user_transactions(user_id)
        preferences = await self.get_user_preferences(user_id)
        pattern_insights = []  # Get from pattern analysis service

        # Get suggestions from agent
        agent_input = SuggestionAgentInput(
            pattern_insights=pattern_insights,
            budget_thresholds=preferences.get("budget_thresholds", {}),
            user_preferences=preferences
        )
        agent_output = self.suggestion_agent.process(agent_input)

        # Organize suggestions by type
        suggestions_by_type = {
            "budget": [],
            "savings": [],
            "spending": [],
            "security": [],
            "goals": []
        }

        for suggestion in agent_output.suggestions:
            suggestion_type = suggestion.type.value
            if suggestion_type in suggestions_by_type:
                suggestions_by_type[suggestion_type].append(suggestion)

        # Calculate total potential savings
        total_savings = sum(
            Decimal(str(s.potential_savings))
            for suggestions in suggestions_by_type.values()
            for s in suggestions
            if s.potential_savings is not None
        )

        return SuggestionBatch(
            user_id=user_id,
            suggestions_by_type=suggestions_by_type,
            total_potential_savings=total_savings,
            priority_suggestions=[s for s in agent_output.suggestions if s.priority in (SuggestionPriority.HIGH, SuggestionPriority.CRITICAL)][:5],
            generated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=1)
        )
