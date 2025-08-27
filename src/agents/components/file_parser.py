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
        """Parse CSV data into standardized format"""
        try:
            # Normalize column names
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # Check for required columns
            missing_required = [col for col in self.required_columns if col not in df.columns]
            if missing_required:
                logger.warning(f"Missing required columns: {missing_required}")
            
            # Drop recurring_flag if present (as per requirements)
            if 'recurring_flag' in df.columns:
                df = df.drop(columns=['recurring_flag'])
                logger.info("Dropped recurring_flag column")
            
            # Convert to list of dictionaries
            transactions = []
            for _, row in df.iterrows():
                transaction = {
                    'input_type': 'structured',
                    'date': str(row.get('date', '')),
                    'amount': str(row.get('amount', '')),
                    'description': str(row.get('description', '')),
                    'category': str(row.get('category', '')),
                    'merchant': str(row.get('merchant', '')),
                    'payment_method': str(row.get('payment_method', '')),
                    'offer_discount': str(row.get('offer_discount', ''))
                }
                transactions.append(transaction)
            
            logger.info(f"Parsed {len(transactions)} transactions from structured data")
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
