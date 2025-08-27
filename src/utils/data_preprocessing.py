"""
Comprehensive Data Preprocessing - Implements the exact preprocessing pipeline
"""

import re
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Comprehensive data preprocessor that implements the exact pipeline:
    
    Step 1: Cleanup - Column normalization, drop unused columns
    Step 2: Date Processing - Extract date components  
    Step 3: Amount Handling - Outlier detection, log transform
    Step 4: Discounts - Extract percentages, calculate values
    Step 5: Encoding - One-hot for categories/payment, frequency for merchant
    Step 6: Description Cleaning - Text normalization
    Step 7: Column management - Drop raw columns, rearrange
    """
    
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
        
        self.final_column_order = [
            # Date features
            'year', 'month', 'day', 'day_of_week',
            # Transaction basics
            'amount', 'is_outlier', 'amount_log',
            'discount_percent', 'discount_value', 'effective_amount',
            # Merchant & Offer
            'merchant_encoded', 'offer_applied',
            # Payment Method One-Hot (will be dynamically determined)
            # Category One-Hot (will be dynamically determined)
            # Text features
            'description_clean'
        ]
    
    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the complete preprocessing pipeline to a DataFrame"""
        logger.info("Starting comprehensive preprocessing pipeline")
        
        # Step 1: Cleanup
        df1 = self._step1_cleanup(df.copy())
        
        # Step 2: Date Processing  
        df2 = self._step2_date_processing(df1)
        
        # Step 3: Amount Handling
        df3 = self._step3_amount_handling(df2)
        
        # Step 4: Discounts
        df4 = self._step4_discounts(df3)
        
        # Step 5: Encoding
        df5 = self._step5_encoding(df4)
        
        # Step 6: Description Cleaning
        df6 = self._step6_description_cleaning(df5)
        
        # Step 7: Drop unwanted columns & rearrange
        df_final = self._step7_column_management(df6)
        
        logger.info(f"Preprocessing complete. Final shape: {df_final.shape}")
        return df_final
    
    def _step1_cleanup(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 1: Cleanup - normalize columns, drop unused"""
        logger.debug("Step 1: Cleanup")
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        
        # Drop unused columns if any
        if "recurring_flag" in df.columns:
            df.drop(columns=["recurring_flag"], inplace=True)
            logger.debug("Dropped recurring_flag column")
        
        return df
    
    def _step2_date_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 2: Date Processing - extract date components"""
        logger.debug("Step 2: Date Processing")
        
        df = df.copy()
        
        # Convert to datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Extract date components
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
        
        return df
    
    def _step3_amount_handling(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 3: Amount Handling - outlier detection, log transform"""
        logger.debug("Step 3: Amount Handling")
        
        df = df.copy()
        
        # Detect anomalies using IQR
        Q1 = df['amount'].quantile(0.25)
        Q3 = df['amount'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        df['is_outlier'] = ((df['amount'] < lower_bound) | (df['amount'] > upper_bound)).astype(int)
        
        # Log-transform for stability
        df['amount_log'] = np.log1p(df['amount'])  # log1p = log(1 + x)
        
        logger.debug(f"Found {df['is_outlier'].sum()} outliers out of {len(df)} transactions")
        return df
    
    def _step4_discounts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 4: Discounts - extract percentages, calculate values"""
        logger.debug("Step 4: Discounts")
        
        df = df.copy()
        
        # Handle discount column - try different possible names
        discount_col = None
        possible_discount_cols = ['offer/discount_applied', 'offer_discount', 'discount', 'offer']
        
        for col in possible_discount_cols:
            if col in df.columns:
                discount_col = col
                break
        
        if discount_col:
            # Create discount_percent column
            df['discount_percent'] = (
                df[discount_col]
                .astype(str)
                .str.extract(r'(\d+)%')  # extract number before %
                .fillna(0)  # replace NaN with 0
                .astype(float)  # convert to float
            )
            
            # Calculate discount value
            df['discount_value'] = df['amount'] * (df['discount_percent'] / 100)
            
            # Calculate effective amount
            df['effective_amount'] = df['amount'] - df['discount_value']
        else:
            # No discount column found, create defaults
            df['discount_percent'] = 0.0
            df['discount_value'] = 0.0
            df['effective_amount'] = df['amount']
            logger.warning("No discount column found, using default values")
        
        return df
    
    def _step5_encoding(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 5: Encoding - category/payment one-hot, merchant frequency"""
        logger.debug("Step 5: Encoding")
        
        df = df.copy()
        
        # Category (few values → One-hot)
        if 'category' in df.columns:
            df = pd.get_dummies(df, columns=['category'], prefix='cat')
            logger.debug("Applied one-hot encoding to category")
        
        # Merchant (many values → Frequency Encode)
        if 'merchant' in df.columns:
            merchant_freq = df['merchant'].value_counts(normalize=True)  # normalized frequency
            df['merchant_encoded'] = df['merchant'].map(merchant_freq)
            logger.debug(f"Applied frequency encoding to {len(merchant_freq)} unique merchants")
        else:
            df['merchant_encoded'] = 0.0
        
        # Payment Method (few values → One-hot)
        if 'payment_method' in df.columns:
            df = pd.get_dummies(df, columns=['payment_method'], prefix='pay')
            logger.debug("Applied one-hot encoding to payment_method")
        
        # Offer Applied
        discount_col = None
        possible_discount_cols = ['offer/discount_applied', 'offer_discount', 'discount', 'offer']
        
        for col in possible_discount_cols:
            if col in df.columns:
                discount_col = col
                break
        
        if discount_col:
            df['offer_applied'] = df[discount_col].astype(str).str.contains("Yes", case=False, na=False).astype(int)
        else:
            df['offer_applied'] = 0
        
        return df
    
    def _step6_description_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 6: Description Cleaning - text normalization"""
        logger.debug("Step 6: Description Cleaning")
        
        df = df.copy()
        
        # Find description column
        desc_col = None
        possible_desc_cols = ['transaction_description', 'description', 'desc']
        
        for col in possible_desc_cols:
            if col in df.columns:
                desc_col = col
                break
        
        if desc_col:
            df['description_clean'] = df[desc_col].astype(str).apply(self._clean_description)
            logger.debug("Applied description cleaning")
        else:
            df['description_clean'] = ""
            logger.warning("No description column found")
        
        return df
    
    def _clean_description(self, text: str) -> str:
        """Clean individual description text"""
        if pd.isna(text) or text == 'nan':
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove numbers (keep if meaningful, but usually IDs are noise)
        text = re.sub(r'\d+', ' ', text)
        
        # Remove special characters (keep only alphabets and spaces)
        text = re.sub(r'[^a-z\s]', ' ', text)
        
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _step7_column_management(self, df: pd.DataFrame) -> pd.DataFrame:
        """Step 7: Drop unwanted columns & rearrange"""
        logger.debug("Step 7: Column Management")
        
        df = df.copy()
        
        # Columns to drop (raw/original, since we have encoded or cleaned versions)
        cols_to_drop = []
        
        # Standard columns to drop if they exist
        potential_drop_cols = [
            'date', 'merchant', 'offer/discount_applied', 'transaction_description',
            'offer_discount', 'discount', 'offer', 'description', 'desc'
        ]
        
        for col in potential_drop_cols:
            if col in df.columns:
                cols_to_drop.append(col)
        
        # Save dropped columns for analysis (optional)
        if cols_to_drop:
            logger.debug(f"Dropping columns: {cols_to_drop}")
            df = df.drop(columns=cols_to_drop)
        
        # Get current columns and organize them
        available_cols = df.columns.tolist()
        
        # Build final column order based on what's available
        final_order = []
        
        # Date features
        date_cols = ['year', 'month', 'day', 'day_of_week']
        final_order.extend([col for col in date_cols if col in available_cols])
        
        # Transaction basics
        basic_cols = ['amount', 'is_outlier', 'amount_log', 'discount_percent', 'discount_value', 'effective_amount']
        final_order.extend([col for col in basic_cols if col in available_cols])
        
        # Merchant & Offer
        merchant_offer_cols = ['merchant_encoded', 'offer_applied']
        final_order.extend([col for col in merchant_offer_cols if col in available_cols])
        
        # Payment Method One-Hot (pay_*)
        pay_cols = [col for col in available_cols if col.startswith('pay_')]
        final_order.extend(sorted(pay_cols))
        
        # Category One-Hot (cat_*)
        cat_cols = [col for col in available_cols if col.startswith('cat_')]
        final_order.extend(sorted(cat_cols))
        
        # Text features
        if 'description_clean' in available_cols:
            final_order.append('description_clean')
        
        # Add any remaining columns not accounted for
        remaining_cols = [col for col in available_cols if col not in final_order]
        final_order.extend(remaining_cols)
        
        # Reorder columns
        df = df[final_order]
        
        logger.debug(f"Final column order: {df.columns.tolist()}")
        return df
    
    def get_schema_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get information about the processed schema"""
        return {
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "date_features": [col for col in df.columns if col in ['year', 'month', 'day', 'day_of_week']],
            "amount_features": [col for col in df.columns if col in ['amount', 'is_outlier', 'amount_log', 'discount_percent', 'discount_value', 'effective_amount']],
            "encoded_features": [col for col in df.columns if col.startswith(('pay_', 'cat_')) or col in ['merchant_encoded', 'offer_applied']],
            "text_features": [col for col in df.columns if col in ['description_clean']],
            "shape": df.shape,
            "ready_for_modeling": True
        }
    
    # Legacy methods for backward compatibility
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
        cleaned = re.sub(r'[$€£¥₹,\s]', '', str(amount_str))
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


# Alias for the comprehensive preprocessor
ComprehensivePreprocessor = DataPreprocessor
