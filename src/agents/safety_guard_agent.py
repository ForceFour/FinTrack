"""
Safety & Compliance Guard Agent - Agent 6
Role: Flag anomalies and unusual transactions for security
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter
import numpy as np
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
        """
        Detect transactions with unusual amounts using statistical outlier detection (IQR method)
        """
        if not transactions or len(transactions) < 4:
            # Need at least 4 transactions for meaningful statistical analysis
            return []

        # Get historical transactions from user profile for better baseline
        historical_amounts = user_profile.get('historical_amounts', [])

        # Combine current and historical amounts
        amounts = [abs(tx.amount) for tx in transactions]
        if historical_amounts:
            amounts = historical_amounts + amounts

        if len(amounts) < 4:
            return []

        # Calculate IQR (Interquartile Range) for outlier detection
        q1 = np.percentile(amounts, 25)
        q3 = np.percentile(amounts, 75)
        iqr = q3 - q1

        # Define outlier boundaries (using 1.5 * IQR, standard statistical method)
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        # Flag transactions that are outliers
        anomalous_transactions = []
        for tx in transactions:
            amount = abs(tx.amount)
            if amount > upper_bound or amount < lower_bound:
                anomalous_transactions.append(tx)

        return anomalous_transactions

    def detect_frequency_anomalies(self, transactions: List[ClassifiedTransaction], user_profile: Dict[str, Any]) -> List[ClassifiedTransaction]:
        """
        Detect unusual transaction frequency patterns
        Flags merchants/categories with unusually high transaction frequency
        """
        if not transactions or len(transactions) < 5:
            return []

        anomalous_transactions = []

        # Group transactions by merchant
        merchant_groups = {}
        for tx in transactions:
            merchant = tx.merchant_name or 'Unknown'
            if merchant not in merchant_groups:
                merchant_groups[merchant] = []
            merchant_groups[merchant].append(tx)

        # Flag merchants with high frequency (more than 10 transactions)
        frequency_threshold = user_profile.get('frequency_threshold', 10)

        for merchant, txs in merchant_groups.items():
            if len(txs) >= frequency_threshold:
                # This merchant has unusually high frequency
                anomalous_transactions.extend(txs)

        # Group transactions by category
        category_groups = {}
        for tx in transactions:
            category = str(tx.predicted_category)
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(tx)

        # Flag categories with extremely high frequency (more than 15 transactions)
        category_threshold = user_profile.get('category_frequency_threshold', 15)

        for category, txs in category_groups.items():
            if len(txs) >= category_threshold:
                # Add these if not already flagged
                for tx in txs:
                    if tx not in anomalous_transactions:
                        anomalous_transactions.append(tx)

        return anomalous_transactions

    def detect_location_anomalies(self, transactions: List[ClassifiedTransaction], user_profile: Dict[str, Any]) -> List[ClassifiedTransaction]:
        """
        Detect transactions in unusual locations
        Flags locations that appear more than 15-20 times (suspicious repetition)
        """
        if not transactions:
            return []

        anomalous_transactions = []

        # Count transactions by location (using merchant_name as proxy for location)
        location_counter = Counter()
        location_to_transactions = {}

        for tx in transactions:
            # Use merchant_name as location identifier
            # In future, can use actual location data if available
            location = tx.merchant_name or 'Unknown'
            location_counter[location] += 1

            if location not in location_to_transactions:
                location_to_transactions[location] = []
            location_to_transactions[location].append(tx)

        # Flag locations with excessive repetition (15-20+ times)
        location_threshold = user_profile.get('location_repetition_threshold', 15)

        for location, count in location_counter.items():
            if count >= location_threshold:
                # This location appears too many times - suspicious
                anomalous_transactions.extend(location_to_transactions[location])

        return anomalous_transactions

    def detect_time_anomalies(self, transactions: List[ClassifiedTransaction], user_profile: Dict[str, Any]) -> List[ClassifiedTransaction]:
        """
        Detect transactions at unusual times
        ONLY flags if transaction explicitly has a time between 1:00 AM - 3:00 AM
        Does NOT flag transactions with default/system timestamps
        """
        anomalous_transactions = []

        # Define suspicious time window (1 AM to 3 AM)
        suspicious_start_hour = 1
        suspicious_end_hour = 3

        for tx in transactions:
            # Check if transaction has explicit time data (not just a default date)
            # Only flag if the hour is explicitly set to suspicious hours
            tx_hour = tx.date.hour
            tx_minute = tx.date.minute
            tx_second = tx.date.second

            # Check if this is likely a real transaction time (not a default timestamp)
            # Default timestamps usually have 00:00:00 or similar patterns
            # Real transaction times have varying minutes/seconds
            has_explicit_time = (tx_minute != 0 or tx_second != 0) or (
                # Or if hour is in suspicious range with exact 00:00:00, still check
                suspicious_start_hour <= tx_hour < suspicious_end_hour
            )

            # Only flag if:
            # 1. Transaction is in suspicious time window (1 AM - 3 AM)
            # 2. Has explicit time data (not bulk upload default time)
            if suspicious_start_hour <= tx_hour < suspicious_end_hour:
                # Additional check: if this is bulk upload data, skip it
                # Bulk uploads typically have metadata indicating batch processing
                metadata = getattr(tx, 'metadata', {})
                is_bulk_upload = metadata.get('source') == 'bulk_upload' or metadata.get('batch_id')

                # Only flag if NOT a bulk upload and has suspicious time
                if not is_bulk_upload:
                    anomalous_transactions.append(tx)

        return anomalous_transactions

    def check_spending_limits(self, transactions: List[ClassifiedTransaction], limits: Dict[str, float], currency: str = "LKR") -> List[SecurityAlert]:
        """Check if transactions exceed predefined spending limits"""
        alerts = []
        for tx in transactions:
            category_limit = limits.get(str(tx.predicted_category), float('inf'))
            if abs(tx.amount) > category_limit:
                alerts.append(SecurityAlert(
                    alert_type="limit_exceeded",
                    severity="medium",
                    title=f"Spending limit exceeded for {tx.predicted_category}",
                    description=f"Transaction on {tx.date.strftime('%Y-%m-%d %H:%M')} for {currency} {abs(tx.amount):.2f} at {tx.merchant_name} exceeds your {tx.predicted_category} limit of {currency} {category_limit:.2f}",
                    transaction_id=tx.id,
                    risk_score=0.6,
                    recommended_action="Review transaction and consider adjusting budget",
                    timestamp=datetime.now(),
                    merchant=tx.merchant_name,
                    amount=abs(tx.amount)
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
            elif anomaly.date.hour < 3:  # Only very unusual hours (3 AM rule)
                risk_score = min(1.0, risk_score + 0.1)

        return risk_score

    def generate_security_alerts(self,
                                 flagged_transactions: List[ClassifiedTransaction],
                                 amount_anomalies: List[ClassifiedTransaction],
                                 frequency_anomalies: List[ClassifiedTransaction],
                                 location_anomalies: List[ClassifiedTransaction],
                                 time_anomalies: List[ClassifiedTransaction],
                                 currency: str = "LKR") -> List[SecurityAlert]:
        """
        Generate security alerts for flagged transactions
        Creates specific alerts based on anomaly type
        """
        alerts = []

        # Track which transactions have been alerted for which type
        alerted_transactions = {}

        # Amount anomaly alerts
        for tx in amount_anomalies:
            if tx.id not in alerted_transactions:
                alerted_transactions[tx.id] = []

            if 'amount' not in alerted_transactions[tx.id]:
                alerts.append(SecurityAlert(
                    alert_type="amount_anomaly",
                    severity="high",
                    title="Unusual Transaction Amount Detected",
                    description=f"Transaction on {tx.date.strftime('%Y-%m-%d %H:%M')} for {currency} {abs(tx.amount):.2f} at {tx.merchant_name} ({str(tx.predicted_category)} category) is significantly outside your normal spending pattern (statistical outlier)",
                    transaction_id=tx.id,
                    risk_score=0.8,
                    recommended_action="Verify this transaction is legitimate. Contact your bank if you don't recognize it.",
                    timestamp=datetime.now(),
                    merchant=tx.merchant_name,
                    amount=abs(tx.amount)
                ))
                alerted_transactions[tx.id].append('amount')

        # Frequency anomaly alerts
        for tx in frequency_anomalies:
            if tx.id not in alerted_transactions:
                alerted_transactions[tx.id] = []

            if 'frequency' not in alerted_transactions[tx.id]:
                alerts.append(SecurityAlert(
                    alert_type="frequency_anomaly",
                    severity="medium",
                    title="Unusual Transaction Frequency",
                    description=f"Transaction on {tx.date.strftime('%Y-%m-%d %H:%M')} for LKR {abs(tx.amount):.2f} at {tx.merchant_name}. Unusually high number of transactions at this merchant ({str(tx.predicted_category)} category). This could indicate unauthorized recurring charges.",
                    transaction_id=tx.id,
                    risk_score=0.6,
                    recommended_action="Review all recent transactions at this merchant. Consider canceling recurring subscriptions if unauthorized.",
                    timestamp=datetime.now(),
                    merchant=tx.merchant_name,
                    amount=abs(tx.amount)
                ))
                alerted_transactions[tx.id].append('frequency')

        # Location anomaly alerts
        for tx in location_anomalies:
            if tx.id not in alerted_transactions:
                alerted_transactions[tx.id] = []

            if 'location' not in alerted_transactions[tx.id]:
                alerts.append(SecurityAlert(
                    alert_type="location_anomaly",
                    severity="medium",
                    title="Suspicious Location Pattern",
                    description=f"Transaction on {tx.date.strftime('%Y-%m-%d %H:%M')} for LKR {abs(tx.amount):.2f} at {tx.merchant_name}. Excessive repetition detected at this location (15+ transactions total). This pattern is unusual and may indicate fraudulent activity.",
                    transaction_id=tx.id,
                    risk_score=0.65,
                    recommended_action="Verify all transactions at this location. Report suspicious activity to your bank immediately.",
                    timestamp=datetime.now(),
                    merchant=tx.merchant_name,
                    amount=abs(tx.amount)
                ))
                alerted_transactions[tx.id].append('location')

        # Time anomaly alerts
        for tx in time_anomalies:
            if tx.id not in alerted_transactions:
                alerted_transactions[tx.id] = []

            if 'time' not in alerted_transactions[tx.id]:
                alerts.append(SecurityAlert(
                    alert_type="time_anomaly",
                    severity="high",
                    title="Suspicious Transaction Time",
                    description=f"Transaction occurred at {tx.date.strftime('%I:%M %p on %A, %B %d')} (between 1:00 AM - 3:00 AM). Transactions at this hour are uncommon and may indicate unauthorized access.",
                    transaction_id=tx.id,
                    risk_score=0.75,
                    recommended_action="Verify this transaction immediately. If you didn't make it, contact your bank to freeze your card.",
                    timestamp=datetime.now()
                ))
                alerted_transactions[tx.id].append('time')

        return alerts

    def update_user_profile(self, transactions: List[ClassifiedTransaction], user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Update user spending profile with new transaction data"""
        # Implementation for user profile updates
        pass

    def generate_default_security_recommendations(self, user_profile: Dict[str, Any]) -> List[SecurityAlert]:
        """
        Generate general security recommendations for new users
        Only shown when NO anomalies are detected
        """
        # Check if user is new (no transaction history)
        is_new_user = user_profile.get('is_new_user', True)
        has_seen_recommendations = user_profile.get('has_seen_security_recommendations', False)

        # Only show recommendations for new users who haven't seen them
        if not is_new_user or has_seen_recommendations:
            return []

        recommendations = [
            SecurityAlert(
                alert_type="security_setup",
                severity="info",
                title="Enable Account Security Features",
                description="Set up two-factor authentication and review account security settings.",
                transaction_id="general",
                risk_score=0.0,
                recommended_action="Enable 2FA and use strong, unique passwords",
                timestamp=datetime.now()
            ),
            SecurityAlert(
                alert_type="fraud_awareness",
                severity="info",
                title="Monitor Your Accounts Regularly",
                description="Check your bank and credit card statements regularly for unauthorized transactions.",
                transaction_id="general",
                risk_score=0.0,
                recommended_action="Set up account alerts for transactions",
                timestamp=datetime.now()
            )
        ]

        return recommendations

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

        # Get currency from user preferences (default to LKR)
        currency = user_profile.get('preferences', {}).get('currency', 'LKR')

        # Check spending limits (if defined in user profile)
        spending_limits = user_profile.get('spending_limits', {})
        limit_alerts = self.check_spending_limits(transactions, spending_limits, currency)

        # Calculate overall risk score
        risk_score = self.calculate_risk_score(transactions, unique_flagged)

        # Generate security alerts based on specific anomaly types
        security_alerts = self.generate_security_alerts(
            unique_flagged,
            amount_anomalies,
            frequency_anomalies,
            location_anomalies,
            time_anomalies,
            currency
        )
        security_alerts.extend(limit_alerts)

        # If NO anomalies detected and user is new, provide general security recommendations
        if not security_alerts and not unique_flagged:
            default_recommendations = self.generate_default_security_recommendations(user_profile)
            security_alerts.extend(default_recommendations)

        return SafetyGuardAgentOutput(
            security_alerts=security_alerts,
            flagged_transactions=unique_flagged,
            risk_score=risk_score
        )
