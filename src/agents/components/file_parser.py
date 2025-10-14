"""
File Parser Component - Handles structured data from CSV/Excel files
"""

import pandas as pd
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class FileParser:
    """
    Component for parsing structured transaction data from files
    """

    def __init__(self):
        self.required_columns = ['date', 'amount', 'description']
        self.optional_columns = [
            'category', 'merchant', 'payment_method',
            'offer_discount', 'recurring_flag'
        ]

    def parse_csv_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse CSV data into standardized format with enhanced classification"""
        try:
            # Normalize column names
            df.columns = df.columns.str.lower().str.strip()

            # Column mapping variations to handle different CSV formats
            column_mappings = {
                'date': ['date', 'transaction_date', 'txn_date', 'posted_date'],
                'amount': ['amount', 'transaction_amount', 'txn_amount', 'value'],
                'description': ['description', 'desc', 'transaction_description', 'memo', 'details'],
                'merchant': ['merchant', 'vendor', 'payee', 'store', 'company'],
                'category': ['category', 'type', 'transaction_type', 'expense_type']
            }

            # Find the best matching columns
            final_mapping = {}
            for field, possible_names in column_mappings.items():
                for name in possible_names:
                    if name in df.columns:
                        final_mapping[field] = name
                        break

            # Drop recurring_flag if present (as per requirements)
            if 'recurring_flag' in df.columns:
                df = df.drop(columns=['recurring_flag'])
                logger.info("Dropped recurring_flag column")

            # Convert to list of dictionaries with enhanced processing
            transactions = []
            for _, row in df.iterrows():
                # Extract basic fields using mapping
                date_val = str(row.get(final_mapping.get('date', 'date'), ''))
                amount_str = str(row.get(final_mapping.get('amount', 'amount'), ''))
                description = str(row.get(final_mapping.get('description', 'description'), ''))
                original_merchant = str(row.get(final_mapping.get('merchant', 'merchant'), ''))
                original_category = str(row.get(final_mapping.get('category', 'category'), ''))

                # Enhanced category classification
                enhanced_category = self._classify_transaction_smart(description, original_merchant, amount_str)

                # Enhanced merchant extraction
                enhanced_merchant = self._extract_merchant_smart(description) if not original_merchant else original_merchant

                # Use enhanced values if they seem more accurate
                final_category = enhanced_category if enhanced_category != 'miscellaneous' else original_category
                final_merchant = enhanced_merchant if enhanced_merchant else original_merchant

                transaction = {
                    'input_type': 'structured',
                    'date': date_val,
                    'amount': amount_str,
                    'description': description,
                    'category': final_category,
                    'merchant': final_merchant,
                    'payment_method': str(row.get('payment_method', '')),
                    'offer_discount': str(row.get('offer_discount', ''))
                }
                transactions.append(transaction)

            logger.info(f"Parsed {len(transactions)} transactions from structured data with enhanced classification")
            return transactions

        except Exception as e:
            logger.error(f"Error parsing CSV data: {e}")
            raise

    def validate_data(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate parsed transaction data"""
        valid_transactions = []

        for i, txn in enumerate(transactions):
            # Check if required fields have values
            if not txn.get('date') or not txn.get('amount') or not txn.get('description'):
                logger.warning(f"Transaction {i} missing required fields, skipping")
                continue

            valid_transactions.append(txn)

        logger.info(f"Validated {len(valid_transactions)} out of {len(transactions)} transactions")
        return valid_transactions

    def _classify_transaction_smart(self, description: str, merchant: str = "", amount_str: str = "0") -> str:
        """Enhanced transaction classification using context"""
        import re

        # Enhanced category keywords with better context
        enhanced_categories = {
            'housing': [
                'rent', 'rental', 'monthly rent', 'apartment', 'mortgage', 'property tax',
                'housing', 'lease', 'landlord', 'property management'
            ],
            'groceries': [
                'grocery', 'groceries', 'supermarket', 'walmart', 'target', 'costco',
                'kroger', 'safeway', 'market', 'weekly grocery', 'weekly groceries',
                'food shopping', 'grocery store', 'food market'
            ],
            'transportation': [
                'gas', 'fuel', 'uber', 'lyft', 'taxi', 'bus', 'train', 'metro',
                'parking', 'toll', 'car insurance', 'auto insurance', 'vehicle',
                'oil change', 'car maintenance', 'public transport', 'quarterly payment'
            ],
            'food_dining': [
                'restaurant', 'cafe', 'coffee', 'dinner', 'lunch', 'breakfast',
                'food', 'eat', 'dining', 'pizza', 'burger', 'starbucks', 'mcdonalds',
                'business lunch', 'client lunch', 'meeting', 'takeout', 'delivery'
            ],
            'shopping': [
                'shopping', 'clothes', 'clothing', 'shoes', 'amazon', 'ebay', 'mall',
                'store', 'laptop', 'computer', 'electronics', 'new laptop', 'work equipment'
            ],
            'entertainment': [
                'movie', 'cinema', 'netflix', 'spotify', 'game', 'entertainment',
                'concert', 'theater', 'streaming', 'subscription', 'premium subscription'
            ],
            'utilities': [
                'electric', 'electricity', 'water', 'gas bill', 'internet', 'phone',
                'cable', 'utility', 'monthly bill', 'power bill', 'heating'
            ],
            'business': [
                'business', 'office', 'work', 'professional', 'meeting', 'client',
                'supplies', 'equipment', 'software', 'conference'
            ],
            'income': [
                'salary', 'paycheck', 'wage', 'direct deposit', 'payroll', 'income',
                'bonus', 'freelance', 'consulting', 'revenue'
            ],
            'financial_services': [
                'bank', 'atm', 'withdrawal', 'transfer', 'fee', 'service charge',
                'overdraft', 'interest', 'loan', 'credit'
            ]
        }

        text = f"{description} {merchant}".lower().strip()

        # Convert amount to check for income
        try:
            amount_val = float(re.sub(r'[^\d.-]', '', amount_str) or '0')
        except:
            amount_val = 0

        # Income detection (positive amounts)
        if amount_val > 0:
            for keyword in enhanced_categories['income']:
                if keyword in text:
                    return 'income'

        # Enhanced classification with context
        for category, keywords in enhanced_categories.items():
            if category == 'income':  # Skip income for expenses
                continue

            for keyword in keywords:
                if keyword in text:
                    # Special context-aware handling
                    if category == 'transportation' and ('insurance' in text or 'quarterly' in text):
                        return 'transportation'
                    elif category == 'housing' and ('monthly' in text and 'rent' in text):
                        return 'housing'
                    elif category == 'business' and ('business' in text or 'work' in text or 'client' in text):
                        return 'business'
                    elif category == 'food_dining' and any(x in text for x in ['lunch', 'client', 'business', 'meeting']):
                        return 'food_dining'
                    else:
                        return category

        # Fallback pattern matching
        if 'atm' in text or 'withdrawal' in text:
            return 'financial_services'
        elif 'monthly' in text and any(word in text for word in ['bill', 'payment', 'subscription']):
            return 'utilities'
        elif any(word in text for word in ['new', 'purchase', 'buy', 'bought']):
            return 'shopping'

        return 'miscellaneous'

    def _extract_merchant_smart(self, description: str) -> str:
        """Enhanced merchant extraction with better accuracy"""
        import re

        description = description.strip()

        # Merchant extraction patterns
        merchant_patterns = [
            r'(?:at|from)\s+([A-Za-z][A-Za-z\s&\'-]+?)(?:\s+(?:store|restaurant|cafe|shop))?(?:\s|$|,|\.|for)',
            r'([A-Za-z][A-Za-z\s&\'-]+?)\s+(?:payment|bill|subscription)',
            r'(?:bought|purchased|from)\s+([A-Za-z][A-Za-z\s&\'-]+?)(?:\s|$|,)',
            r'([A-Za-z][A-Za-z\s&\'-]+?)\s+(?:service|premium|subscription)'
        ]

        for pattern in merchant_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip().title()
                if len(merchant) > 2 and merchant not in ['The', 'And', 'For', 'With', 'Monthly', 'Weekly']:
                    return merchant

        # Fallback: look for capitalized words
        words = description.split()
        for word in words:
            if word and word[0].isupper() and len(word) > 2:
                if not word.lower() in ['monthly', 'weekly', 'daily', 'new', 'business', 'client']:
                    return word

        return ""
