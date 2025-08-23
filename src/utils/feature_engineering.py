"""Feature engineering utilities for ML models"""

import numpy as np
from typing import List, Dict, Any
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer


class FeatureEngineer:
    """Utility class for engineering features from transaction data"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.merchant_encoder = {}
        self.payment_method_encoder = {}
    
    def engineer_date_features(self, transactions: List[Dict[str, Any]]) -> np.ndarray:
        """Create date-based features"""
        features = []
        for txn in transactions:
            date_features = [
                txn.get('year', 0),
                txn.get('month', 0),
                txn.get('day', 0),
                txn.get('day_of_week', 0),
                1 if txn.get('month') in [12, 1, 2] else 0,  # Winter season
                1 if txn.get('month') in [3, 4, 5] else 0,   # Spring season
                1 if txn.get('month') in [6, 7, 8] else 0,   # Summer season
                1 if txn.get('month') in [9, 10, 11] else 0, # Fall season
                1 if txn.get('day_of_week') in [5, 6] else 0 # Weekend
            ]
            features.append(date_features)
        return np.array(features)
    
    def engineer_amount_features(self, transactions: List[Dict[str, Any]]) -> np.ndarray:
        """Create amount-based features"""
        amounts = [txn.get('amount', 0) for txn in transactions]
        amounts_array = np.array(amounts).reshape(-1, 1)
        
        # Additional amount features
        features = []
        for amount in amounts:
            amount_features = [
                amount,
                np.log1p(abs(amount)),  # Log transform
                1 if amount > 100 else 0,  # High amount flag
                1 if amount < 0 else 0,    # Negative amount flag
            ]
            features.append(amount_features)
        
        return np.array(features)
    
    def engineer_merchant_features(self, transactions: List[Dict[str, Any]]) -> np.ndarray:
        """Create merchant frequency encoding features"""
        merchants = [txn.get('merchant_standardized', 'Unknown') for txn in transactions]
        
        # Calculate merchant frequencies
        merchant_counts = {}
        for merchant in merchants:
            merchant_counts[merchant] = merchant_counts.get(merchant, 0) + 1
        
        # Create frequency encoding
        features = []
        for merchant in merchants:
            freq = merchant_counts[merchant]
            total_transactions = len(transactions)
            features.append([
                freq,  # Absolute frequency
                freq / total_transactions,  # Relative frequency
                1 if freq > 1 else 0,  # Is recurring merchant
            ])
        
        return np.array(features)
    
    def engineer_payment_features(self, transactions: List[Dict[str, Any]]) -> np.ndarray:
        """Create one-hot encoded payment method features"""
        payment_methods = [txn.get('payment_method', 'other') for txn in transactions]
        unique_methods = list(set(payment_methods))
        
        # Create one-hot encoding
        features = []
        for payment in payment_methods:
            one_hot = [1 if payment == method else 0 for method in unique_methods]
            features.append(one_hot)
        
        return np.array(features)
    
    def engineer_text_features(self, transactions: List[Dict[str, Any]]) -> np.ndarray:
        """Create text embeddings from descriptions"""
        descriptions = [txn.get('description_cleaned', '') for txn in transactions]
        
        # Fit and transform TF-IDF
        if len(descriptions) > 0:
            try:
                tfidf_features = self.tfidf_vectorizer.fit_transform(descriptions)
                return tfidf_features.toarray()
            except Exception:
                # Fallback to simple features if TF-IDF fails
                return np.zeros((len(descriptions), 10))
        else:
            return np.zeros((len(descriptions), 10))
    
    def engineer_discount_features(self, transactions: List[Dict[str, Any]]) -> np.ndarray:
        """Create discount-related features"""
        features = []
        for txn in transactions:
            discount_features = [
                1 if txn.get('has_discount', False) else 0,
                txn.get('discount_percentage', 0) / 100,  # Normalize percentage
            ]
            features.append(discount_features)
        
        return np.array(features)
    
    def combine_features(self, *feature_arrays) -> np.ndarray:
        """Combine multiple feature arrays horizontally"""
        if not feature_arrays:
            return np.array([])
        
        # Filter out empty arrays
        valid_arrays = [arr for arr in feature_arrays if arr.size > 0]
        
        if not valid_arrays:
            return np.array([])
        
        return np.hstack(valid_arrays)
    
    def scale_features(self, features: np.ndarray, fit: bool = True) -> np.ndarray:
        """Scale features using StandardScaler"""
        if fit:
            return self.scaler.fit_transform(features)
        else:
            return self.scaler.transform(features)
