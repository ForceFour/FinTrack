"""
Safety & Compliance Guard Agent - Agent 6
Role: Flag anomalies and unusual transactions for security
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor
from pydantic import BaseModel, Field

from ..schemas.transaction_schemas import ClassifiedTransaction, SecurityAlert
from ..models.anomaly_detector import AnomalyDetector
from ..utils.security_utils import SecurityValidator


class SafetyGuardAgentInput(BaseModel):
    """Input schema for Safety & Compliance Guard Agent"""
    classified_transactions: List[ClassifiedTransaction] = Field(description="Transactions with categories")
    user_profile: Dict[str, Any] = Field(description="User spending profile and normal patterns")


class SafetyGuardAgentOutput(BaseModel):
    """Output schema for Safety & Compliance Guard Agent"""
    security_alerts: List[SecurityAlert] = Field(description="Security and anomaly alerts")
    flagged_transactions: List[ClassifiedTransaction] = Field(description="Transactions flagged as suspicious")
    risk_score: float = Field(description="Overall risk score for the transaction batch")


class SafetyGuardAgent:
    """
    Agent 6: Safety & Compliance Guard Agent

    Responsibilities:
    - Detect anomalous transactions using ML models or rule-based systems
    - Flag suspicious spending patterns
    - Identify potential fraud indicators
    - Check for compliance with spending limits
    - Generate security alerts for unusual activity
    - Maintain user spending profile for baseline comparison
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.anomaly_detector = AnomalyDetector()
        self.security_validator = SecurityValidator()

    def detect_amount_anomalies(self, transactions: List[ClassifiedTransaction], user_profile: Dict[str, Any]) -> List[ClassifiedTransaction]:
        """Detect transactions with unusual amounts"""
        # Simple implementation: flag transactions over $500 as anomalies
        return [tx for tx in transactions if abs(tx.amount) > 500]

    def detect_frequency_anomalies(self, transactions: List[ClassifiedTransaction], user_profile: Dict[str, Any]) -> List[ClassifiedTransaction]:
        """Detect unusual transaction frequency patterns"""
        # Simple implementation: return empty list for now
        return []

    def detect_location_anomalies(self, transactions: List[ClassifiedTransaction], user_profile: Dict[str, Any]) -> List[ClassifiedTransaction]:
        """Detect transactions in unusual locations (if location data available)"""
        # Simple implementation: return empty list for now
        return []

    def detect_time_anomalies(self, transactions: List[ClassifiedTransaction], user_profile: Dict[str, Any]) -> List[ClassifiedTransaction]:
        """Detect transactions at unusual times"""
        # Simple implementation: flag transactions after 11 PM or before 5 AM
        return [tx for tx in transactions if tx.day_of_week >= 5 or tx.date.hour >= 23 or tx.date.hour <= 5]

    def check_spending_limits(self, transactions: List[ClassifiedTransaction], limits: Dict[str, float]) -> List[SecurityAlert]:
        """Check if transactions exceed predefined spending limits"""
        alerts = []
        for tx in transactions:
            category_limit = limits.get(str(tx.predicted_category), float('inf'))
            if abs(tx.amount) > category_limit:
                alerts.append(SecurityAlert(
                    alert_type="limit_exceeded",
                    severity="medium",
                    title=f"Spending limit exceeded for {tx.predicted_category}",
                    description=f"Transaction of ${abs(tx.amount):.2f} exceeds limit of ${category_limit:.2f}",
                    transaction_id=tx.id,
                    risk_score=0.6,
                    recommended_action="Review transaction and consider adjusting budget",
                    timestamp=datetime.now()
                ))
        return alerts

    def calculate_risk_score(self, transactions: List[ClassifiedTransaction], anomalies: List[ClassifiedTransaction]) -> float:
        """Calculate overall risk score for the transaction batch"""
        if not transactions:
            return 0.0

        # Calculate risk based on anomaly ratio and severity
        anomaly_ratio = len(anomalies) / len(transactions)

        # Base risk from anomaly ratio
        risk_score = min(1.0, anomaly_ratio * 2)

        # Increase risk for high-value anomalies
        for anomaly in anomalies:
            if abs(anomaly.amount) > 500:
                risk_score = min(1.0, risk_score + 0.3)
            elif anomaly.day_of_week >= 5 or anomaly.date.hour >= 23 or anomaly.date.hour <= 5:
                risk_score = min(1.0, risk_score + 0.1)

        return risk_score

    def generate_security_alerts(self, flagged_transactions: List[ClassifiedTransaction]) -> List[SecurityAlert]:
        """Generate security alerts for flagged transactions"""
        alerts = []
        for tx in flagged_transactions:
            if abs(tx.amount) > 500:
                alerts.append(SecurityAlert(
                    alert_type="amount_anomaly",
                    severity="high",
                    title="Unusual transaction amount detected",
                    description=f"Transaction of ${abs(tx.amount):.2f} is unusually high",
                    transaction_id=tx.id,
                    risk_score=0.8,
                    recommended_action="Verify this transaction with your bank",
                    timestamp=datetime.now()
                ))
            elif tx.day_of_week >= 5 or tx.date.hour >= 23 or tx.date.hour <= 5:
                alerts.append(SecurityAlert(
                    alert_type="time_anomaly",
                    severity="medium",
                    title="Unusual transaction timing",
                    description=f"Transaction occurred at unusual time: {tx.date.strftime('%A %H:%M')}",
                    transaction_id=tx.id,
                    risk_score=0.4,
                    recommended_action="Review transaction for legitimacy",
                    timestamp=datetime.now()
                ))
        return alerts

    def update_user_profile(self, transactions: List[ClassifiedTransaction], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Update user spending profile with new transaction data"""
        # Implementation for user profile updates
        pass

    def process(self, input_data: SafetyGuardAgentInput) -> SafetyGuardAgentOutput:
        """Main processing method for the Safety & Compliance Guard Agent"""
        transactions = input_data.classified_transactions
        user_profile = input_data.user_profile

        # Detect anomalies
        amount_anomalies = self.detect_amount_anomalies(transactions, user_profile)
        frequency_anomalies = self.detect_frequency_anomalies(transactions, user_profile)
        location_anomalies = self.detect_location_anomalies(transactions, user_profile)
        time_anomalies = self.detect_time_anomalies(transactions, user_profile)

        # Combine all flagged transactions
        all_flagged = amount_anomalies + frequency_anomalies + location_anomalies + time_anomalies

        # Remove duplicates based on transaction ID
        seen_ids = set()
        unique_flagged = []
        for tx in all_flagged:
            if tx.id not in seen_ids:
                unique_flagged.append(tx)
                seen_ids.add(tx.id)

        # Check spending limits (if defined in user profile)
        spending_limits = user_profile.get('spending_limits', {})
        limit_alerts = self.check_spending_limits(transactions, spending_limits)

        # Calculate overall risk score
        risk_score = self.calculate_risk_score(transactions, unique_flagged)

        # Generate security alerts
        security_alerts = self.generate_security_alerts(unique_flagged)
        security_alerts.extend(limit_alerts)

        return SafetyGuardAgentOutput(
            security_alerts=security_alerts,
            flagged_transactions=unique_flagged,
            risk_score=risk_score
        )
