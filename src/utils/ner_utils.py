"""NER utilities for merchant extraction"""

import re
from typing import Optional, List, Dict, Any


class MerchantExtractor:
    """Utility class for extracting and standardizing merchant names"""
    
    def __init__(self):
        # Common merchant patterns and their standardized names
        self.merchant_patterns = {
            r'STARBUCKS.*': 'Starbucks',
            r'WALMART.*': 'Walmart',
            r'AMAZON.*': 'Amazon',
            r'TARGET.*': 'Target',
            r'MCDONALD.*': 'McDonald\'s',
            r'UBER.*': 'Uber',
            r'SPOTIFY.*': 'Spotify',
            r'NETFLIX.*': 'Netflix',
            r'APPLE.*': 'Apple',
            r'GOOGLE.*': 'Google'
        }
        
        # Merchant categories mapping
        self.merchant_categories = {
            'Starbucks': 'Food & Dining',
            'McDonald\'s': 'Food & Dining',
            'Walmart': 'Groceries',
            'Target': 'Shopping',
            'Amazon': 'Shopping',
            'Uber': 'Transportation',
            'Spotify': 'Entertainment',
            'Netflix': 'Entertainment',
            'Apple': 'Technology',
            'Google': 'Technology'
        }
    
    def extract_merchant(self, description: str) -> Optional[str]:
        """Extract merchant name from transaction description"""
        # Clean the description
        description = description.upper().strip()
        
        # Check against known patterns
        for pattern, merchant in self.merchant_patterns.items():
            if re.search(pattern, description):
                return merchant
        
        # Try to extract merchant from common formats
        merchant = self._extract_from_common_formats(description)
        if merchant:
            return merchant
        
        return None
    
    def _extract_from_common_formats(self, description: str) -> Optional[str]:
        """Extract merchant from common transaction description formats"""
        # Pattern: "MERCHANT NAME LOCATION" or "MERCHANT NAME #ID"
        patterns = [
            r'^([A-Z\s&]+?)\s+(?:\#\d+|\d{4}|\w{2,3}\s\d+)',  # Merchant followed by ID or location
            r'^([A-Z\s&]+?)\s+\d{2}/\d{2}',  # Merchant followed by date
            r'^([A-Z\s&]+?)\s+[A-Z]{2}\s*$',  # Merchant followed by state code
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                merchant = match.group(1).strip()
                if len(merchant) > 3:  # Avoid very short matches
                    return self._clean_merchant_name(merchant)
        
        return None
    
    def _clean_merchant_name(self, merchant: str) -> str:
        """Clean and standardize merchant name"""
        # Remove common suffixes
        suffixes_to_remove = ['LLC', 'INC', 'CORP', 'CO', 'LTD']
        for suffix in suffixes_to_remove:
            merchant = re.sub(rf'\s+{suffix}$', '', merchant)
        
        # Convert to title case
        return merchant.title()
    
    def get_merchant_category(self, merchant: str) -> Optional[str]:
        """Get category for a known merchant"""
        return self.merchant_categories.get(merchant)
    
    def standardize_merchant(self, merchant: str) -> str:
        """Standardize merchant name using known mappings"""
        if not merchant:
            return "Unknown Merchant"
        
        # Check if we have a standardized version
        merchant_upper = merchant.upper()
        for pattern, standard_name in self.merchant_patterns.items():
            if re.search(pattern, merchant_upper):
                return standard_name
        
        return self._clean_merchant_name(merchant)
