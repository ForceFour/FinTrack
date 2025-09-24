"""
Classification Agent
Role: Comprehensive transaction classification combining category prediction and transaction type classification
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import logging
import re
from collections import Counter
from datetime import datetime
from pydantic import BaseModel, Field

from ..schemas.transaction_schemas import (
    MerchantTransaction,
    ClassifiedTransaction,
    TransactionCategory,
    PreprocessedTransaction
)
from ..models.category_classifier import CategoryClassifier
from ..utils.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class ClassifierAgentInput(BaseModel):
    """Input schema for Classifier Agent"""
    merchant_transactions: List[MerchantTransaction] = Field(description="Transactions with merchant info")
    historical_data: Optional[List[MerchantTransaction]] = Field(None, description="Historical transactions for context")


class ClassifierAgentOutput(BaseModel):
    """Output schema for Classifier Agent"""
    classified_transactions: List[ClassifiedTransaction] = Field(description="Fully classified transactions")
    confidence_scores: List[float] = Field(description="Prediction confidence scores")
    classification_stats: Dict[str, Any] = Field(description="Classification performance statistics")


class ClassifierAgent:
    """
    Classification Agent combining category prediction and transaction type classification

    Responsibilities:
    - Classify transaction categories (Food, Transport, etc.) using ML and rules
    - Determine transaction type (Income vs Expense) with high accuracy
    - Use ensemble methods combining multiple signals
    - Handle Sri Lankan context and merchants
    - Provide comprehensive confidence scoring and reasoning
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.classifier = CategoryClassifier()
        self.feature_engineer = FeatureEngineer()

        # Configuration parameters
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.default_category = self.config.get('default_category', 'miscellaneous')

        # Initialize classification components
        self._init_category_mapping()
        self._init_transaction_type_patterns()
        self._init_temporal_patterns()
        self._init_ensemble_components()

        # Feature tracking
        self.feature_names = []
        self.feature_importance = {}

    def _init_category_mapping(self):
        """Initialize category mapping rules for Sri Lankan merchants"""
        self.merchant_category_mapping = {
            # Food & Dining
            'kfc': TransactionCategory.FOOD_DINING,
            'mcdonalds': TransactionCategory.FOOD_DINING,
            'pizza hut': TransactionCategory.FOOD_DINING,
            'dominos': TransactionCategory.FOOD_DINING,
            'subway': TransactionCategory.FOOD_DINING,
            'chinese dragon': TransactionCategory.FOOD_DINING,
            'hotel galadari': TransactionCategory.FOOD_DINING,
            'cinnamon grand': TransactionCategory.FOOD_DINING,

            # Grocery & Retail
            'keells': TransactionCategory.GROCERIES,
            'keells super': TransactionCategory.GROCERIES,
            'cargills': TransactionCategory.GROCERIES,
            'cargills food city': TransactionCategory.GROCERIES,
            'food city': TransactionCategory.GROCERIES,
            'laugfs super': TransactionCategory.GROCERIES,
            'arpico supercenter': TransactionCategory.SHOPPING,
            'softlogic': TransactionCategory.SHOPPING,
            'singer': TransactionCategory.SHOPPING,
            'abans': TransactionCategory.SHOPPING,

            # Transportation & Fuel
            'uber': TransactionCategory.TRANSPORTATION,
            'pickme': TransactionCategory.TRANSPORTATION,
            'ceypetco': TransactionCategory.TRANSPORTATION,
            'indian oil': TransactionCategory.TRANSPORTATION,
            'ioc': TransactionCategory.TRANSPORTATION,
            'shell': TransactionCategory.TRANSPORTATION,

            # Utilities & Services
            'dialog': TransactionCategory.UTILITIES,
            'mobitel': TransactionCategory.UTILITIES,
            'airtel': TransactionCategory.UTILITIES,
            'hutch': TransactionCategory.UTILITIES,
            'ceb': TransactionCategory.UTILITIES,
            'nwsdb': TransactionCategory.UTILITIES,
            'commercial bank': TransactionCategory.UTILITIES,
            'peoples bank': TransactionCategory.UTILITIES,
            'bank of ceylon': TransactionCategory.UTILITIES,
            'sampath bank': TransactionCategory.UTILITIES,

            # E-commerce & Online
            'daraz': TransactionCategory.SHOPPING,
            'ikman': TransactionCategory.SHOPPING,
            'netflix': TransactionCategory.ENTERTAINMENT,
            'spotify': TransactionCategory.ENTERTAINMENT,
            'youtube premium': TransactionCategory.ENTERTAINMENT,

            # Healthcare
            'nawaloka': TransactionCategory.HEALTHCARE,
            'asiri hospitals': TransactionCategory.HEALTHCARE,
            'osu sala': TransactionCategory.HEALTHCARE,
        }

        # Amount-based category hints (in LKR)
        self.amount_category_hints = {
            (0, 500): [TransactionCategory.FOOD_DINING, TransactionCategory.TRANSPORTATION],
            (500, 2000): [TransactionCategory.FOOD_DINING, TransactionCategory.GROCERIES],
            (2000, 10000): [TransactionCategory.GROCERIES, TransactionCategory.SHOPPING],
            (10000, 50000): [TransactionCategory.UTILITIES, TransactionCategory.HEALTHCARE],
            (50000, 200000): [TransactionCategory.TRAVEL, TransactionCategory.HEALTHCARE],
            (200000, float('inf')): [TransactionCategory.TRAVEL, TransactionCategory.EDUCATION],
        }

        # Enhanced keyword mapping for categories
        self.category_keywords = {
            TransactionCategory.FOOD_DINING: {
                'high_weight': ['restaurant', 'cafe', 'hotel', 'kfc', 'mcdonalds', 'pizza'],
                'medium_weight': ['food', 'dining', 'coffee', 'burger', 'rice', 'curry'],
                'low_weight': ['eat', 'meal', 'lunch', 'dinner', 'breakfast']
            },
            TransactionCategory.GROCERIES: {
                'high_weight': ['keells', 'cargills', 'food city', 'laugfs', 'arpico'],
                'medium_weight': ['super', 'market', 'grocery'],
                'low_weight': ['supplies', 'essentials']
            },
            TransactionCategory.TRANSPORTATION: {
                'high_weight': ['uber', 'pickme', 'taxi', 'ceypetco', 'ioc', 'shell'],
                'medium_weight': ['fuel', 'petrol', 'diesel', 'transport', 'bus'],
                'low_weight': ['parking', 'toll', 'car']
            },
            TransactionCategory.UTILITIES: {
                'high_weight': ['dialog', 'mobitel', 'airtel', 'ceb', 'nwsdb'],
                'medium_weight': ['electricity', 'water', 'internet', 'phone', 'bill'],
                'low_weight': ['utility', 'service']
            },
            TransactionCategory.ENTERTAINMENT: {
                'high_weight': ['netflix', 'spotify', 'youtube'],
                'medium_weight': ['movie', 'cinema', 'game', 'entertainment'],
                'low_weight': ['subscription', 'streaming']
            },
            TransactionCategory.HEALTHCARE: {
                'high_weight': ['nawaloka', 'asiri', 'hospital', 'doctor'],
                'medium_weight': ['medical', 'pharmacy', 'health', 'clinic'],
                'low_weight': ['medicine', 'treatment']
            },
            TransactionCategory.SHOPPING: {
                'high_weight': ['daraz', 'ikman', 'singer', 'abans', 'softlogic'],
                'medium_weight': ['shop', 'store', 'buy', 'purchase'],
                'low_weight': ['retail', 'goods']
            }
        }

    def _init_transaction_type_patterns(self):
        """Initialize patterns for income vs expense classification"""

        # Strong income indicators
        self.income_keywords = {
            'salary_payroll': ['salary', 'payroll', 'direct deposit', 'wages', 'monthly salary'],
            'freelance': ['freelance', 'contractor', 'consulting', 'client payment'],
            'investment': ['dividend', 'interest', 'investment', 'capital gains'],
            'business': ['revenue', 'sales', 'business income', 'commission', 'royalty'],
            'government': ['pension', 'allowance', 'government payment'],
            'other': ['bonus', 'gift', 'cashback', 'reward', 'reimbursement', 'refund'],
            'sri_lankan': ['epf', 'etf', 'gratuity', 'festival bonus', 'overtime']
        }

        # Strong expense indicators
        self.expense_keywords = {
            'utilities': ['ceb', 'electricity', 'water board', 'gas bill'],
            'telecom': ['dialog', 'mobitel', 'airtel', 'hutch', 'internet bill'],
            'fuel': ['ceypetco', 'ioc', 'shell', 'petrol', 'diesel'],
            'food': ['restaurant', 'hotel', 'kfc', 'mcdonalds', 'grocery'],
            'healthcare': ['nawaloka', 'asiri', 'hospital', 'doctor', 'pharmacy'],
            'education': ['school fee', 'tuition', 'university'],
            'shopping': ['daraz', 'purchase', 'shopping', 'pos'],
            'banking': ['bank charge', 'atm fee', 'service charge'],
            'religious': ['temple', 'donation', 'dana', 'offering']
        }

        # Income amount patterns (LKR)
        self.income_amount_patterns = {
            'salary_range': (50000, 500000),
            'freelance_range': (5000, 200000),
            'small_income': (100, 5000),
            'large_income': (200000, 2000000)
        }

        # Common salary amounts in LKR
        self.salary_amounts = [50000, 75000, 100000, 125000, 150000, 200000, 250000, 300000, 400000, 500000]

    def _init_temporal_patterns(self):
        """Initialize temporal patterns for Sri Lankan context"""

        # Payday patterns
        self.payday_dates = [1, 15, 25, 26, 27, 28, 30, 31]

        # Bill payment patterns
        self.bill_payment_dates = [1, 2, 3, 15, 28, 29, 30]

        # Festival seasons (higher expenses)
        self.festival_months = [3, 4, 5, 10, 11, 12]  # Avurudu, Vesak, Christmas seasons

        # School fee months
        self.school_fee_months = [1, 4, 7, 10]  # Quarterly payments

    def _init_ensemble_components(self):
        """Initialize ensemble classification components"""

        # Ensemble weights for category classification
        self.category_ensemble_weights = {
            'ml_model': 0.4,
            'merchant_rules': 0.3,
            'amount_heuristics': 0.15,
            'temporal_patterns': 0.1,
            'keywords': 0.05
        }

        # Ensemble weights for transaction type classification
        self.type_ensemble_weights = {
            'amount_signal': 0.35,
            'keyword_signal': 0.35,
            'merchant_signal': 0.20,
            'temporal_signal': 0.10
        }

        # Confidence adjustments
        self.confidence_boosters = {
            'merchant_exact_match': 1.2,
            'multiple_signals_agree': 1.15,
            'high_amount_confidence': 1.1,
            'strong_keyword_match': 1.1
        }

        self.confidence_penalties = {
            'conflicting_signals': 0.8,
            'low_merchant_confidence': 0.9,
            'unusual_amount': 0.85,
            'generic_description': 0.9
        }

    def engineer_features(self, transactions: List[MerchantTransaction]) -> np.ndarray:
        """Engineer comprehensive features for ML classification"""
        logger.debug(f"Engineering features for {len(transactions)} transactions")

        features = []

        for txn in transactions:
            # Basic numeric features
            amount = abs(txn.amount)
            txn_features = [
                amount,
                np.log1p(amount),
                amount ** 0.5,
                1 if amount > 100 else 0,
                1 if amount < 10 else 0,
                1 if txn.amount < 0 else 0,
                1 if txn.transaction_type.value == 'income' else 0,
                1 if txn.transaction_type.value == 'expense' else 0
            ]

            # Temporal features
            txn_features.extend([
                txn.year % 100,
                txn.month,
                txn.day,
                txn.day_of_week,
                1 if txn.day_of_week >= 5 else 0,  # Weekend
                1 if txn.month in self.festival_months else 0,  # Festival season
                1 if txn.day in self.payday_dates else 0,  # Potential payday
                np.sin(2 * np.pi * txn.month / 12),
                np.cos(2 * np.pi * txn.month / 12)
            ])

            # Merchant features
            merchant = (txn.merchant_standardized or '').lower()
            txn_features.extend([
                1 if txn.is_merchant_known else 0,
                1 if merchant in self.merchant_category_mapping else 0,
                len(merchant.split()) if merchant else 0
            ])

            # Description features
            desc = txn.description_cleaned.lower()
            txn_features.extend([
                len(desc),
                desc.count(' '),
                1 if any(keyword in desc for keywords in self.income_keywords.values()
                        for keyword in keywords) else 0,
                1 if any(keyword in desc for keywords in self.expense_keywords.values()
                        for keyword in keywords) else 0
            ])

            features.append(txn_features)

        return np.array(features, dtype=np.float32)

    def predict_category(self, transaction: MerchantTransaction, features: np.ndarray) -> Tuple[str, float, Dict[str, float]]:
        """Predict transaction category using ensemble methods"""

        ensemble_results = {}

        # Signal 1: Merchant-based prediction
        merchant_pred, merchant_conf = self._predict_category_from_merchant(transaction)
        if merchant_pred:
            ensemble_results['merchant'] = (merchant_pred, merchant_conf)

        # Signal 2: Keyword-based prediction
        keyword_pred, keyword_conf = self._predict_category_from_keywords(transaction)
        if keyword_pred:
            ensemble_results['keywords'] = (keyword_pred, keyword_conf)

        # Signal 3: Amount-based heuristics
        amount_pred, amount_conf = self._predict_category_from_amount(transaction)
        if amount_pred:
            ensemble_results['amount'] = (amount_pred, amount_conf)

        # Signal 4: ML model (if available and trained)
        if self.classifier.is_trained and features.size > 0:
            try:
                ml_preds, ml_confs = self.classifier.predict(features.reshape(1, -1))
                if ml_preds and ml_confs:
                    ensemble_results['ml_model'] = (ml_preds[0], ml_confs[0])
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")

        # Combine ensemble signals
        return self._combine_category_signals(ensemble_results, transaction)

    def _predict_category_from_merchant(self, transaction: MerchantTransaction) -> Tuple[Optional[str], float]:
        """Predict category from merchant information"""
        if not transaction.merchant_standardized:
            return None, 0.0

        merchant_lower = transaction.merchant_standardized.lower()

        # Direct merchant mapping
        if merchant_lower in self.merchant_category_mapping:
            return self.merchant_category_mapping[merchant_lower].value, 0.95

        # Merchant category from NER agent
        if transaction.merchant_category:
            confidence = transaction.metadata.get('merchant_extraction_confidence', 0.8)
            return transaction.merchant_category, min(0.85 * (1 + confidence * 0.2), 0.95)

        return None, 0.0

    def _predict_category_from_keywords(self, transaction: MerchantTransaction) -> Tuple[Optional[str], float]:
        """Predict category from keywords with weighted scoring"""
        desc = transaction.description_cleaned.lower()
        merchant = (transaction.merchant_standardized or '').lower()
        combined_text = f"{desc} {merchant}".strip()

        if not combined_text:
            return None, 0.0

        category_scores = {}

        for category, weight_groups in self.category_keywords.items():
            score = 0.0

            # High weight keywords
            for keyword in weight_groups.get('high_weight', []):
                if keyword in combined_text:
                    score += 1.0

            # Medium weight keywords
            for keyword in weight_groups.get('medium_weight', []):
                if keyword in combined_text:
                    score += 0.6

            # Low weight keywords
            for keyword in weight_groups.get('low_weight', []):
                if keyword in combined_text:
                    score += 0.3

            if score > 0:
                category_scores[category] = score

        if category_scores:
            best_category = max(category_scores.keys(), key=lambda x: category_scores[x])
            best_score = category_scores[best_category]
            confidence = min(best_score * 0.4, 0.8)
            return best_category.value, confidence

        return None, 0.0

    def _predict_category_from_amount(self, transaction: MerchantTransaction) -> Tuple[Optional[str], float]:
        """Predict category from amount patterns"""
        amount = abs(transaction.amount)

        # Find matching amount range
        for (min_amt, max_amt), categories in self.amount_category_hints.items():
            if min_amt <= amount < max_amt:
                if categories:
                    return categories[0].value, 0.3  # Low confidence for amount-only

        return None, 0.0

    def _combine_category_signals(self, ensemble_results: Dict[str, Tuple[str, float]],
                                 transaction: MerchantTransaction) -> Tuple[str, float, Dict[str, float]]:
        """Combine category prediction signals"""
        if not ensemble_results:
            return self.default_category, 0.1, {}

        # Weight and combine signals
        category_votes = {}
        total_weight = 0.0

        for signal_name, (prediction, confidence) in ensemble_results.items():
            weight = self.category_ensemble_weights.get(signal_name, 0.1)
            weighted_vote = confidence * weight
            category_votes[prediction] = category_votes.get(prediction, 0.0) + weighted_vote
            total_weight += weight

        # Find best prediction
        best_category = max(category_votes.keys(), key=lambda x: category_votes[x])
        raw_confidence = category_votes[best_category] / total_weight if total_weight > 0 else 0.1

        # Apply confidence adjustments
        adjusted_confidence = self._apply_category_confidence_adjustments(
            best_category, raw_confidence, ensemble_results, transaction
        )

        # Create probability distribution
        proba_dist = {}
        total_votes = sum(category_votes.values())
        for category in category_votes:
            proba_dist[category] = category_votes[category] / total_votes

        return best_category, adjusted_confidence, proba_dist

    def _apply_category_confidence_adjustments(self, prediction: str, base_confidence: float,
                                             ensemble_results: Dict, transaction: MerchantTransaction) -> float:
        """Apply confidence adjustments for category prediction"""
        adjusted_confidence = base_confidence

        # Multiple signals agreement
        predictions = [pred for pred, conf in ensemble_results.values()]
        agreement = sum(1 for p in predictions if p == prediction) / len(predictions)

        if agreement >= 0.8:
            adjusted_confidence *= self.confidence_boosters['multiple_signals_agree']

        # Merchant exact match
        if 'merchant' in ensemble_results and ensemble_results['merchant'][0] == prediction:
            adjusted_confidence *= self.confidence_boosters['merchant_exact_match']

        return min(adjusted_confidence, 0.98)

    def predict_transaction_type(self, transaction: MerchantTransaction) -> Tuple[str, float, str]:
        """Predict if transaction is income or expense with reasoning"""

        amount = transaction.amount
        desc = transaction.description_cleaned.lower()
        signals = []

        # Amount signal
        amount_signal = self._analyze_amount_for_type(amount)
        signals.append(('amount', amount_signal['type'], amount_signal['confidence']))

        # Keyword signal
        keyword_signal = self._analyze_keywords_for_type(desc)
        if keyword_signal['type']:
            signals.append(('keyword', keyword_signal['type'], keyword_signal['confidence']))

        # Merchant signal
        merchant_signal = self._analyze_merchant_for_type(desc)
        if merchant_signal['type']:
            signals.append(('merchant', merchant_signal['type'], merchant_signal['confidence']))

        # Temporal signal
        temporal_signal = self._analyze_temporal_for_type(transaction)
        if temporal_signal['type']:
            signals.append(('temporal', temporal_signal['type'], temporal_signal['confidence']))

        # Combine signals
        return self._combine_type_signals(signals, transaction)

    def _analyze_amount_for_type(self, amount: float) -> Dict[str, Any]:
        """Analyze amount for transaction type classification"""
        abs_amount = abs(amount)

        if amount > 0:
            if abs_amount in self.salary_amounts:
                return {'type': 'income', 'confidence': 0.85, 'reason': 'Salary amount pattern'}
            elif abs_amount >= 50000:
                return {'type': 'income', 'confidence': 0.75, 'reason': 'Large positive amount'}
            else:
                return {'type': 'income', 'confidence': 0.65, 'reason': 'Positive amount'}
        else:
            return {'type': 'expense', 'confidence': 0.80, 'reason': 'Negative amount'}

    def _analyze_keywords_for_type(self, description: str) -> Dict[str, Any]:
        """Analyze keywords for transaction type"""

        # Check income keywords
        for category, keywords in self.income_keywords.items():
            for keyword in keywords:
                if keyword in description:
                    return {'type': 'income', 'confidence': 0.90, 'reason': f'Income keyword: {keyword}'}

        # Check expense keywords
        for category, keywords in self.expense_keywords.items():
            for keyword in keywords:
                if keyword in description:
                    return {'type': 'expense', 'confidence': 0.85, 'reason': f'Expense keyword: {keyword}'}

        return {'type': None, 'confidence': 0.0, 'reason': 'No clear keywords'}

    def _analyze_merchant_for_type(self, description: str) -> Dict[str, Any]:
        """Analyze merchant patterns for transaction type"""

        # Check for known expense merchants
        expense_merchants = ['keells', 'cargills', 'dialog', 'mobitel', 'ceypetco', 'uber']
        for merchant in expense_merchants:
            if merchant in description:
                return {'type': 'expense', 'confidence': 0.85, 'reason': f'Known expense merchant: {merchant}'}

        # Check for income sources
        income_sources = ['payroll', 'salary', 'commercial bank', 'boc']
        for source in income_sources:
            if source in description:
                return {'type': 'income', 'confidence': 0.80, 'reason': f'Known income source: {source}'}

        return {'type': None, 'confidence': 0.0, 'reason': 'Unknown merchant pattern'}

    def _analyze_temporal_for_type(self, transaction: MerchantTransaction) -> Dict[str, Any]:
        """Analyze temporal patterns for transaction type"""

        day = transaction.day
        month = transaction.month

        # Payday patterns
        if day in self.payday_dates:
            return {'type': 'income', 'confidence': 0.65, 'reason': 'Potential payday date'}

        # Festival seasons (more expenses)
        if month in self.festival_months:
            return {'type': 'expense', 'confidence': 0.55, 'reason': 'Festival season'}

        return {'type': None, 'confidence': 0.0, 'reason': 'No temporal pattern'}

    def _combine_type_signals(self, signals: List[Tuple[str, str, float]],
                             transaction: MerchantTransaction) -> Tuple[str, float, str]:
        """Combine transaction type signals"""

        if not signals:
            return 'expense', 0.3, 'Default classification (no signals)'

        # Weight signals
        income_score = 0.0
        expense_score = 0.0
        reasoning_parts = []

        for signal_name, signal_type, confidence in signals:
            weight = self.type_ensemble_weights.get(f'{signal_name}_signal', 0.1)
            weighted_score = confidence * weight

            if signal_type == 'income':
                income_score += weighted_score
            else:
                expense_score += weighted_score

            reasoning_parts.append(f"{signal_name}: {signal_type} ({confidence:.2f})")

        # Determine final type
        if income_score > expense_score:
            final_type = 'income'
            confidence = min(income_score / (income_score + expense_score), 0.98)
        else:
            final_type = 'expense'
            confidence = min(expense_score / (income_score + expense_score), 0.98)

        reasoning = "; ".join(reasoning_parts)

        return final_type, confidence, reasoning

    def process(self, input_data: ClassifierAgentInput) -> ClassifierAgentOutput:
        """Process transactions for comprehensive classification"""
        start_time = datetime.now()
        logger.info(f"Processing {len(input_data.merchant_transactions)} transactions for unified classification")

        transactions = input_data.merchant_transactions
        if not transactions:
            return ClassifierAgentOutput(
                classified_transactions=[],
                confidence_scores=[],
                classification_stats={'error': 'No transactions provided'}
            )

        # Engineer features for ML
        try:
            features = self.engineer_features(transactions)
            logger.debug(f"Engineered features shape: {features.shape}")
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            features = np.array([])

        # Classify transactions
        classified_transactions = []
        confidence_scores = []

        for i, txn in enumerate(transactions):
            try:
                # Get features for this transaction
                txn_features = features[i] if features.size > 0 else np.array([])

                # Predict category
                category, category_conf, category_proba = self.predict_category(txn, txn_features)

                # Predict transaction type
                txn_type, type_conf, type_reasoning = self.predict_transaction_type(txn)

                # Create classified transaction
                classified_txn = ClassifiedTransaction(
                    # Base transaction fields
                    id=txn.id,
                    date=txn.date,
                    year=txn.year,
                    month=txn.month,
                    day=txn.day,
                    day_of_week=txn.day_of_week,
                    amount=txn.amount,
                    payment_method=txn.payment_method,
                    description_cleaned=txn.description_cleaned,
                    has_discount=txn.has_discount,
                    discount_percentage=txn.discount_percentage,
                    transaction_type=txn.transaction_type,
                    metadata=txn.metadata.copy(),
                    merchant_name=txn.merchant_name,
                    merchant_standardized=txn.merchant_standardized,
                    merchant_category=txn.merchant_category,
                    is_merchant_known=txn.is_merchant_known,

                    # Classification results
                    predicted_category=TransactionCategory(category),
                    prediction_confidence=category_conf,
                    category_probabilities=category_proba
                )

                # Add unified classification metadata
                classified_txn.metadata.update({
                    'unified_classification': True,
                    'category_prediction': category,
                    'category_confidence': category_conf,
                    'transaction_type_prediction': txn_type,
                    'transaction_type_confidence': type_conf,
                    'transaction_type_reasoning': type_reasoning,
                    'classification_timestamp': datetime.now().isoformat(),
                    'overall_confidence': (category_conf + type_conf) / 2
                })

                classified_transactions.append(classified_txn)
                confidence_scores.append(classified_txn.metadata['overall_confidence'])

            except Exception as e:
                logger.error(f"Error classifying transaction {i}: {e}")
                # Create fallback classification
                fallback = self._create_fallback_classification(txn, str(e))
                classified_transactions.append(fallback)
                confidence_scores.append(0.1)

        # Generate statistics
        processing_time = (datetime.now() - start_time).total_seconds()
        classification_stats = self._generate_unified_stats(
            classified_transactions, confidence_scores, processing_time
        )

        logger.info(
            f"Unified classification completed in {processing_time:.2f}s. "
            f"Average confidence: {classification_stats['average_confidence']:.2f}"
        )

        return ClassifierAgentOutput(
            classified_transactions=classified_transactions,
            confidence_scores=confidence_scores,
            classification_stats=classification_stats
        )

    def _create_fallback_classification(self, txn: MerchantTransaction, error: str) -> ClassifiedTransaction:
        """Create fallback classification when errors occur"""
        return ClassifiedTransaction(
            id=txn.id,
            date=txn.date,
            year=txn.year,
            month=txn.month,
            day=txn.day,
            day_of_week=txn.day_of_week,
            amount=txn.amount,
            payment_method=txn.payment_method,
            description_cleaned=txn.description_cleaned,
            has_discount=txn.has_discount,
            discount_percentage=txn.discount_percentage,
            transaction_type=txn.transaction_type,
            metadata=txn.metadata.copy(),
            merchant_name=txn.merchant_name,
            merchant_standardized=txn.merchant_standardized,
            merchant_category=txn.merchant_category,
            is_merchant_known=txn.is_merchant_known,
            predicted_category=TransactionCategory.MISCELLANEOUS,
            prediction_confidence=0.1,
            category_probabilities={},
            metadata_extra={'classification_error': error}
        )

    def _generate_unified_stats(self, classified_transactions: List[ClassifiedTransaction],
                               confidence_scores: List[float], processing_time: float) -> Dict[str, Any]:
        """Generate comprehensive classification statistics"""

        category_counts = Counter([t.predicted_category.value for t in classified_transactions])
        type_counts = Counter([t.metadata.get('transaction_type_prediction', 'unknown')
                              for t in classified_transactions])

        return {
            'total_processed': len(classified_transactions),
            'processing_time': processing_time,
            'processing_rate': len(classified_transactions) / processing_time if processing_time > 0 else 0,
            'average_confidence': float(np.mean(confidence_scores)) if confidence_scores else 0.0,
            'median_confidence': float(np.median(confidence_scores)) if confidence_scores else 0.0,
            'high_confidence_count': sum(1 for c in confidence_scores if c >= 0.8),
            'medium_confidence_count': sum(1 for c in confidence_scores if 0.5 <= c < 0.8),
            'low_confidence_count': sum(1 for c in confidence_scores if c < 0.5),
            'category_distribution': dict(category_counts),
            'transaction_type_distribution': dict(type_counts),
            'classification_method': 'unified_ensemble',
            'feature_count': len(self.feature_names) if hasattr(self, 'feature_names') else 0
        }


# Maintain backward compatibility
UnifiedClassifierAgent = ClassifierAgent  # Legacy alias
TransactionClassifierAgent = ClassifierAgent  # Legacy alias
