"""Category classification model"""

import numpy as np
from typing import List, Tuple, Dict, Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os


class CategoryClassifier:
    """Machine Learning model for predicting transaction categories"""
    
    def __init__(self, model_path: str = None):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.is_trained = False
        self.categories = []
        self.model_path = model_path or "models/category_classifier.joblib"
        
        # Load pre-trained model if exists
        if os.path.exists(self.model_path):
            self.load_model()
    
    def train(self, X: np.ndarray, y: List[str], validation_split: float = 0.2) -> Dict[str, Any]:
        """Train the category classification model"""
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        self.categories = list(set(y))
        
        # Evaluate
        y_pred = self.model.predict(X_val)
        accuracy = accuracy_score(y_val, y_pred)
        report = classification_report(y_val, y_pred, output_dict=True)
        
        # Save model
        self.save_model()
        
        return {
            "accuracy": accuracy,
            "classification_report": report,
            "feature_importance": self.get_feature_importance(),
            "categories": self.categories
        }
    
    def predict(self, X: np.ndarray) -> Tuple[List[str], List[float]]:
        """Predict categories and return confidence scores"""
        if not self.is_trained:
            raise ValueError("Model has not been trained yet")
        
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        
        # Get confidence scores (max probability for each prediction)
        confidence_scores = [max(probs) for probs in probabilities]
        
        return predictions.tolist(), confidence_scores
    
    def predict_proba(self, X: np.ndarray) -> Dict[str, List[float]]:
        """Get probability distributions for all categories"""
        if not self.is_trained:
            raise ValueError("Model has not been trained yet")
        
        probabilities = self.model.predict_proba(X)
        classes = self.model.classes_
        
        result = {}
        for i, class_name in enumerate(classes):
            result[class_name] = probabilities[:, i].tolist()
        
        return result
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from the trained model"""
        if not self.is_trained:
            return {}
        
        feature_names = [f"feature_{i}" for i in range(len(self.model.feature_importances_))]
        importance_dict = dict(zip(feature_names, self.model.feature_importances_))
        
        # Sort by importance
        sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_importance
    
    def save_model(self):
        """Save the trained model to disk"""
        if self.is_trained:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump({
                'model': self.model,
                'categories': self.categories,
                'is_trained': self.is_trained
            }, self.model_path)
    
    def load_model(self):
        """Load a pre-trained model from disk"""
        if os.path.exists(self.model_path):
            saved_data = joblib.load(self.model_path)
            self.model = saved_data['model']
            self.categories = saved_data['categories']
            self.is_trained = saved_data['is_trained']
            return True
        return False
    
    def retrain_incremental(self, X_new: np.ndarray, y_new: List[str]) -> Dict[str, Any]:
        """Incrementally retrain the model with new data"""
        if not self.is_trained:
            return self.train(X_new, y_new)
        
        # For RandomForest, we need to retrain from scratch
        # In production, consider using models that support incremental learning
        print("Warning: RandomForest doesn't support incremental learning. Retraining from scratch.")
        return self.train(X_new, y_new)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_type": "RandomForestClassifier",
            "is_trained": self.is_trained,
            "n_categories": len(self.categories),
            "categories": self.categories,
            "model_path": self.model_path,
            "n_estimators": self.model.n_estimators if self.is_trained else None,
            "max_depth": self.model.max_depth if self.is_trained else None
        }
