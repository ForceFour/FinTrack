"""
Security utilities for transaction validation and anomaly detection
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import re
from enum import Enum

class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(str, Enum):
    """Types of security alerts"""
    AMOUNT_ANOMALY = "amount_anomaly"
    FREQUENCY_ANOMALY = "frequency_anomaly" 
    TIME_ANOMALY = "time_anomaly"
    MERCHANT_ANOMALY = "merchant_anomaly"
    SPENDING_LIMIT = "spending_limit"
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    FRAUD_PATTERN = "fraud_pattern"

class SecurityValidator:
    """Security validation and risk assessment for transactions"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.suspicious_merchants = self.config.get('suspicious_merchants', [])
        self.max_transaction_amount = self.config.get('max_transaction_amount', 10000)
        self.high_risk_hours = self.config.get('high_risk_hours', [0, 1, 2, 3, 4, 5])
        
    def validate_transaction_amount(
        self, 
        transaction: Dict[str, Any], 
        user_profile: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Validate if transaction amount is suspicious
        Returns: (is_suspicious, risk_score, reason)
        """
        amount = float(transaction.get('amount', 0))
        avg_amount = user_profile.get('average_transaction_amount', 100)
        
        # Check against absolute limits
        if amount > self.max_transaction_amount:
            return True, 0.9, f"Transaction amount ${amount} exceeds maximum limit"
        
        # Check against user's spending pattern
        if avg_amount > 0:
            ratio = amount / avg_amount
            if ratio > 10:  # More than 10x average
                return True, 0.8, f"Transaction amount is {ratio:.1f}x higher than average"
            elif ratio > 5:  # More than 5x average
                return True, 0.6, f"Transaction amount is {ratio:.1f}x higher than average"
            elif ratio > 3:  # More than 3x average
                return True, 0.4, f"Transaction amount is moderately higher than average"
        
        return False, 0.1, "Amount within normal range"
    
    def validate_transaction_frequency(
        self, 
        transactions: List[Dict[str, Any]], 
        user_profile: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Validate if transaction frequency is suspicious
        Returns: (is_suspicious, risk_score, reason)
        """
        if len(transactions) < 2:
            return False, 0.1, "Insufficient transactions to analyze frequency"
        
        # Count transactions in last hour
        now = datetime.now()
        recent_transactions = []
        
        for txn in transactions:
            try:
                txn_time = datetime.fromisoformat(txn.get('date', ''))
                if (now - txn_time).total_seconds() < 3600:  # Last hour
                    recent_transactions.append(txn)
            except:
                continue
        
        hourly_count = len(recent_transactions)
        normal_hourly_rate = user_profile.get('average_hourly_transactions', 2)
        
        if hourly_count > normal_hourly_rate * 5:
            return True, 0.8, f"Unusually high transaction frequency: {hourly_count} in last hour"
        elif hourly_count > normal_hourly_rate * 3:
            return True, 0.6, f"High transaction frequency: {hourly_count} in last hour"
        
        return False, 0.1, "Transaction frequency within normal range"
    
    def validate_merchant(
        self, 
        transaction: Dict[str, Any], 
        user_profile: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Validate merchant against known patterns and blacklists
        Returns: (is_suspicious, risk_score, reason)
        """
        merchant = transaction.get('merchant_standardized', '').lower()
        known_merchants = [m.lower() for m in user_profile.get('known_merchants', [])]
        
        # Check suspicious merchants
        if merchant in [m.lower() for m in self.suspicious_merchants]:
            return True, 0.9, f"Transaction with known suspicious merchant: {merchant}"
        
        # Check if merchant is completely new
        if merchant and merchant not in known_merchants:
            # Additional checks for potentially suspicious merchant names
            suspicious_patterns = [
                r'test.*merchant',
                r'temp.*store',
                r'\d{10,}',  # Long strings of numbers
                r'[a-z]{20,}',  # Very long strings
                r'xxx.*',
                r'temp.*'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, merchant, re.IGNORECASE):
                    return True, 0.7, f"Merchant name matches suspicious pattern: {merchant}"
            
            return True, 0.3, f"Transaction with new merchant: {merchant}"
        
        return False, 0.1, "Merchant validation passed"
    
    def validate_transaction_time(
        self, 
        transaction: Dict[str, Any], 
        user_profile: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Validate if transaction time is suspicious
        Returns: (is_suspicious, risk_score, reason)
        """
        try:
            txn_time = datetime.fromisoformat(transaction.get('date', ''))
            hour = txn_time.hour
            
            # Check if transaction is during high-risk hours
            if hour in self.high_risk_hours:
                return True, 0.5, f"Transaction at unusual time: {hour:02d}:00"
            
            # Check against user's normal transaction hours
            normal_hours = user_profile.get('normal_transaction_hours', list(range(6, 23)))
            if hour not in normal_hours:
                return True, 0.4, f"Transaction outside normal hours: {hour:02d}:00"
        
        except Exception as e:
            return True, 0.3, f"Unable to validate transaction time: {str(e)}"
        
        return False, 0.1, "Transaction time within normal range"
    
    def check_duplicate_transactions(
        self, 
        transaction: Dict[str, Any], 
        recent_transactions: List[Dict[str, Any]]
    ) -> Tuple[bool, float, str]:
        """
        Check for potential duplicate transactions
        Returns: (is_duplicate, risk_score, reason)
        """
        amount = transaction.get('amount', 0)
        merchant = transaction.get('merchant_standardized', '')
        txn_date = transaction.get('date', '')
        
        for recent_txn in recent_transactions:
            # Check for exact matches within 5 minutes
            if (recent_txn.get('amount') == amount and 
                recent_txn.get('merchant_standardized') == merchant):
                
                try:
                    recent_time = datetime.fromisoformat(recent_txn.get('date', ''))
                    current_time = datetime.fromisoformat(txn_date)
                    time_diff = abs((current_time - recent_time).total_seconds())
                    
                    if time_diff < 300:  # 5 minutes
                        return True, 0.9, f"Potential duplicate transaction within 5 minutes"
                    elif time_diff < 3600:  # 1 hour
                        return True, 0.6, f"Similar transaction within 1 hour"
                except:
                    pass
        
        return False, 0.1, "No duplicate transactions found"
    
    def assess_overall_risk(
        self, 
        transaction: Dict[str, Any], 
        user_profile: Dict[str, Any],
        recent_transactions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment
        Returns: Complete risk assessment report
        """
        if recent_transactions is None:
            recent_transactions = []
        
        assessment_results = []
        total_risk_score = 0.0
        
        # Amount validation
        is_suspicious, risk_score, reason = self.validate_transaction_amount(transaction, user_profile)
        assessment_results.append({
            'check_type': 'amount_validation',
            'is_suspicious': is_suspicious,
            'risk_score': risk_score,
            'reason': reason
        })
        total_risk_score = max(total_risk_score, risk_score)
        
        # Frequency validation
        is_suspicious, risk_score, reason = self.validate_transaction_frequency(
            recent_transactions + [transaction], user_profile
        )
        assessment_results.append({
            'check_type': 'frequency_validation',
            'is_suspicious': is_suspicious,
            'risk_score': risk_score,
            'reason': reason
        })
        total_risk_score = max(total_risk_score, risk_score)
        
        # Merchant validation
        is_suspicious, risk_score, reason = self.validate_merchant(transaction, user_profile)
        assessment_results.append({
            'check_type': 'merchant_validation',
            'is_suspicious': is_suspicious,
            'risk_score': risk_score,
            'reason': reason
        })
        total_risk_score = max(total_risk_score, risk_score)
        
        # Time validation
        is_suspicious, risk_score, reason = self.validate_transaction_time(transaction, user_profile)
        assessment_results.append({
            'check_type': 'time_validation',
            'is_suspicious': is_suspicious,
            'risk_score': risk_score,
            'reason': reason
        })
        total_risk_score = max(total_risk_score, risk_score)
        
        # Duplicate check
        is_suspicious, risk_score, reason = self.check_duplicate_transactions(transaction, recent_transactions)
        assessment_results.append({
            'check_type': 'duplicate_check',
            'is_suspicious': is_suspicious,
            'risk_score': risk_score,
            'reason': reason
        })
        total_risk_score = max(total_risk_score, risk_score)
        
        # Determine overall risk level
        if total_risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif total_risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif total_risk_score >= 0.4:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return {
            'transaction_id': transaction.get('id', 'unknown'),
            'overall_risk_score': round(total_risk_score, 2),
            'risk_level': risk_level,
            'assessment_results': assessment_results,
            'requires_review': total_risk_score >= 0.6,
            'requires_immediate_attention': total_risk_score >= 0.8,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_security_alert(
        self, 
        risk_assessment: Dict[str, Any],
        alert_type: AlertType = AlertType.FRAUD_PATTERN
    ) -> Dict[str, Any]:
        """Generate a structured security alert"""
        risk_level = risk_assessment.get('risk_level', RiskLevel.LOW)
        risk_score = risk_assessment.get('overall_risk_score', 0.0)
        
        # Determine alert severity
        if risk_score >= 0.8:
            severity = "critical"
        elif risk_score >= 0.6:
            severity = "high"
        elif risk_score >= 0.4:
            severity = "medium"
        else:
            severity = "low"
        
        # Generate alert title and description
        suspicious_checks = [
            result for result in risk_assessment.get('assessment_results', [])
            if result.get('is_suspicious', False)
        ]
        
        if suspicious_checks:
            primary_concern = max(suspicious_checks, key=lambda x: x.get('risk_score', 0))
            title = f"Security Alert: {primary_concern.get('check_type', 'Unknown').replace('_', ' ').title()}"
            description = primary_concern.get('reason', 'Suspicious activity detected')
        else:
            title = "Security Alert: Transaction Review Required"
            description = "Transaction flagged for review"
        
        return {
            'alert_id': f"alert_{risk_assessment.get('transaction_id', 'unknown')}_{int(datetime.now().timestamp())}",
            'alert_type': alert_type.value,
            'severity': severity,
            'title': title,
            'description': description,
            'transaction_id': risk_assessment.get('transaction_id', 'unknown'),
            'risk_score': risk_score,
            'risk_level': risk_level.value,
            'recommended_action': self._get_recommended_action(risk_level),
            'timestamp': datetime.now().isoformat(),
            'details': risk_assessment.get('assessment_results', [])
        }
    
    def _get_recommended_action(self, risk_level: RiskLevel) -> str:
        """Get recommended action based on risk level"""
        if risk_level == RiskLevel.CRITICAL:
            return "Immediately freeze account and contact user for verification"
        elif risk_level == RiskLevel.HIGH:
            return "Contact user for transaction verification before processing"
        elif risk_level == RiskLevel.MEDIUM:
            return "Flag for manual review and monitor future transactions"
        else:
            return "Continue monitoring transaction patterns"

class TransactionSafetyChecker:
    """Additional safety checking utilities"""
    
    def is_transaction_safe(self, transaction: Dict[str, Any], user_limits: Dict[str, Any]) -> bool:
        """Quick safety check for transaction approval"""
        amount = float(transaction.get('amount', 0))
        daily_limit = user_limits.get('daily_limit', float('inf'))
        per_transaction_limit = user_limits.get('per_transaction_limit', float('inf'))
        
        return amount <= per_transaction_limit and amount <= daily_limit
    
    def calculate_daily_spending(self, transactions: List[Dict[str, Any]]) -> float:
        """Calculate total spending for current day"""
        today = datetime.now().date()
        daily_total = 0.0
        
        for txn in transactions:
            try:
                txn_date = datetime.fromisoformat(txn.get('date', '')).date()
                if txn_date == today:
                    daily_total += float(txn.get('amount', 0))
            except:
                continue
        
        return daily_total
    
    def get_spending_velocity(self, transactions: List[Dict[str, Any]], hours: int = 24) -> float:
        """Calculate spending velocity (amount per hour) over specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_spending = 0.0
        
        for txn in transactions:
            try:
                txn_time = datetime.fromisoformat(txn.get('date', ''))
                if txn_time >= cutoff_time:
                    recent_spending += float(txn.get('amount', 0))
            except:
                continue
        
        return recent_spending / hours if hours > 0 else 0.0
