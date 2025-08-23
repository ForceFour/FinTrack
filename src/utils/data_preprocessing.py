"""Utility functions for data preprocessing"""

import re
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional


class DataPreprocessor:
    """Utility class for preprocessing raw transaction data"""
    
    def __init__(self):
        self.date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S"
        ]
        
        self.payment_method_mapping = {
            "visa": "credit_card",
            "mastercard": "credit_card",
            "amex": "credit_card",
            "american express": "credit_card",
            "debit": "debit_card",
            "cash": "cash",
            "transfer": "bank_transfer",
            "paypal": "digital_wallet",
            "venmo": "digital_wallet",
            "apple pay": "digital_wallet",
            "google pay": "digital_wallet"
        }
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string using multiple formats"""
        for fmt in self.date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    
    def parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[$€£¥,\s]', '', str(amount_str))
        # Handle negative amounts in parentheses
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def standardize_payment_method(self, payment_str: str) -> str:
        """Standardize payment method"""
        payment_lower = payment_str.lower().strip()
        for key, value in self.payment_method_mapping.items():
            if key in payment_lower:
                return value
        return "other"
    
    def extract_discount_info(self, description: str) -> Dict[str, Any]:
        """Extract discount information from description"""
        discount_patterns = [
            r'(\d+)%\s*off',
            r'save\s*(\d+)%',
            r'discount\s*(\d+)%',
            r'(\d+)%\s*discount'
        ]
        
        for pattern in discount_patterns:
            match = re.search(pattern, description.lower())
            if match:
                return {
                    "has_discount": True,
                    "discount_percentage": float(match.group(1))
                }
        
        return {"has_discount": False, "discount_percentage": None}
    
    def clean_description(self, description: str) -> str:
        """Clean and normalize description text"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', description.strip())
        # Remove special characters but keep basic punctuation
        cleaned = re.sub(r'[^\w\s\-\.\,\&]', '', cleaned)
        return cleaned
