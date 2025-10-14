"""Transaction data schemas using Pydantic"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TransactionType(str, Enum):
    """Transaction types"""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class PaymentMethod(str, Enum):
    """Sri Lankan payment methods"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CHECK = "check"
    # Sri Lanka specific payment methods
    MOBILE_MONEY = "mobile_money"  # Dialog eZ Cash, Mobitel mCash
    ONLINE_BANKING = "online_banking"  # BOC, Commercial Bank, etc.
    ATM_TRANSFER = "atm_transfer"
    RTGS = "rtgs"  # Real Time Gross Settlement
    SLIPS = "slips"  # Sri Lanka Interbank Payment System
    OTHER = "other"


class TransactionCategory(str, Enum):
    """Sri Lankan transaction categories (both income and expense)"""
    # Income categories
    SALARY = "salary"  # Regular employment income
    FREELANCE = "freelance"  # Contract/freelance work
    BUSINESS = "business"  # Business income/revenue
    INVESTMENT = "investment"  # Dividends, interest, capital gains
    RENTAL = "rental"  # Rental income
    REFUND = "refund"  # Refunds, reimbursements, cashback
    GIFT = "gift"  # Gifts received
    OTHER_INCOME = "other_income"  # Other income sources

    # Expense categories
    FOOD_DINING = "food_dining"
    GROCERIES = "groceries"
    TRANSPORTATION = "transportation"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    SHOPPING = "shopping"
    SUBSCRIPTIONS = "subscriptions"
    EDUCATION = "education"
    TRAVEL = "travel"
    # Sri Lanka specific categories
    RELIGIOUS_DONATIONS = "religious_donations"  # Temple, Church donations
    GOVERNMENT_SERVICES = "government_services"  # License fees, taxes, etc.
    DOMESTIC_HELP = "domestic_help"  # Maid, driver payments
    TELECOMMUNICATIONS = "telecommunications"  # Mobile, internet bills
    FUEL = "fuel"  # Petrol, diesel - important category in Sri Lanka
    MEDICAL_INSURANCE = "medical_insurance"
    MISCELLANEOUS = "miscellaneous"


class RawTransaction(BaseModel):
    """Raw transaction data as received from bank/CSV"""
    id: Optional[str] = Field(None, description="Transaction ID")
    date: str = Field(description="Date string in various formats")
    amount: str = Field(description="Amount as string (may include currency symbols)")
    description: str = Field(description="Raw transaction description")
    payment_method: str = Field(description="Payment method as string")
    balance: Optional[str] = Field(None, description="Account balance after transaction")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class PreprocessedTransaction(BaseModel):
    """Preprocessed transaction with normalized fields"""
    id: str = Field(description="Transaction ID")
    date: datetime = Field(description="Parsed datetime")
    year: int = Field(description="Year extracted from date")
    month: int = Field(description="Month extracted from date")
    day: int = Field(description="Day extracted from date")
    day_of_week: int = Field(description="Day of week (0=Monday, 6=Sunday)")
    amount: float = Field(description="Numeric amount")
    transaction_type: TransactionType = Field(description="Transaction type (income/expense/transfer)")
    payment_method: PaymentMethod = Field(description="Standardized payment method")
    description_cleaned: str = Field(description="Cleaned transaction description")
    has_discount: bool = Field(False, description="Whether transaction includes discount")
    discount_percentage: Optional[float] = Field(None, description="Discount percentage if available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MerchantTransaction(PreprocessedTransaction):
    """Transaction with extracted merchant information"""
    merchant_name: Optional[str] = Field(None, description="Extracted merchant name")
    merchant_standardized: Optional[str] = Field(None, description="Standardized merchant name")
    merchant_category: Optional[str] = Field(None, description="Merchant category if available")
    is_merchant_known: bool = Field(False, description="Whether merchant is recognized")


class ClassifiedTransaction(MerchantTransaction):
    """Transaction with predicted category"""
    predicted_category: TransactionCategory = Field(description="Predicted expense category")
    prediction_confidence: float = Field(description="Confidence score for category prediction")
    category_probabilities: Dict[str, float] = Field(default_factory=dict, description="Probabilities for all categories")


class PatternInsight(BaseModel):
    """Insight from pattern analysis"""
    insight_type: str = Field(description="Type of insight (recurring, spike, trend, etc.)")
    category: Optional[str] = Field(None, description="Related category")
    description: str = Field(description="Human-readable insight description")
    severity: str = Field(description="Severity level (low, medium, high)")
    transactions_involved: List[str] = Field(description="Transaction IDs involved in this insight")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional insight metadata")


class Suggestion(BaseModel):
    """Financial suggestion/recommendation"""
    suggestion_type: str = Field(description="Type of suggestion (budget, reduction, alert)")
    title: str = Field(description="Suggestion title")
    description: str = Field(description="Detailed suggestion description")
    priority: str = Field(description="Priority level (low, medium, high)")
    potential_savings: Optional[float] = Field(None, description="Potential savings amount")
    category: Optional[str] = Field(None, description="Related category")
    action_required: bool = Field(False, description="Whether user action is required")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional suggestion metadata")


class SecurityAlert(BaseModel):
    """Security/anomaly alert"""
    alert_type: str = Field(description="Type of alert (anomaly, fraud, limit)")
    severity: str = Field(description="Alert severity (low, medium, high, critical)")
    title: str = Field(description="Alert title")
    description: str = Field(description="Detailed alert description")
    transaction_id: str = Field(description="Related transaction ID")
    risk_score: float = Field(description="Risk score for this alert")
    recommended_action: str = Field(description="Recommended action for user")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert generation timestamp")
