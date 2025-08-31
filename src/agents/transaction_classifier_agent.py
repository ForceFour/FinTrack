"""
Transaction Classification Agent - Advanced Income vs Expense Classifier
Role: Classify transactions as Income or Expense with high accuracy using multiple signals
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
import re
import os
import numpy as np
from collections import Counter
from datetime import datetime
from pydantic import BaseModel, Field

from ..schemas.transaction_schemas import PreprocessedTransaction, TransactionCategory

logger = logging.getLogger(__name__)


class TransactionClassificationInput(BaseModel):
    """Input schema for Transaction Classification Agent"""
    preprocessed_transactions: List[PreprocessedTransaction] = Field(description="Preprocessed transaction data")
    user_patterns: Optional[Dict[str, Any]] = Field(None, description="User-specific income/expense patterns")


class ClassifiedTransactionType(BaseModel):
    """Transaction with type classification"""
    transaction_id: str = Field(description="Transaction ID")
    transaction_type: str = Field(description="income or expense")
    classification_confidence: float = Field(description="Confidence score 0-1")
    classification_reasoning: str = Field(description="Why this classification was chosen")
    amount_analysis: Dict[str, Any] = Field(description="Amount-based analysis")
    keyword_analysis: Dict[str, Any] = Field(description="Keyword-based analysis")
    pattern_analysis: Dict[str, Any] = Field(description="Pattern-based analysis")


class TransactionClassificationOutput(BaseModel):
    """Output schema for Transaction Classification Agent"""
    classified_transactions: List[ClassifiedTransactionType] = Field(description="Transactions with type classification")
    classification_stats: Dict[str, Any] = Field(description="Classification statistics")
    learned_patterns: Dict[str, Any] = Field(description="New patterns discovered")


class TransactionClassificationAgent:
    """
    Advanced Transaction Classification Agent
    
    Responsibilities:
    - Classify transactions as Income vs Expense with high accuracy
    - Use multiple signals: amount patterns, keywords, merchant types, timing
    - Learn from user corrections and feedback
    - Handle edge cases: refunds, transfers, cashback, rewards
    - Provide detailed reasoning for each classification
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.8)
        
        # Initialize classification components
        self._init_keyword_patterns()
        self._init_amount_patterns()
        self._init_temporal_patterns()
        self._init_merchant_patterns()
        
        # Learning components
        self.learned_patterns = {
            'income_merchants': Counter(),
            'expense_merchants': Counter(),
            'income_keywords': Counter(),
            'expense_keywords': Counter(),
            'amount_thresholds': {},
            'temporal_patterns': {}
        }
        
        # Performance tracking
        self.classification_stats = {
            'total_classified': 0,
            'high_confidence_count': 0,
            'income_count': 0,
            'expense_count': 0,
            'method_usage': Counter()
        }
    
    def _init_keyword_patterns(self):
        """Initialize comprehensive keyword patterns for classification"""
        
        # Strong income indicators (high confidence) - Sri Lankan context
        self.strong_income_keywords = {
            'salary_payroll': ['salary', 'payroll', 'direct deposit', 'dd payroll', 'paycheck', 'wages', 'monthly salary'],
            'freelance_contract': ['freelance', 'contractor', 'consulting', 'invoice payment', 'client payment', 'professional services'],
            'investment_returns': ['dividend', 'interest', 'investment', 'capital gains', 'stock sale', 'mutual fund'],
            'business_income': ['revenue', 'sales', 'business income', 'commission', 'royalty', 'profit'],
            'government_benefits': ['pension', 'allowance', 'government payment', 'social security', 'welfare'],
            'other_income': ['bonus', 'gift', 'cashback', 'reward', 'reimbursement', 'refund', 'return'],
            'sri_lankan_income': ['epf', 'etf', 'gratuity', 'festival bonus', 'overtime payment', 'poya day bonus']
        }
        
        # Strong expense indicators (high confidence) - Sri Lankan context
        self.strong_expense_keywords = {
            'utilities_bills': ['ceb', 'electricity', 'water board', 'gas bill', 'utility bill'],
            'telecom_bills': ['dialog', 'mobitel', 'airtel', 'hutch', 'internet bill', 'mobile bill'],
            'fuel_transport': ['ceypetco', 'ioc', 'shell', 'petrol', 'diesel', 'fuel', 'uber', 'pickme', 'taxi'],
            'food_dining': ['restaurant', 'hotel', 'rice curry', 'kottu', 'hoppers', 'kfc', 'mcdonalds', 'pizza hut'],
            'groceries': ['keells', 'cargills', 'food city', 'laugfs', 'arpico', 'grocery', 'supermarket'],
            'healthcare': ['nawaloka', 'asiri', 'lanka hospitals', 'osu sala', 'pharmacy', 'doctor', 'hospital'],
            'education': ['school fee', 'tuition', 'university', 'institute', 'class fee', 'exam fee'],
            'government_services': ['rto', 'passport office', 'tax payment', 'license fee', 'registration', 'fine'],
            'banking_fees': ['bank charge', 'atm fee', 'service charge', 'loan payment', 'credit card payment'],
            'religious_donations': ['temple', 'kovil', 'church', 'mosque', 'vihara', 'donation', 'dana', 'offering'],
            'domestic_services': ['maid payment', 'driver salary', 'gardener', 'security', 'domestic help'],
            'shopping': ['daraz', 'kapruka', 'softlogic', 'singer', 'purchase', 'shopping', 'pos'],
            'entertainment': ['netflix', 'spotify', 'iflix', 'cinema', 'movie', 'entertainment'],
            'insurance': ['insurance premium', 'policy payment', 'medical insurance', 'life insurance']
        }
        
        # Weak/context-dependent keywords - Sri Lankan context
        self.context_keywords = {
            'transfer_patterns': {
                'transfer_in': ['transfer in', 'deposit', 'cash deposit', 'mobile deposit', 'online transfer'],
                'transfer_out': ['transfer out', 'withdrawal', 'cash withdrawal', 'atm withdrawal', 'bank transfer']
            },
            'payment_patterns': {
                'bill_payment': ['bill payment', 'utility payment', 'loan payment'],
                'purchase_payment': ['pos payment', 'card payment', 'online payment']
            },
            'refund_patterns': {
                'merchant_refund': ['refund from', 'return credit', 'purchase return'],
                'service_refund': ['service refund', 'cancellation refund', 'booking refund']
            },
            'sri_lankan_banking': ['cdb', 'boc', 'peoples bank', 'hnb', 'commercial bank', 'sampath bank', 'nsb']
        }
        
        # Exception patterns (override amount-based classification) - Sri Lankan context
        self.exception_patterns = {
            'positive_expenses': [
                r'refund.*to.*(keells|cargills|daraz|kapruka)',  # Refunds to merchants
                r'cashback.*from.*(commercial.*bank|boc|hnb)',   # Bank cashback
                r'reversal.*charge',                             # Fee reversals
                r'credit.*note'                                  # Credit notes
            ],
            'negative_income': [
                r'salary.*deduction',                           # Salary deductions
                r'tax.*deducted',                              # Tax deductions
                r'epf.*deduction',                             # EPF deductions
                r'loan.*recovery'                              # Loan recoveries from salary
            ],
            'government_related': [
                r'(rto|passport|visa|license).*fee',           # Government fees
                r'tax.*(payment|settlement)',                   # Tax payments
                r'fine.*(traffic|court|municipal)'             # Government fines
            ],
            'religious_cultural': [
                r'(temple|kovil|church|mosque).*donation',     # Religious donations
                r'dana.*offering',                             # Buddhist offerings
                r'festival.*contribution'                      # Festival contributions
            ]
        }
    
    def _init_amount_patterns(self):
        """Initialize amount-based classification patterns"""
        
        # Typical income amount ranges - Sri Lankan context (LKR)
        self.income_amount_patterns = {
            'salary_range': (50000, 500000),    # Monthly salaries in LKR
            'freelance_range': (5000, 200000),  # Freelance payments in LKR
            'small_income': (100, 5000),        # Small income (cashback, etc.) in LKR
            'large_income': (200000, 2000000),  # Large income (bonuses, sales) in LKR
        }
        
        # Typical expense amount ranges with confidence adjustments - Sri Lankan context (LKR)
        self.expense_amount_patterns = {
            'micro_expense': (10, 500),         # Tea, snacks, etc. in LKR
            'small_expense': (500, 5000),       # Meals, bus fare, small purchases in LKR
            'medium_expense': (5000, 25000),    # Groceries, utilities in LKR
            'large_expense': (25000, 100000),   # Rent, car payments in LKR
            'major_expense': (100000, 500000),  # Major purchases in LKR
        }
        
        # Round number patterns - Sri Lankan context (LKR)
        self.round_number_patterns = {
            'salary_amounts': [50000, 75000, 100000, 125000, 150000, 200000, 250000, 300000, 400000, 500000],
            'bill_amounts': [2500, 5000, 7500, 10000, 12500, 15000, 20000, 25000],
            'subscription_amounts': [999, 1499, 1999, 2999, 4999, 9999]  # Common subscription amounts in LKR
        }
    
    def _init_temporal_patterns(self):
        """Initialize temporal patterns for classification - Sri Lankan context"""
        
        self.temporal_income_patterns = {
            'payday_patterns': {
                'monthly': [1, 15, 30, 31],  # Common payday dates
                'biweekly': 'every_14_days',
                'weekly': 'fridays',
                'sri_lankan_paydays': [25, 26, 27, 28]  # End of month paydays common in SL
            },
            'business_hours': {
                'hours': list(range(9, 17)),  # 9 AM to 5 PM
                'days': [0, 1, 2, 3, 4]  # Monday to Friday
            },
            'festival_bonuses': {
                'avurudu': [3, 4],  # April (New Year)
                'vesak': [4, 5],    # May (Vesak)
                'christmas': [12],   # December
                'diwali': [10, 11]  # October/November
            }
        }
        
        self.temporal_expense_patterns = {
            'bill_payment_dates': [1, 2, 3, 15, 28, 29, 30],  # Common bill due dates
            'weekend_spending': [5, 6],  # Saturday, Sunday
            'lunch_hours': [11, 12, 13, 14],
            'evening_dining': [17, 18, 19, 20, 21],
            'school_fee_months': [1, 4, 7, 10],  # Quarterly school fee payments
            'insurance_months': [1, 4, 7, 10],   # Quarterly insurance payments
            'festival_expenses': [3, 4, 5, 10, 11, 12]  # Festival season expenses
        }
    
    def _init_merchant_patterns(self):
        """Initialize merchant-based classification patterns"""
        
        # Known income sources - Sri Lankan context
        self.income_merchants = {
            'employers': ['payroll', 'hr dept', 'human resources', 'company ltd', 'pvt ltd'],
            'freelance_platforms': ['upwork', 'fiverr', 'freelancer', 'paypal', 'wise', 'remitly'],
            'investment_firms': ['cse', 'colombo stock exchange', 'unit trust', 'employee share'],
            'government': ['treasury', 'government payment', 'public service', 'ministry'],
            'financial': ['interest payment', 'dividend payment', 'cashback', 'fd interest'],
            'sri_lankan_banks': ['commercial bank', 'boc', 'peoples bank', 'hnb', 'sampath', 'cdb', 'nsb']
        }
        
        # Known expense merchants - Sri Lankan context
        self.expense_merchants = {
            'utilities': ['ceb', 'electricity board', 'water board', 'leco', 'gas company'],
            'telecom': ['dialog', 'mobitel', 'airtel', 'hutch', 'slt'],
            'retail': ['keells', 'cargills', 'food city', 'arpico', 'softlogic', 'singer'],
            'dining': ['kfc', 'mcdonalds', 'pizza hut', 'burger king', 'chinese dragon cafe'],
            'online': ['daraz', 'kapruka', 'wow.lk', 'ikman.lk'],
            'transport': ['ceypetco', 'ioc', 'shell', 'pickme', 'uber', 'kangaroo cabs'],
            'healthcare': ['nawaloka', 'asiri', 'lanka hospitals', 'durdans', 'osu sala'],
            'subscriptions': ['netflix', 'spotify', 'iflix', 'youtube premium']
        }
    
    def classify_transaction(self, transaction: PreprocessedTransaction, 
                           context: Dict[str, Any] = None) -> ClassifiedTransactionType:
        """
        Classify a single transaction with comprehensive analysis
        """
        description = transaction.description_cleaned.lower()
        amount = transaction.amount
        
        # Initialize analysis results
        analysis_results = {
            'amount_analysis': self._analyze_amount(amount),
            'keyword_analysis': self._analyze_keywords(description),
            'pattern_analysis': self._analyze_patterns(description, amount),
            'temporal_analysis': self._analyze_temporal(transaction),
            'merchant_analysis': self._analyze_merchant(description)
        }
        
        # Combine signals for final classification
        final_classification = self._combine_classification_signals(
            analysis_results, transaction, context
        )
        
        return ClassifiedTransactionType(
            transaction_id=transaction.id,
            transaction_type=final_classification['type'],
            classification_confidence=final_classification['confidence'],
            classification_reasoning=final_classification['reasoning'],
            amount_analysis=analysis_results['amount_analysis'],
            keyword_analysis=analysis_results['keyword_analysis'],
            pattern_analysis=analysis_results['pattern_analysis']
        )
    
    def _analyze_amount(self, amount: float) -> Dict[str, Any]:
        """Analyze transaction amount for classification signals"""
        abs_amount = abs(amount)
        
        analysis = {
            'raw_amount': amount,
            'absolute_amount': abs_amount,
            'is_positive': amount > 0,
            'is_negative': amount < 0,
            'is_round_number': abs_amount == round(abs_amount),
            'amount_category': self._categorize_amount(abs_amount),
            'confidence_modifier': 1.0,
            'signals': []
        }
        
        # Amount-based classification signals - Sri Lankan context
        if amount > 0:
            analysis['signals'].append('positive_amount_suggests_income')
            if abs_amount >= 50000:  # LKR threshold for salary indication
                analysis['signals'].append('large_positive_suggests_salary')
                analysis['confidence_modifier'] = 1.2
        else:
            analysis['signals'].append('negative_amount_suggests_expense')
            analysis['confidence_modifier'] = 1.1
        
        # Round number analysis - Sri Lankan context
        if analysis['is_round_number']:
            if abs_amount in [50000, 75000, 100000, 125000, 150000, 200000, 250000, 300000, 400000, 500000]:
                analysis['signals'].append('round_number_suggests_salary')
            elif abs_amount in [999, 1499, 1999, 2999, 4999, 9999]:
                analysis['signals'].append('subscription_amount_pattern')
        
        return analysis
    
    def _categorize_amount(self, amount: float) -> str:
        """Categorize transaction amount - Sri Lankan context (LKR)"""
        if amount < 500:
            return 'micro'
        elif amount < 5000:
            return 'small'
        elif amount < 25000:
            return 'medium'
        elif amount < 100000:
            return 'large'
        else:
            return 'major'
    
    def _analyze_keywords(self, description: str) -> Dict[str, Any]:
        """Analyze keywords in transaction description"""
        analysis = {
            'strong_income_signals': [],
            'strong_expense_signals': [],
            'context_signals': [],
            'confidence_score': 0.0,
            'primary_signal': None
        }
        
        # Check strong income keywords
        for category, keywords in self.strong_income_keywords.items():
            for keyword in keywords:
                if keyword in description:
                    analysis['strong_income_signals'].append({
                        'keyword': keyword,
                        'category': category,
                        'confidence': 0.9
                    })
        
        # Check strong expense keywords
        for category, keywords in self.strong_expense_keywords.items():
            for keyword in keywords:
                if keyword in description:
                    analysis['strong_expense_signals'].append({
                        'keyword': keyword,
                        'category': category,
                        'confidence': 0.9
                    })
        
        # Check context keywords - Sri Lankan patterns
        for category, keyword_dict in self.context_keywords.items():
            if isinstance(keyword_dict, dict):
                for subcategory, keywords in keyword_dict.items():
                    for keyword in keywords:
                        if keyword in description:
                            analysis['context_signals'].append({
                                'keyword': keyword,
                                'category': f"{category}_{subcategory}",
                                'confidence': 0.6
                            })
            else:
                for keyword in keyword_dict:
                    if keyword in description:
                        analysis['context_signals'].append({
                            'keyword': keyword,
                            'category': category,
                            'confidence': 0.6
                        })
        
        # Determine primary signal and confidence
        if analysis['strong_income_signals']:
            analysis['primary_signal'] = 'income'
            analysis['confidence_score'] = 0.9
        elif analysis['strong_expense_signals']:
            analysis['primary_signal'] = 'expense'
            analysis['confidence_score'] = 0.9
        elif analysis['context_signals']:
            analysis['primary_signal'] = 'context_dependent'
            analysis['confidence_score'] = 0.6
        
        return analysis
    
    def _analyze_patterns(self, description: str, amount: float) -> Dict[str, Any]:
        """Analyze patterns for special cases and exceptions"""
        analysis = {
            'pattern_matches': [],
            'exceptions': [],
            'confidence_adjustments': []
        }
        
        # Check exception patterns
        for exception_type, patterns in self.exception_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    analysis['exceptions'].append({
                        'type': exception_type,
                        'pattern': pattern,
                        'override': True
                    })
        
        # Check for transfer patterns - Sri Lankan context
        transfer_indicators = ['transfer', 'xfer', 'p2p', 'online banking', 'mobile banking', 'internet banking']
        if any(indicator in description for indicator in transfer_indicators):
            analysis['pattern_matches'].append({
                'type': 'transfer',
                'confidence_reduction': 0.2,
                'note': 'Transfers require additional context'
            })
        
        # Check for Sri Lankan specific patterns
        if any(bank in description for bank in ['cdb', 'boc', 'commercial bank', 'hnb', 'sampath']):
            analysis['pattern_matches'].append({
                'type': 'local_bank_transaction',
                'confidence_modifier': 1.1,
                'note': 'Local bank transaction'
            })
        
        return analysis
    
    def _analyze_temporal(self, transaction: PreprocessedTransaction) -> Dict[str, Any]:
        """Analyze temporal patterns - Sri Lankan context"""
        analysis = {
            'time_signals': [],
            'confidence_modifier': 1.0
        }
        
        day_of_month = transaction.day
        day_of_week = transaction.day_of_week
        month = transaction.month
        
        # Check for payday patterns
        if day_of_month in [1, 15, 30, 31]:
            analysis['time_signals'].append('potential_payday')
            analysis['confidence_modifier'] = 1.1
        
        # Check for Sri Lankan specific payday patterns
        if day_of_month in [25, 26, 27, 28]:
            analysis['time_signals'].append('sri_lankan_month_end_payday')
            analysis['confidence_modifier'] = 1.15
        
        # Check for weekend spending
        if day_of_week in [5, 6]:  # Saturday, Sunday
            analysis['time_signals'].append('weekend_transaction')
        
        # Check for festival seasons (higher expense likelihood)
        if month in [3, 4, 5, 10, 11, 12]:  # Festival months
            analysis['time_signals'].append('festival_season')
            if day_of_week in [5, 6]:  # Weekend during festival season
                analysis['confidence_modifier'] = 1.1
        
        # Check for quarterly patterns (school fees, insurance)
        if month in [1, 4, 7, 10] and day_of_month <= 15:
            analysis['time_signals'].append('quarterly_payment_period')
        
        return analysis
    
    def _analyze_merchant(self, description: str) -> Dict[str, Any]:
        """Analyze merchant patterns"""
        analysis = {
            'merchant_signals': [],
            'merchant_type': None,
            'confidence': 0.0
        }
        
        # Check known income merchants
        for category, merchants in self.income_merchants.items():
            for merchant in merchants:
                if merchant in description:
                    analysis['merchant_signals'].append({
                        'merchant': merchant,
                        'type': 'income',
                        'category': category,
                        'confidence': 0.85
                    })
                    analysis['merchant_type'] = 'income'
                    analysis['confidence'] = 0.85
        
        # Check known expense merchants
        for category, merchants in self.expense_merchants.items():
            for merchant in merchants:
                if merchant in description:
                    analysis['merchant_signals'].append({
                        'merchant': merchant,
                        'type': 'expense',
                        'category': category,
                        'confidence': 0.85
                    })
                    analysis['merchant_type'] = 'expense'
                    analysis['confidence'] = 0.85
        
        return analysis
    
    def _combine_classification_signals(self, analysis_results: Dict[str, Any], 
                                      transaction: PreprocessedTransaction,
                                      context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Combine all classification signals for final decision"""
        
        signals = []
        confidence_scores = []
        
        # Amount signal
        amount_analysis = analysis_results['amount_analysis']
        if amount_analysis['is_positive']:
            signals.append(('income', 0.7 * amount_analysis['confidence_modifier']))
        else:
            signals.append(('expense', 0.8 * amount_analysis['confidence_modifier']))
        
        # Keyword signal
        keyword_analysis = analysis_results['keyword_analysis']
        if keyword_analysis['primary_signal'] == 'income':
            signals.append(('income', keyword_analysis['confidence_score']))
        elif keyword_analysis['primary_signal'] == 'expense':
            signals.append(('expense', keyword_analysis['confidence_score']))
        
        # Merchant signal
        merchant_analysis = analysis_results['merchant_analysis']
        if merchant_analysis['merchant_type']:
            signals.append((merchant_analysis['merchant_type'], merchant_analysis['confidence']))
        
        # Exception overrides
        pattern_analysis = analysis_results['pattern_analysis']
        for exception in pattern_analysis['exceptions']:
            if exception['override']:
                if 'positive_expenses' in exception['type']:
                    return {
                        'type': 'expense',
                        'confidence': 0.95,
                        'reasoning': f"Exception pattern: {exception['pattern']}"
                    }
                elif 'negative_income' in exception['type']:
                    return {
                        'type': 'income',
                        'confidence': 0.95,
                        'reasoning': f"Exception pattern: {exception['pattern']}"
                    }
        
        # Combine signals
        if not signals:
            return {
                'type': 'expense',  # Default to expense if no signals
                'confidence': 0.3,
                'reasoning': 'No clear signals found, defaulting to expense'
            }
        
        # Weight and combine signals
        income_score = sum(conf for typ, conf in signals if typ == 'income')
        expense_score = sum(conf for typ, conf in signals if typ == 'expense')
        
        if income_score > expense_score:
            final_type = 'income'
            confidence = min(income_score / (income_score + expense_score), 0.98)
        else:
            final_type = 'expense'
            confidence = min(expense_score / (income_score + expense_score), 0.98)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(signals, analysis_results)
        
        return {
            'type': final_type,
            'confidence': confidence,
            'reasoning': reasoning
        }
    
    def _generate_reasoning(self, signals: List[Tuple[str, float]], 
                          analysis_results: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for classification"""
        reasons = []
        
        # Amount reasoning - Sri Lankan context
        amount_analysis = analysis_results['amount_analysis']
        if amount_analysis['is_positive'] and amount_analysis['absolute_amount'] >= 50000:  # LKR threshold
            reasons.append("Large positive amount suggests salary/income")
        elif amount_analysis['is_negative']:
            reasons.append("Negative amount indicates expense")
        
        # Keyword reasoning
        keyword_analysis = analysis_results['keyword_analysis']
        if keyword_analysis['strong_income_signals']:
            signal = keyword_analysis['strong_income_signals'][0]
            reasons.append(f"Income keyword '{signal['keyword']}' found")
        elif keyword_analysis['strong_expense_signals']:
            signal = keyword_analysis['strong_expense_signals'][0]
            reasons.append(f"Expense keyword '{signal['keyword']}' found")
        
        # Merchant reasoning
        merchant_analysis = analysis_results['merchant_analysis']
        if merchant_analysis['merchant_signals']:
            signal = merchant_analysis['merchant_signals'][0]
            reasons.append(f"Known {signal['type']} merchant '{signal['merchant']}'")
        
        return "; ".join(reasons) if reasons else "Classification based on amount pattern"
    
    def process(self, input_data: TransactionClassificationInput) -> TransactionClassificationOutput:
        """Process transactions for income/expense classification"""
        start_time = datetime.now()
        logger.info(f"Classifying {len(input_data.preprocessed_transactions)} transactions")
        
        classified_transactions = []
        classification_stats = {
            'total_processed': len(input_data.preprocessed_transactions),
            'income_count': 0,
            'expense_count': 0,
            'high_confidence_count': 0,
            'low_confidence_count': 0,
            'average_confidence': 0.0,
            'processing_time': 0.0,
            'method_usage': Counter()
        }
        
        total_confidence = 0.0
        
        for transaction in input_data.preprocessed_transactions:
            try:
                classified = self.classify_transaction(transaction)
                classified_transactions.append(classified)
                
                # Update statistics
                if classified.transaction_type == 'income':
                    classification_stats['income_count'] += 1
                else:
                    classification_stats['expense_count'] += 1
                
                if classified.classification_confidence >= 0.8:
                    classification_stats['high_confidence_count'] += 1
                elif classified.classification_confidence < 0.5:
                    classification_stats['low_confidence_count'] += 1
                
                total_confidence += classified.classification_confidence
                
            except Exception as e:
                logger.error(f"Error classifying transaction {transaction.id}: {e}")
                # Create fallback classification
                fallback = ClassifiedTransactionType(
                    transaction_id=transaction.id,
                    transaction_type='expense' if transaction.amount < 0 else 'income',
                    classification_confidence=0.3,
                    classification_reasoning=f"Fallback classification due to error: {e}",
                    amount_analysis={},
                    keyword_analysis={},
                    pattern_analysis={}
                )
                classified_transactions.append(fallback)
        
        # Calculate final statistics
        processing_time = (datetime.now() - start_time).total_seconds()
        classification_stats['processing_time'] = processing_time
        classification_stats['average_confidence'] = (
            total_confidence / len(classified_transactions) if classified_transactions else 0.0
        )
        
        logger.info(
            f"Classification completed in {processing_time:.2f}s. "
            f"Income: {classification_stats['income_count']}, "
            f"Expenses: {classification_stats['expense_count']}, "
            f"Avg confidence: {classification_stats['average_confidence']:.2f}"
        )
        
        return TransactionClassificationOutput(
            classified_transactions=classified_transactions,
            classification_stats=classification_stats,
            learned_patterns=dict(self.learned_patterns)
        )
    
    def update_learned_patterns(self, transaction_id: str, correct_type: str):
        """Update learned patterns based on user feedback"""
        # This would be called when user corrects a classification
        # Implementation would update the learned_patterns based on the correction
        pass
