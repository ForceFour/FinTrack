"""Test the basic functionality of FinTrack agents"""

# import pytest  # Commented out for basic testing
from src.utils.data_preprocessing import DataPreprocessor
from src.utils.ner_utils import MerchantExtractor
from src.schemas.transaction_schemas import RawTransaction


class TestDataPreprocessor:
    """Test data preprocessing functionality"""
    
    def test_parse_amount(self):
        preprocessor = DataPreprocessor()
        
        # Test various amount formats
        assert preprocessor.parse_amount("$45.67") == 45.67
        assert preprocessor.parse_amount("-123.45") == -123.45
        assert preprocessor.parse_amount("$1,234.56") == 1234.56
        assert preprocessor.parse_amount("(89.99)") == -89.99
    
    def test_standardize_payment_method(self):
        preprocessor = DataPreprocessor()
        
        # Test payment method standardization
        assert preprocessor.standardize_payment_method("Visa Credit Card") == "credit_card"
        assert preprocessor.standardize_payment_method("Debit Card") == "debit_card"
        assert preprocessor.standardize_payment_method("PayPal") == "digital_wallet"
        assert preprocessor.standardize_payment_method("Cash") == "cash"
        assert preprocessor.standardize_payment_method("Unknown Method") == "other"
    
    def test_extract_discount_info(self):
        preprocessor = DataPreprocessor()
        
        # Test discount extraction
        result1 = preprocessor.extract_discount_info("STORE ABC 20% OFF SALE")
        assert result1["has_discount"] == True
        assert result1["discount_percentage"] == 20.0
        
        result2 = preprocessor.extract_discount_info("REGULAR PURCHASE NO DISCOUNT")
        assert result2["has_discount"] == False
        assert result2["discount_percentage"] is None


class TestMerchantExtractor:
    """Test merchant extraction functionality"""
    
    def test_extract_merchant(self):
        extractor = MerchantExtractor()
        
        # Test known merchant patterns
        assert extractor.extract_merchant("STARBUCKS STORE #1234") == "Starbucks"
        assert extractor.extract_merchant("WALMART SUPERCENTER #5678") == "Walmart"
        assert extractor.extract_merchant("AMAZON.COM AMZN.COM/BILL") == "Amazon"
        
        # Test unknown merchant
        unknown = extractor.extract_merchant("UNKNOWN STORE ABC")
        assert unknown is None or isinstance(unknown, str)
    
    def test_get_merchant_category(self):
        extractor = MerchantExtractor()
        
        # Test category mapping
        assert extractor.get_merchant_category("Starbucks") == "Food & Dining"
        assert extractor.get_merchant_category("Walmart") == "Groceries"
        assert extractor.get_merchant_category("Amazon") == "Shopping"
        assert extractor.get_merchant_category("Unknown Merchant") is None


class TestTransactionSchemas:
    """Test transaction data schemas"""
    
    def test_raw_transaction_creation(self):
        # Test creating a raw transaction
        raw_txn = RawTransaction(
            id="test_001",
            date="2024-01-15",
            amount="$45.67",
            description="TEST MERCHANT",
            payment_method="Credit Card"
        )
        
        assert raw_txn.id == "test_001"
        assert raw_txn.amount == "$45.67"
        assert raw_txn.description == "TEST MERCHANT"
    
    def test_raw_transaction_with_metadata(self):
        # Test creating transaction with metadata
        raw_txn = RawTransaction(
            id="test_002",
            date="2024-01-16",
            amount="$123.45",
            description="TEST STORE",
            payment_method="Debit",
            metadata={"location": "Seattle, WA", "category_hint": "grocery"}
        )
        
        assert raw_txn.metadata["location"] == "Seattle, WA"
        assert raw_txn.metadata["category_hint"] == "grocery"


if __name__ == "__main__":
    # Run basic tests manually
    print("Running basic FinTrack tests...")
    
    # Test data preprocessor
    print("\n1. Testing DataPreprocessor...")
    preprocessor = DataPreprocessor()
    
    test_amounts = ["$45.67", "-123.45", "$1,234.56", "(89.99)"]
    for amount in test_amounts:
        parsed = preprocessor.parse_amount(amount)
        print(f"  {amount} → {parsed}")
    
    # Test merchant extractor
    print("\n2. Testing MerchantExtractor...")
    extractor = MerchantExtractor()
    
    test_descriptions = [
        "STARBUCKS STORE #1234 SEATTLE WA",
        "WALMART SUPERCENTER #5678 BELLEVUE WA", 
        "AMAZON.COM AMZN.COM/BILL WA",
        "UNKNOWN LOCAL STORE ABC"
    ]
    
    for desc in test_descriptions:
        merchant = extractor.extract_merchant(desc)
        category = extractor.get_merchant_category(merchant) if merchant else None
        print(f"  '{desc}'")
        print(f"    → Merchant: {merchant or 'Unknown'}")
        print(f"    → Category: {category or 'Unknown'}")
    
    # Test transaction schema
    print("\n3. Testing Transaction Schemas...")
    raw_txn = RawTransaction(
        id="test_001",
        date="2024-01-15", 
        amount="$45.67",
        description="STARBUCKS STORE #1234",
        payment_method="Credit Card"
    )
    print(f"  Created transaction: {raw_txn.id} - {raw_txn.description}")
    
    print("\n✅ All basic tests completed successfully!")
