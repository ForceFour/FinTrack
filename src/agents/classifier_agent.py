"""
Enhanced Classifier Agent - Agent 3
Role: Predict expense categories using advanced ML features and ensemble methods
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import logging
from collections import Counter
from datetime import datetime
from pydantic import BaseModel, Field

from ..schemas.transaction_schemas import MerchantTransaction, ClassifiedTransaction, TransactionCategory
from ..models.category_classifier import CategoryClassifier
from ..utils.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class ClassifierAgentInput(BaseModel):
    """Input schema for Enhanced Classifier Agent"""
    merchant_transactions: List[MerchantTransaction] = Field(description="Transactions with merchant info")
    historical_data: Optional[List[MerchantTransaction]] = Field(None, description="Historical transactions for context")


class ClassifierAgentOutput(BaseModel):
    """Output schema for Enhanced Classifier Agent"""
    classified_transactions: List[ClassifiedTransaction] = Field(description="Transactions with predicted categories")
    confidence_scores: List[float] = Field(description="Prediction confidence scores")
    classification_stats: Dict[str, Any] = Field(description="Classification performance statistics")


class EnhancedClassifierAgent:
    """
    Enhanced Agent 3: Classifier Agent with Advanced ML Features
    
    Responsibilities:
    - Engineer comprehensive features from transaction data:
        * Numeric features: amount, discounts, date components, outlier detection
        * Merchant features: frequency encoding, similarity metrics
        * Payment method features: one-hot encoding with interaction terms
        * Text features: TF-IDF embeddings and semantic features  
        * Temporal features: seasonality, day patterns, time-based trends
    - Use ensemble prediction combining multiple signals:
        * ML model predictions with confidence scoring
        * Rule-based merchant category mapping
        * Historical user patterns and preferences
    - Handle edge cases and low-confidence predictions gracefully
    - Provide detailed prediction explanations and fallback strategies
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.classifier = CategoryClassifier()
        self.feature_engineer = FeatureEngineer()
        
        # Configuration parameters
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.default_category = self.config.get('default_category', 'miscellaneous')
        
        # Initialize advanced components
        self._init_advanced_features()
        self._init_ensemble_components()
        
        # Feature importance tracking
        self.feature_names = []
        self.feature_importance = {}
        
        # Category mappings and rules - Sri Lankan merchants
        # Sri Lankan-specific merchant category mappings
        self.merchant_category_override = {
            # Sri Lankan Food & Dining
            'kfc': TransactionCategory.FOOD_DINING,
            'mcdonalds': TransactionCategory.FOOD_DINING,
            'pizza hut': TransactionCategory.FOOD_DINING,
            'dominos': TransactionCategory.FOOD_DINING,
            'subway': TransactionCategory.FOOD_DINING,
            'chinese dragon': TransactionCategory.FOOD_DINING,
            'hotel galadari': TransactionCategory.FOOD_DINING,
            'cinnamon grand': TransactionCategory.FOOD_DINING,
            
            # Sri Lankan Grocery & Retail
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
            
            # Sri Lankan Transportation & Fuel
            'uber': TransactionCategory.TRANSPORTATION,
            'pickme': TransactionCategory.TRANSPORTATION,
            'ceypetco': TransactionCategory.TRANSPORTATION,
            'indian oil': TransactionCategory.TRANSPORTATION,
            'ioc': TransactionCategory.TRANSPORTATION,
            'shell': TransactionCategory.TRANSPORTATION,
            
            # Sri Lankan Utilities & Services
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
            
            # E-commerce & Online Services
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
        
        # Amount-based category rules for Sri Lankan context (in LKR)
        self.amount_category_hints = {
            (0, 500): [TransactionCategory.FOOD_DINING, TransactionCategory.TRANSPORTATION, TransactionCategory.MISCELLANEOUS],
            (500, 2000): [TransactionCategory.FOOD_DINING, TransactionCategory.GROCERIES, TransactionCategory.TRANSPORTATION],
            (2000, 10000): [TransactionCategory.GROCERIES, TransactionCategory.SHOPPING, TransactionCategory.UTILITIES],
            (10000, 50000): [TransactionCategory.UTILITIES, TransactionCategory.HEALTHCARE, TransactionCategory.EDUCATION],
            (50000, 200000): [TransactionCategory.TRAVEL, TransactionCategory.HEALTHCARE, TransactionCategory.SHOPPING],
            (200000, float('inf')): [TransactionCategory.TRAVEL, TransactionCategory.EDUCATION, TransactionCategory.MISCELLANEOUS],
        }
    
    def _init_advanced_features(self):
        """Initialize advanced feature engineering components for Sri Lankan context"""
        # Seasonal patterns for different categories in Sri Lankan context
        # Sri Lankan seasonal patterns 
        self.seasonal_patterns = {
            'monsoon_season': {  # May-Sep & Nov-Feb
                TransactionCategory.UTILITIES: 1.2,  # Higher electricity bills (AC usage)
                TransactionCategory.HEALTHCARE: 1.1,  # More medical visits during monsoon
                TransactionCategory.TRANSPORTATION: 0.8,  # Less travel during heavy rains
            },
            'dry_season': {  # Mar-Apr & Oct
                TransactionCategory.UTILITIES: 1.3,  # Peak electricity usage for AC
                TransactionCategory.TRANSPORTATION: 1.2,  # More travel during good weather
                TransactionCategory.ENTERTAINMENT: 1.1,  # More outdoor activities
                TransactionCategory.TRAVEL: 1.3,  # Peak travel season
            },
            'festival_season': {  # Apr (New Year), Dec-Jan (Christmas/Western New Year)
                TransactionCategory.SHOPPING: 1.6,    # Heavy festival shopping
                TransactionCategory.FOOD_DINING: 1.4, # Festival dining
                TransactionCategory.TRAVEL: 1.3,      # Festival travel
                TransactionCategory.TRANSPORTATION: 1.2, # More travel for festivals
            },
            'school_season': {  # Jan-Mar, May-Aug, Sep-Dec
                TransactionCategory.EDUCATION: 1.5,   # School fees, supplies
                TransactionCategory.TRANSPORTATION: 1.2, # School transport
                TransactionCategory.SHOPPING: 1.1,    # School supplies
            }
        }
        
        # Day-of-week patterns for Sri Lankan context
        self.dow_patterns = {
            'weekday': {
                TransactionCategory.FOOD_DINING: 0.7,  # Less dining on weekdays
                TransactionCategory.GROCERIES: 1.1,    # More grocery shopping
                TransactionCategory.TRANSPORTATION: 1.3, # More commuting
                TransactionCategory.FUEL: 1.2,         # Commuting fuel
                TransactionCategory.TELECOMMUNICATIONS: 1.1,  # Work-related usage
            },
            'weekend': {
                TransactionCategory.ENTERTAINMENT: 1.4, # More entertainment on weekends
                TransactionCategory.SHOPPING: 1.2,      # More shopping
                TransactionCategory.FOOD_DINING: 1.3,   # More dining out
                TransactionCategory.RELIGIOUS_DONATIONS: 1.3, # Weekend temple visits
            },
            'poya_day': {  # Full moon day (public holiday)
                TransactionCategory.RELIGIOUS_DONATIONS: 2.0, # Peak temple visits
                TransactionCategory.TRAVEL: 1.2,       # Travel to temples/family
                TransactionCategory.FOOD_DINING: 0.8,   # Many observe fasting
                TransactionCategory.ENTERTAINMENT: 0.7,  # More religious observance
            }
        }
        
        # Sri Lankan specific amount confidence modifiers (in LKR)
        self.amount_confidence_modifiers = {
            TransactionCategory.FOOD_DINING: {
                (0, 300): 0.9,      # Tea/snacks
                (300, 1000): 1.0,   # Local meals
                (1000, 3000): 1.1,  # Restaurant dining
                (3000, 8000): 1.0,  # Fine dining
                (8000, float('inf')): 0.7,  # Unlikely for regular food
            },
            TransactionCategory.GROCERIES: {
                (1000, 10000): 1.2,   # Typical grocery shopping
                (10000, 25000): 1.0,  # Large family shopping
                (0, 1000): 0.8,       # Small purchases
                (25000, float('inf')): 0.6,  # Very large purchases
            },
            TransactionCategory.FUEL: {
                (1000, 8000): 1.2,    # Typical fuel fill-up
                (8000, 15000): 1.0,   # Full tank for larger vehicles
                (0, 1000): 0.8,       # Small fuel purchases
                (15000, float('inf')): 0.7,  # Very large fuel purchases
            },
            TransactionCategory.TELECOMMUNICATIONS: {
                (500, 5000): 1.2,     # Monthly mobile bills
                (5000, 15000): 1.1,   # Internet + mobile packages
                (0, 500): 0.9,        # Top-up cards
                (15000, float('inf')): 0.8,  # Very expensive plans
            },
            TransactionCategory.TRANSPORTATION: {
                (100, 2000): 1.1,     # Local transport, three-wheeler
                (2000, 5000): 1.0,    # Taxi rides
                (5000, 20000): 0.9,   # Long distance travel
                (20000, float('inf')): 0.8,  # Very expensive transport
            },
            TransactionCategory.UTILITIES: {
                (3000, 25000): 1.2,   # Monthly utility bills
                (25000, 50000): 1.0,  # High usage periods
                (0, 3000): 0.8,       # Very low utility bills
                (50000, float('inf')): 0.7,  # Extremely high bills
            }
        }
    
    def _init_ensemble_components(self):
        """Initialize ensemble classification components"""
        # Rule-based classifier weights
        self.ensemble_weights = {
            'ml_model': 0.4,          # ML model predictions
            'merchant_rules': 0.3,    # Merchant-based rules
            'amount_heuristics': 0.15, # Amount-based heuristics
            'temporal_patterns': 0.1,  # Time-based patterns
            'description_keywords': 0.05, # Keyword matching
        }
        
        # Confidence boosting rules
        self.confidence_boosters = {
            'merchant_exact_match': 1.2,    # Exact merchant match
            'multiple_signals_agree': 1.15,  # Multiple methods agree
            'high_amount_confidence': 1.1,   # Amount fits category well
            'strong_keyword_match': 1.1,     # Strong keyword evidence
        }
        
        # Confidence penalty rules
        self.confidence_penalties = {
            'conflicting_signals': 0.8,     # Methods disagree
            'low_merchant_confidence': 0.9,  # Uncertain merchant
            'unusual_amount': 0.85,          # Amount doesn't fit pattern
            'generic_description': 0.9,      # Very generic description
        }
    
    def engineer_numeric_features(self, transactions: List[MerchantTransaction]) -> np.ndarray:
        """Create comprehensive numeric features with advanced patterns"""
        logger.debug(f"Engineering enhanced numeric features for {len(transactions)} transactions")
        
        features = []
        feature_names = []
        
        for txn in transactions:
            # Basic amount features
            amount = abs(txn.amount)
            txn_features = [
                amount,                           # Raw amount
                np.log1p(amount),                # Log-transformed amount
                amount ** 0.5,                   # Square root amount
                1 if amount > 100 else 0,        # High amount flag
                1 if amount < 10 else 0,         # Small amount flag
                1 if txn.amount < 0 else 0,      # Negative amount flag (legacy)
                1 if txn.transaction_type.value == 'income' else 0,    # Income flag
                1 if txn.transaction_type.value == 'expense' else 0,   # Expense flag
                1 if txn.transaction_type.value == 'transfer' else 0,  # Transfer flag
            ]
            
            # Enhanced date-based features with seasonal patterns
            month = txn.month
            day_of_week = txn.day_of_week
            
            # Basic temporal features
            txn_features.extend([
                txn.year % 100,                  # Year (2-digit)
                month,                           # Month (1-12)
                txn.day,                         # Day of month
                day_of_week,                     # Day of week (0-6)
            ])
            
            # Advanced temporal features
            txn_features.extend([
                1 if day_of_week >= 5 else 0,   # Weekend flag
                1 if month in [12, 1, 2] else 0, # Winter flag
                1 if month in [6, 7, 8] else 0,  # Summer flag
                1 if month in [11, 12] else 0,   # Holiday season flag
                1 if day_of_week == 0 else 0,    # Monday flag (start of week)
                1 if day_of_week == 4 else 0,    # Friday flag (end of week)
                np.sin(2 * np.pi * month / 12),  # Monthly seasonality (sine)
                np.cos(2 * np.pi * month / 12),  # Monthly seasonality (cosine)
                np.sin(2 * np.pi * day_of_week / 7), # Weekly seasonality (sine)
                np.cos(2 * np.pi * day_of_week / 7), # Weekly seasonality (cosine)
            ])
            
            # Discount and promotion features
            txn_features.extend([
                1 if txn.has_discount else 0,    # Has discount flag
                txn.discount_percentage or 0,     # Discount percentage
                amount * (txn.discount_percentage or 0) / 100 if txn.has_discount else 0, # Discount amount
            ])
            
            # Enhanced metadata features
            metadata = txn.metadata or {}
            txn_features.extend([
                1 if metadata.get('is_outlier', False) else 0,  # Outlier flag
                metadata.get('amount_log', np.log1p(amount)),    # Pre-computed log amount
                metadata.get('effective_amount', amount),         # Effective amount after discount
                metadata.get('merchant_encoded', 0.0),           # Merchant encoding from preprocessing
                metadata.get('merchant_extraction_confidence', 0.0), # Merchant confidence from NER
            ])
            
            # Amount pattern features
            txn_features.extend([
                1 if amount % 1 == 0 else 0,     # Round number flag
                1 if str(amount).endswith(('.99', '.95', '.49')) else 0, # Promotional pricing
                len(str(int(amount))),           # Number of digits
                1 if amount > 1000 else 0,       # Very high amount
            ])
            
            features.append(txn_features)
        
        # Set feature names for the first transaction
        if not feature_names:
            feature_names = [
                'amount', 'amount_log', 'amount_sqrt', 'high_amount', 'small_amount', 'negative_amount',
                'is_income', 'is_expense', 'is_transfer',
                'year', 'month', 'day', 'day_of_week',
                'weekend', 'winter', 'summer', 'holiday_season', 'monday', 'friday',
                'monthly_sin', 'monthly_cos', 'weekly_sin', 'weekly_cos',
                'has_discount', 'discount_percentage', 'discount_amount',
                'is_outlier', 'preprocessed_amount_log', 'effective_amount', 'merchant_encoded', 'merchant_confidence',
                'round_number', 'promotional_pricing', 'amount_digits', 'very_high_amount'
            ]
            self.feature_names.extend([f'numeric_{name}' for name in feature_names])
        
        return np.array(features, dtype=np.float32)
    
    def engineer_merchant_features(self, transactions: List[MerchantTransaction]) -> np.ndarray:
        """Create merchant-based features with frequency encoding and similarity"""
        logger.debug(f"Engineering merchant features for {len(transactions)} transactions")
        
        # Collect all merchants for frequency analysis
        all_merchants = [txn.merchant_standardized or 'Unknown' for txn in transactions]
        merchant_counts = Counter(all_merchants)
        unique_merchants = list(set(all_merchants))
        
        features = []
        feature_names = ['merchant_frequency', 'merchant_relative_freq', 'is_recurring_merchant', 'is_known_merchant']
        
        for txn in transactions:
            merchant = txn.merchant_standardized or 'Unknown'
            
            # Frequency-based features
            frequency = merchant_counts[merchant]
            relative_frequency = frequency / len(transactions) if transactions else 0
            
            merchant_features = [
                frequency,                        # Absolute frequency
                relative_frequency,               # Relative frequency
                1 if frequency > 1 else 0,       # Is recurring merchant
                1 if txn.is_merchant_known else 0,  # Is known merchant
            ]
            
            features.append(merchant_features)
        
        # Add feature names to global list
        if f'merchant_{feature_names[0]}' not in self.feature_names:
            self.feature_names.extend([f'merchant_{name}' for name in feature_names])
        
        return np.array(features, dtype=np.float32)
    
    def engineer_payment_features(self, transactions: List[MerchantTransaction]) -> np.ndarray:
        """Create one-hot encoded payment method features with interactions"""
        logger.debug(f"Engineering payment method features for {len(transactions)} transactions")
        
        # Get all unique payment methods
        payment_methods = [txn.payment_method.value for txn in transactions]
        unique_methods = sorted(list(set(payment_methods)))
        
        features = []
        feature_names = []
        
        for txn in transactions:
            payment_method = txn.payment_method.value
            
            # One-hot encoding for payment methods
            one_hot_features = [1 if payment_method == method else 0 for method in unique_methods]
            
            # Additional payment method features
            additional_features = [
                1 if payment_method in ['credit_card', 'debit_card'] else 0,  # Card payment
                1 if payment_method == 'cash' else 0,                         # Cash payment
                1 if payment_method in ['digital_wallet', 'bank_transfer'] else 0,  # Digital payment
            ]
            
            payment_features = one_hot_features + additional_features
            features.append(payment_features)
        
        # Set feature names for first transaction
        if not any('payment_' in name for name in self.feature_names):
            feature_names = [f'pay_{method}' for method in unique_methods]
            feature_names.extend(['card_payment', 'cash_payment', 'digital_payment'])
            self.feature_names.extend([f'payment_{name}' for name in feature_names])
        
        return np.array(features, dtype=np.float32)
    
    def engineer_text_features(self, transactions: List[MerchantTransaction]) -> np.ndarray:
        """Create text embeddings and semantic features from descriptions"""
        logger.debug(f"Engineering text features for {len(transactions)} transactions")
        
        descriptions = [txn.description_cleaned for txn in transactions]
        
        # Use the feature engineer's text feature extraction
        try:
            tfidf_features = self.feature_engineer.engineer_text_features([
                {'description_cleaned': desc} for desc in descriptions
            ])
            
            # Add semantic features based on keywords
            semantic_features = []
            for desc in descriptions:
                desc_lower = desc.lower()
                semantic_feature = [
                    1 if any(word in desc_lower for word in ['restaurant', 'cafe', 'food', 'dining']) else 0,
                    1 if any(word in desc_lower for word in ['gas', 'fuel', 'station', 'shell', 'chevron']) else 0,
                    1 if any(word in desc_lower for word in ['grocery', 'market', 'walmart', 'target']) else 0,
                    1 if any(word in desc_lower for word in ['online', 'amazon', 'website', 'internet']) else 0,
                    1 if any(word in desc_lower for word in ['subscription', 'monthly', 'recurring']) else 0,
                ]
                semantic_features.append(semantic_feature)
            
            semantic_features = np.array(semantic_features, dtype=np.float32)
            
            # Combine TF-IDF with semantic features
            combined_features = np.hstack([tfidf_features, semantic_features])
            
            # Add feature names
            if not any('text_' in name for name in self.feature_names):
                tfidf_names = [f'tfidf_{i}' for i in range(tfidf_features.shape[1])]
                semantic_names = ['food_keywords', 'gas_keywords', 'grocery_keywords', 'online_keywords', 'subscription_keywords']
                self.feature_names.extend([f'text_{name}' for name in tfidf_names + semantic_names])
            
            return combined_features
            
        except Exception as e:
            logger.warning(f"Text feature engineering failed: {e}. Using fallback.")
            # Fallback to simple features
            simple_features = []
            for desc in descriptions:
                simple_features.append([len(desc), desc.count(' '), 1 if desc.isupper() else 0])
            
            if not any('text_' in name for name in self.feature_names):
                self.feature_names.extend(['text_length', 'text_word_count', 'text_all_caps'])
            
            return np.array(simple_features, dtype=np.float32)
    
    def combine_features(self, *feature_arrays) -> np.ndarray:
        """Combine all feature arrays into final feature matrix"""
        valid_arrays = [arr for arr in feature_arrays if arr.size > 0 and arr.ndim == 2]
        
        if not valid_arrays:
            logger.error("No valid feature arrays to combine")
            return np.array([[]])
        
        # Ensure all arrays have the same number of rows
        n_samples = valid_arrays[0].shape[0]
        for i, arr in enumerate(valid_arrays):
            if arr.shape[0] != n_samples:
                logger.error(f"Feature array {i} has {arr.shape[0]} samples, expected {n_samples}")
                return np.array([[]])
        
        combined = np.hstack(valid_arrays)
        logger.debug(f"Combined features shape: {combined.shape}")
        return combined
    
    def predict_categories_with_ensemble(self, transactions: List[MerchantTransaction], features: np.ndarray) -> Tuple[List[str], List[float], List[Dict[str, float]]]:
        """
        Enhanced ensemble prediction with multiple signals and confidence adjustment
        Returns: (predictions, confidence_scores, probability_distributions)
        """
        logger.debug(f"Making enhanced ensemble predictions for {len(transactions)} transactions")
        
        predictions = []
        confidence_scores = []
        probability_distributions = []
        
        # Get ML model predictions if available
        ml_predictions, ml_confidences, ml_probabilities = self._get_ml_predictions(features)
        
        # Process each transaction with comprehensive ensemble
        for i, txn in enumerate(transactions):
            ensemble_results = {}
            
            # Signal 1: ML model prediction
            if i < len(ml_predictions):
                ensemble_results['ml_model'] = {
                    'prediction': ml_predictions[i],
                    'confidence': ml_confidences[i],
                    'weight': self.ensemble_weights['ml_model']
                }
            
            # Signal 2: Merchant-based rules
            merchant_pred, merchant_conf = self._predict_from_merchant(txn)
            if merchant_pred:
                ensemble_results['merchant_rules'] = {
                    'prediction': merchant_pred,
                    'confidence': merchant_conf,
                    'weight': self.ensemble_weights['merchant_rules']
                }
            
            # Signal 3: Amount-based heuristics with enhanced logic
            amount_pred, amount_conf = self._predict_by_enhanced_heuristics(txn)
            if amount_pred:
                ensemble_results['amount_heuristics'] = {
                    'prediction': amount_pred,
                    'confidence': amount_conf,
                    'weight': self.ensemble_weights['amount_heuristics']
                }
            
            # Signal 4: Temporal pattern analysis
            temporal_pred, temporal_conf = self._predict_by_temporal_patterns(txn)
            if temporal_pred:
                ensemble_results['temporal_patterns'] = {
                    'prediction': temporal_pred,
                    'confidence': temporal_conf,
                    'weight': self.ensemble_weights['temporal_patterns']
                }
            
            # Signal 5: Enhanced keyword matching
            keyword_pred, keyword_conf = self._predict_by_enhanced_keywords(txn)
            if keyword_pred:
                ensemble_results['description_keywords'] = {
                    'prediction': keyword_pred,
                    'confidence': keyword_conf,
                    'weight': self.ensemble_weights['description_keywords']
                }
            
            # Combine ensemble signals with transaction type awareness
            final_pred, final_conf, proba_dist = self._combine_ensemble_signals(ensemble_results, txn)
            
            predictions.append(final_pred)
            confidence_scores.append(final_conf)
            probability_distributions.append(proba_dist)
            
            logger.debug(f"Transaction {i}: Ensemble={len(ensemble_results)} signals → {final_pred}({final_conf:.2f})")
        
        return predictions, confidence_scores, probability_distributions
    
    def _get_ml_predictions(self, features: np.ndarray) -> Tuple[List[str], List[float], List[Dict[str, float]]]:
        """Get ML model predictions with error handling"""
        ml_predictions = []
        ml_confidences = []
        ml_probabilities = []
        
        if self.classifier.is_trained and features.size > 0:
            try:
                ml_preds, ml_confs = self.classifier.predict(features)
                ml_proba_dict = self.classifier.predict_proba(features)
                
                ml_predictions = ml_preds
                ml_confidences = ml_confs
                ml_probabilities = ml_proba_dict
                
                logger.debug(f"ML model predictions: {len(ml_predictions)} with avg confidence: {np.mean(ml_confs):.2f}")
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")
        
        return ml_predictions, ml_confidences, ml_probabilities
    
    def _predict_from_merchant(self, transaction: MerchantTransaction) -> Tuple[Optional[str], float]:
        """Predict category from merchant information"""
        if not transaction.merchant_standardized:
            return None, 0.0
        
        merchant_lower = transaction.merchant_standardized.lower()
        
        # Check direct merchant mapping
        if merchant_lower in self.merchant_category_override:
            return self.merchant_category_override[merchant_lower].value, 0.95
        
        # Check merchant category from NER agent
        if transaction.merchant_category:
            # Boost confidence if extraction was confident
            merchant_extraction_conf = transaction.metadata.get('merchant_extraction_confidence', 0.5)
            base_confidence = 0.80
            adjusted_confidence = min(base_confidence * (1 + merchant_extraction_conf * 0.2), 0.95)
            return transaction.merchant_category, adjusted_confidence
        
        return None, 0.0
    
    def _predict_by_enhanced_heuristics(self, transaction: MerchantTransaction) -> Tuple[Optional[str], float]:
        """Enhanced heuristic prediction with amount patterns and context"""
        amount = abs(transaction.amount)
        desc = transaction.description_cleaned.lower()
        
        # Enhanced keyword mapping with context
        # Enhanced keyword mapping with Sri Lankan context and LKR amounts
        enhanced_keyword_mapping = {
            TransactionCategory.FOOD_DINING: {
                'keywords': ['restaurant', 'cafe', 'hotel', 'food', 'dining', 'coffee', 'pizza', 'burger', 'eat', 
                           'rice', 'curry', 'kottu', 'hoppers', 'roti', 'chinese', 'dragon', 'kfc', 'mcdonalds'],
                'amount_sweet_spot': (200, 5000),  # LKR
                'confidence_base': 0.75
            },
            TransactionCategory.GROCERIES: {
                'keywords': ['keells', 'cargills', 'food city', 'arpico', 'laugfs', 'super', 'market', 'grocery'],
                'amount_sweet_spot': (1000, 15000),  # LKR
                'confidence_base': 0.80
            },
            TransactionCategory.TRANSPORTATION: {
                'keywords': ['uber', 'pickme', 'taxi', 'fuel', 'petrol', 'diesel', 'ceypetco', 'ioc', 'shell', 
                           'transport', 'bus', 'parking'],
                'amount_sweet_spot': (100, 5000),  # LKR
                'confidence_base': 0.75
            },
            TransactionCategory.ENTERTAINMENT: {
                'keywords': ['netflix', 'spotify', 'movie', 'cinema', 'game', 'entertainment', 'subscription', 
                           'youtube'],
                'amount_sweet_spot': (500, 3000),  # LKR
                'confidence_base': 0.70
            },
            TransactionCategory.UTILITIES: {
                'keywords': ['dialog', 'mobitel', 'airtel', 'hutch', 'ceb', 'nwsdb', 'electricity', 'water', 
                           'internet', 'phone', 'bill', 'utility'],
                'amount_sweet_spot': (2000, 25000),  # LKR
                'confidence_base': 0.85
            },
            TransactionCategory.HEALTHCARE: {
                'keywords': ['nawaloka', 'asiri', 'hospital', 'doctor', 'medical', 'pharmacy', 'osu', 'sala', 
                           'health', 'clinic'],
                'amount_sweet_spot': (1000, 50000),  # LKR
                'confidence_base': 0.75
            },
            TransactionCategory.SHOPPING: {
                'keywords': ['daraz', 'ikman', 'shop', 'store', 'buy', 'purchase', 'singer', 'abans', 'softlogic'],
                'amount_sweet_spot': (500, 100000),  # LKR
                'confidence_base': 0.65
            },
        }
        
        best_category = None
        best_confidence = 0.0
        
        for category, config in enhanced_keyword_mapping.items():
            # Check for keyword matches
            keyword_matches = sum(1 for keyword in config['keywords'] if keyword in desc)
            
            if keyword_matches > 0:
                # Base confidence from keyword match
                confidence = config['confidence_base'] * (keyword_matches / len(config['keywords']))
                
                # Adjust confidence based on amount fit
                min_amt, max_amt = config['amount_sweet_spot']
                if min_amt <= amount <= max_amt:
                    confidence *= 1.2  # Boost confidence for good amount fit
                elif amount < min_amt * 0.5 or amount > max_amt * 2:
                    confidence *= 0.7  # Reduce confidence for poor amount fit
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_category = category.value
        
        return best_category, min(best_confidence, 0.85) if best_category else (None, 0.0)
    
    def _predict_by_temporal_patterns(self, transaction: MerchantTransaction) -> Tuple[Optional[str], float]:
        """Predict category based on temporal patterns"""
        month = transaction.month
        day_of_week = transaction.day_of_week
        
        # Determine time context
        is_weekend = day_of_week >= 5
        is_winter = month in [12, 1, 2]
        is_summer = month in [6, 7, 8]
        is_holiday = month in [11, 12]
        
        best_category = None
        best_confidence = 0.0
        
        # Apply seasonal patterns
        seasonal_modifiers = {}
        if is_winter:
            seasonal_modifiers.update(self.seasonal_patterns.get('winter', {}))
        if is_summer:
            seasonal_modifiers.update(self.seasonal_patterns.get('summer', {}))
        if is_holiday:
            seasonal_modifiers.update(self.seasonal_patterns.get('holiday', {}))
        
        # Apply day-of-week patterns
        dow_modifiers = {}
        if is_weekend:
            dow_modifiers.update(self.dow_patterns.get('weekend', {}))
        else:
            dow_modifiers.update(self.dow_patterns.get('weekday', {}))
        
        # Find category with highest combined modifier
        all_modifiers = {}
        for category in seasonal_modifiers:
            all_modifiers[category] = seasonal_modifiers[category] * dow_modifiers.get(category, 1.0)
        
        if all_modifiers:
            best_category = max(all_modifiers.keys(), key=lambda x: all_modifiers[x])
            best_confidence = min((all_modifiers[best_category] - 1.0) * 0.5 + 0.3, 0.6)  # Convert modifier to confidence
        
        return best_category.value if best_category else None, best_confidence
    
    def _predict_by_enhanced_keywords(self, transaction: MerchantTransaction) -> Tuple[Optional[str], float]:
        """Enhanced keyword-based prediction with weighted matching"""
        desc = transaction.description_cleaned.lower()
        merchant = (transaction.merchant_standardized or '').lower()
        combined_text = f"{desc} {merchant}".strip()
        
        if not combined_text:
            return None, 0.0
        
        # Weighted keyword sets
        weighted_keywords = {
            TransactionCategory.FOOD_DINING: {
                'high_weight': ['starbucks', 'mcdonalds', 'restaurant', 'cafe'],
                'medium_weight': ['food', 'dining', 'coffee', 'pizza', 'burger'],
                'low_weight': ['eat', 'meal', 'lunch', 'dinner', 'breakfast']
            },
            TransactionCategory.SHOPPING: {
                'high_weight': ['amazon', 'walmart', 'target', 'shop', 'store'],
                'medium_weight': ['retail', 'purchase', 'buy', 'mall'],
                'low_weight': ['clothing', 'electronics', 'goods']
            },
            TransactionCategory.TRANSPORTATION: {
                'high_weight': ['uber', 'lyft', 'gas', 'fuel'],
                'medium_weight': ['taxi', 'parking', 'metro', 'transport'],
                'low_weight': ['car', 'vehicle', 'auto']
            }
        }
        
        category_scores = {}
        
        for category, weight_groups in weighted_keywords.items():
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
            confidence = min(best_score * 0.4, 0.8)  # Scale to reasonable confidence
            
            return best_category.value, confidence
        
        return None, 0.0
    
    def _combine_ensemble_signals(self, ensemble_results: Dict[str, Dict], transaction: MerchantTransaction) -> Tuple[str, float, Dict[str, float]]:
        """Advanced ensemble combination with confidence adjustment"""
        if not ensemble_results:
            return self.default_category, 0.1, {}
        
        # Calculate weighted votes for each category
        category_votes = {}
        total_weight = 0.0
        
        for signal_name, result in ensemble_results.items():
            prediction = result['prediction']
            confidence = result['confidence']
            weight = result['weight']
            
            weighted_vote = confidence * weight
            category_votes[prediction] = category_votes.get(prediction, 0.0) + weighted_vote
            total_weight += weight
        
        # Find best prediction
        if not category_votes:
            return self.default_category, 0.1, {}
        
        best_category = max(category_votes.keys(), key=lambda x: category_votes[x])
        raw_confidence = category_votes[best_category] / total_weight if total_weight > 0 else 0.1
        
        # Apply confidence adjustments
        adjusted_confidence = self._apply_confidence_adjustments(
            best_category, raw_confidence, ensemble_results, transaction
        )
        
        # Create probability distribution
        proba_dist = {}
        for category in category_votes:
            proba_dist[category] = category_votes[category] / sum(category_votes.values())
        
        # Ensure all categories are represented
        all_categories = [cat.value for cat in TransactionCategory]
        for cat in all_categories:
            if cat not in proba_dist:
                proba_dist[cat] = 0.01
        
        # Normalize
        total_prob = sum(proba_dist.values())
        proba_dist = {k: v / total_prob for k, v in proba_dist.items()}
        
        return best_category, adjusted_confidence, proba_dist
    
    def _apply_confidence_adjustments(self, prediction: str, base_confidence: float, 
                                    ensemble_results: Dict[str, Dict], transaction: MerchantTransaction) -> float:
        """Apply confidence boosters and penalties"""
        adjusted_confidence = base_confidence
        
        # Check for boosters
        predictions = [result['prediction'] for result in ensemble_results.values()]
        prediction_agreement = sum(1 for p in predictions if p == prediction) / len(predictions)
        
        if prediction_agreement >= 0.8:  # High agreement
            adjusted_confidence *= self.confidence_boosters['multiple_signals_agree']
        
        # Merchant exact match booster
        if transaction.merchant_standardized and any(
            signal['prediction'] == prediction and 'merchant' in signal_name 
            for signal_name, signal in ensemble_results.items()
        ):
            adjusted_confidence *= self.confidence_boosters['merchant_exact_match']
        
        # Amount confidence modifier
        amount = abs(transaction.amount)
        if prediction in self.amount_confidence_modifiers:
            for (min_amt, max_amt), modifier in self.amount_confidence_modifiers[TransactionCategory(prediction)].items():
                if min_amt <= amount < max_amt:
                    adjusted_confidence *= modifier
                    break
        
        # Apply penalties for conflicting signals
        if prediction_agreement < 0.5:
            adjusted_confidence *= self.confidence_penalties['conflicting_signals']
        
        # Low merchant confidence penalty
        merchant_conf = transaction.metadata.get('merchant_extraction_confidence', 1.0)
        if merchant_conf < 0.5:
            adjusted_confidence *= self.confidence_penalties['low_merchant_confidence']
        
        return min(adjusted_confidence, 0.98)  # Cap at 98%
    
    def _predict_by_heuristics(self, transaction: MerchantTransaction) -> Tuple[str, float]:
        """Predict category using heuristic rules based on amount, description, etc."""
        amount = abs(transaction.amount)
        desc = transaction.description_cleaned.lower()
        
        # Amount-based hints
        likely_categories = []
        for (min_amt, max_amt), categories in self.amount_category_hints.items():
            if min_amt <= amount < max_amt:
                likely_categories = categories
                break
        
        # Description keyword matching
        keyword_mapping = {
            'food_dining': ['restaurant', 'cafe', 'food', 'dining', 'coffee', 'pizza', 'burger'],
            'groceries': ['grocery', 'market', 'walmart', 'target', 'costco', 'whole foods'],
            'transportation': ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'parking', 'metro'],
            'entertainment': ['netflix', 'spotify', 'movie', 'game', 'entertainment'],
            'utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'utility'],
            'healthcare': ['doctor', 'hospital', 'pharmacy', 'medical', 'health'],
        }
        
        for category, keywords in keyword_mapping.items():
            if any(keyword in desc for keyword in keywords):
                return category, 0.65  # Moderate confidence for keyword matching
        
        # Fallback to amount-based prediction
        if likely_categories:
            return likely_categories[0].value, 0.30  # Low confidence for amount-only prediction
        
        return self.default_category, 0.20  # Very low confidence for default
    
    def _combine_predictions(self, ml_pred: str, ml_conf: float, rule_pred: str, rule_conf: float, 
                           heuristic_pred: str, heuristic_conf: float) -> Tuple[str, float]:
        """Combine multiple prediction sources into final prediction"""
        
        # Collect all predictions with their confidences
        candidates = []
        if ml_pred and ml_conf > 0:
            candidates.append((ml_pred, ml_conf, 'ml'))
        if rule_pred and rule_conf > 0:
            candidates.append((rule_pred, rule_conf, 'rule'))
        if heuristic_pred and heuristic_conf > 0:
            candidates.append((heuristic_pred, heuristic_conf, 'heuristic'))
        
        if not candidates:
            return self.default_category, 0.1
        
        # Sort by confidence
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Decision logic
        best_pred, best_conf, best_source = candidates[0]
        
        # If rule-based prediction exists and has reasonable confidence, prefer it
        rule_candidate = next((c for c in candidates if c[2] == 'rule'), None)
        if rule_candidate and rule_candidate[1] >= 0.80:
            return rule_candidate[0], rule_candidate[1]
        
        # If ML prediction is confident enough, use it
        if best_source == 'ml' and best_conf >= self.confidence_threshold:
            return best_pred, best_conf
        
        # If multiple predictions agree, boost confidence
        pred_counts = Counter([c[0] for c in candidates])
        if pred_counts[best_pred] > 1:
            boosted_conf = min(best_conf * 1.2, 0.95)
            return best_pred, boosted_conf
        
        # Default to best prediction
        return best_pred, best_conf
    
    def process(self, input_data: ClassifierAgentInput) -> ClassifierAgentOutput:
        """Enhanced processing with comprehensive performance monitoring"""
        start_time = datetime.now()
        logger.info(f"Processing {len(input_data.merchant_transactions)} transactions for enhanced classification")
        
        transactions = input_data.merchant_transactions
        if not transactions:
            logger.warning("No transactions to classify")
            return ClassifierAgentOutput(
                classified_transactions=[],
                confidence_scores=[],
                classification_stats={'error': 'No transactions provided'}
            )
        
        # Initialize comprehensive statistics
        classification_stats = {
            'total_processed': len(transactions),
            'processing_start_time': start_time.isoformat(),
            'feature_engineering_time': 0.0,
            'prediction_time': 0.0,
            'total_processing_time': 0.0,
            'average_confidence': 0.0,
            'median_confidence': 0.0,
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'ensemble_signals_used': Counter(),
            'category_distribution': Counter(),
            'feature_stats': {},
            'performance_metrics': {}
        }
        
        # Feature engineering with timing
        logger.debug("Starting enhanced feature engineering...")
        feature_start = datetime.now()
        
        try:
            numeric_features = self.engineer_numeric_features(transactions)
            merchant_features = self.engineer_merchant_features(transactions)
            payment_features = self.engineer_payment_features(transactions)
            text_features = self.engineer_text_features(transactions)
            
            # Combine all features
            combined_features = self.combine_features(
                numeric_features, merchant_features, payment_features, text_features
            )
            
            feature_time = (datetime.now() - feature_start).total_seconds()
            classification_stats['feature_engineering_time'] = feature_time
            classification_stats['feature_stats'] = {
                'total_features': combined_features.shape[1] if combined_features.size > 0 else 0,
                'numeric_features': numeric_features.shape[1] if numeric_features.size > 0 else 0,
                'merchant_features': merchant_features.shape[1] if merchant_features.size > 0 else 0,
                'payment_features': payment_features.shape[1] if payment_features.size > 0 else 0,
                'text_features': text_features.shape[1] if text_features.size > 0 else 0,
            }
            
            logger.debug(f"Enhanced feature engineering complete. Final shape: {combined_features.shape} in {feature_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            # Fallback to simple features
            combined_features = np.array([[txn.amount, txn.month, txn.day_of_week] for txn in transactions])
            classification_stats['feature_stats']['error'] = str(e)
        
        # Make predictions using enhanced ensemble method
        logger.debug("Starting enhanced ensemble prediction...")
        pred_start = datetime.now()
        
        predictions, confidence_scores, probability_distributions = self.predict_categories_with_ensemble(
            transactions, combined_features
        )
        
        pred_time = (datetime.now() - pred_start).total_seconds()
        classification_stats['prediction_time'] = pred_time
        
        # Create enhanced classified transactions
        classified_transactions = []
        for i, txn in enumerate(transactions):
            try:
                classified_txn = ClassifiedTransaction(
                    # Inherit from MerchantTransaction
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
                    # Enhanced classification fields
                    predicted_category=TransactionCategory(predictions[i]),
                    prediction_confidence=confidence_scores[i],
                    category_probabilities=probability_distributions[i]
                )
                
                # Add comprehensive classification metadata
                classified_txn.metadata.update({
                    'classification_method': 'enhanced_ensemble_v2',
                    'feature_count': combined_features.shape[1] if combined_features.size > 0 else 0,
                    'ensemble_confidence': confidence_scores[i],
                    'classification_timestamp': datetime.now().isoformat(),
                    'processing_duration_ms': (feature_time + pred_time) * 1000 / len(transactions),
                    'category_probabilities_sorted': sorted(
                        probability_distributions[i].items(), 
                        key=lambda x: x[1], reverse=True
                    )[:3]  # Top 3 category probabilities
                })
                
                classified_transactions.append(classified_txn)
                
                # Update statistics
                confidence = confidence_scores[i]
                if confidence >= 0.8:
                    classification_stats['confidence_distribution']['high'] += 1
                elif confidence >= 0.5:
                    classification_stats['confidence_distribution']['medium'] += 1
                else:
                    classification_stats['confidence_distribution']['low'] += 1
                
                classification_stats['category_distribution'][predictions[i]] += 1
                
            except Exception as e:
                logger.error(f"Error creating classified transaction {i}: {e}")
                # Create basic classified transaction
                basic_classified = ClassifiedTransaction(
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
                    category_probabilities={}
                )
                basic_classified.metadata['classification_error'] = str(e)
                classified_transactions.append(basic_classified)
        
        # Calculate final comprehensive statistics
        total_time = (datetime.now() - start_time).total_seconds()
        classification_stats['total_processing_time'] = total_time
        classification_stats['processing_rate_per_second'] = len(transactions) / total_time if total_time > 0 else 0
        
        if confidence_scores:
            classification_stats['average_confidence'] = float(np.mean(confidence_scores))
            classification_stats['median_confidence'] = float(np.median(confidence_scores))
            classification_stats['min_confidence'] = float(np.min(confidence_scores))
            classification_stats['max_confidence'] = float(np.max(confidence_scores))
            classification_stats['std_confidence'] = float(np.std(confidence_scores))
        
        # Performance metrics
        classification_stats['performance_metrics'] = {
            'transactions_per_second': classification_stats['processing_rate_per_second'],
            'feature_engineering_ratio': classification_stats['feature_engineering_time'] / total_time,
            'prediction_ratio': classification_stats['prediction_time'] / total_time,
            'high_confidence_rate': classification_stats['confidence_distribution']['high'] / len(transactions),
            'ensemble_effectiveness': len([c for c in confidence_scores if c > 0.7]) / len(transactions)
        }
        
        # Convert Counter objects for JSON serialization
        classification_stats['ensemble_signals_used'] = dict(classification_stats['ensemble_signals_used'])
        classification_stats['category_distribution'] = dict(classification_stats['category_distribution'])
        
        logger.info(
            f"Enhanced classification completed in {total_time:.2f}s. "
            f"Avg confidence: {classification_stats['average_confidence']:.2f}, "
            f"High confidence rate: {classification_stats['performance_metrics']['high_confidence_rate']:.1%}, "
            f"Rate: {classification_stats['processing_rate_per_second']:.1f}/s"
        )
        
        return ClassifierAgentOutput(
            classified_transactions=classified_transactions,
            confidence_scores=confidence_scores,
            classification_stats=classification_stats
        )
    
    def _generate_classification_stats(self, predictions: List[str], confidence_scores: List[float], 
                                     probability_distributions: List[Dict[str, float]]) -> Dict[str, Any]:
        """Generate detailed statistics about the classification results"""
        
        category_counts = Counter(predictions)
        
        stats = {
            'total_classified': len(predictions),
            'average_confidence': float(np.mean(confidence_scores)) if confidence_scores else 0.0,
            'median_confidence': float(np.median(confidence_scores)) if confidence_scores else 0.0,
            'min_confidence': float(np.min(confidence_scores)) if confidence_scores else 0.0,
            'max_confidence': float(np.max(confidence_scores)) if confidence_scores else 0.0,
            'high_confidence_count': sum(1 for conf in confidence_scores if conf >= self.confidence_threshold),
            'low_confidence_count': sum(1 for conf in confidence_scores if conf < 0.5),
            'category_distribution': dict(category_counts),
            'most_common_category': category_counts.most_common(1)[0][0] if category_counts else None,
            'feature_count': len(self.feature_names),
            'classifier_type': 'enhanced_ensemble'
        }
        
        # Add confidence rate
        if len(confidence_scores) > 0:
            stats['high_confidence_rate'] = stats['high_confidence_count'] / len(confidence_scores)
        
        return stats


# Backward compatibility alias
ClassifierAgent = EnhancedClassifierAgent
