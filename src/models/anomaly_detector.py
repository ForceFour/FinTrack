"""Anomaly detection model for identifying suspicious transactions"""

import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os


class AnomalyDetector:
    """Machine Learning model for detecting anomalous transactions"""
    
    def __init__(self, model_path: str = None):
        self.model = IsolationForest(
            contamination=0.1,  # Expect 10% of data to be anomalous
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.model_path = model_path or "models/anomaly_detector.joblib"
        
        # Load pre-trained model if exists
        if os.path.exists(self.model_path):
            self.load_model()
    
    def train(self, X: np.ndarray, feature_names: List[str] = None) -> Dict[str, Any]:
        """Train the anomaly detection model"""
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled)
        self.is_trained = True
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        
        # Get anomaly scores for training data
        anomaly_scores = self.model.decision_function(X_scaled)
        outliers = self.model.predict(X_scaled)
        
        # Calculate statistics
        n_outliers = np.sum(outliers == -1)
        outlier_percentage = n_outliers / len(outliers) * 100
        
        # Save model
        self.save_model()
        
        return {
            "n_samples": len(X),
            "n_outliers": n_outliers,
            "outlier_percentage": outlier_percentage,
            "score_mean": np.mean(anomaly_scores),
            "score_std": np.std(anomaly_scores),
            "feature_names": self.feature_names
        }
    
    def predict(self, X: np.ndarray) -> Tuple[List[bool], List[float]]:
        """Predict anomalies and return anomaly scores"""
        if not self.is_trained:
            raise ValueError("Model has not been trained yet")
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Predict
        predictions = self.model.predict(X_scaled)
        scores = self.model.decision_function(X_scaled)
        
        # Convert predictions to boolean (True = anomaly)
        is_anomaly = [pred == -1 for pred in predictions]
        
        # Convert scores to risk scores (higher = more anomalous)
        risk_scores = [(-score + 0.5) for score in scores]  # Normalize to positive values
        
        return is_anomaly, risk_scores
    
    def detect_amount_anomalies(self, amounts: List[float], user_profile: Dict[str, Any]) -> List[bool]:
        """Detect anomalies based on transaction amounts"""
        avg_amount = user_profile.get('avg_monthly_spending', 1000) / 30  # Daily average
        std_amount = avg_amount * 0.5  # Assume 50% standard deviation
        
        anomalies = []
        for amount in amounts:
            z_score = abs((amount - avg_amount) / std_amount) if std_amount > 0 else 0
            is_anomaly = z_score > 3  # More than 3 standard deviations
            anomalies.append(is_anomaly)
        
        return anomalies
    
    def detect_frequency_anomalies(self, transaction_times: List[str], user_profile: Dict[str, Any]) -> List[bool]:
        """Detect anomalies based on transaction frequency and timing"""
        # Simple implementation - can be enhanced with more sophisticated time series analysis
        anomalies = []
        
        # For now, flag transactions outside normal hours (assuming 6 AM - 11 PM is normal)
        for time_str in transaction_times:
            try:
                # Extract hour from time string (assuming format includes time)
                if 'T' in time_str:  # ISO format
                    hour = int(time_str.split('T')[1].split(':')[0])
                else:
                    hour = 12  # Default to noon if no time info
                
                is_anomaly = hour < 6 or hour > 23
                anomalies.append(is_anomaly)
            except:
                anomalies.append(False)  # Default to not anomalous if parsing fails
        
        return anomalies
    
    def calculate_risk_score(self, transaction: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """Calculate overall risk score for a single transaction"""
        risk_factors = []
        
        # Amount-based risk
        amount = transaction.get('amount', 0)
        avg_amount = user_profile.get('avg_monthly_spending', 1000) / 30
        if avg_amount > 0:
            amount_ratio = amount / avg_amount
            if amount_ratio > 5:  # More than 5x average
                risk_factors.append(0.8)
            elif amount_ratio > 2:  # More than 2x average
                risk_factors.append(0.4)
        
        # Merchant-based risk
        merchant = transaction.get('merchant_standardized', '')
        known_merchants = user_profile.get('merchant_history', [])
        if merchant and merchant not in known_merchants:
            risk_factors.append(0.3)
        
        # Category-based risk
        category = transaction.get('predicted_category', '')
        if category == 'miscellaneous':  # Unknown category
            risk_factors.append(0.2)
        
        # Calculate final risk score
        if not risk_factors:
            return 0.1  # Minimum risk
        
        return min(sum(risk_factors), 1.0)  # Cap at 1.0
    
    def save_model(self):
        """Save the trained model to disk"""
        if self.is_trained:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained
            }, self.model_path)
    
    def load_model(self):
        """Load a pre-trained model from disk"""
        if os.path.exists(self.model_path):
            saved_data = joblib.load(self.model_path)
            self.model = saved_data['model']
            self.scaler = saved_data['scaler']
            self.feature_names = saved_data['feature_names']
            self.is_trained = saved_data['is_trained']
            return True
        return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_type": "IsolationForest",
            "is_trained": self.is_trained,
            "n_features": len(self.feature_names),
            "feature_names": self.feature_names,
            "model_path": self.model_path,
            "contamination": self.model.contamination if self.is_trained else None
        }
