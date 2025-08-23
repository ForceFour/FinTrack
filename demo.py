"""Demo script to showcase FinTrack functionality"""

import asyncio
import json
from typing import List, Dict, Any
from src.schemas.transaction_schemas import RawTransaction
from src.workflows.transaction_workflow import TransactionWorkflow


def get_sample_transactions() -> List[RawTransaction]:
    """Get sample transaction data for demonstration"""
    return [
        RawTransaction(
            id="txn_001",
            date="2024-01-15",
            amount="$45.67",
            description="STARBUCKS STORE #1234 SEATTLE WA",
            payment_method="Visa Credit Card"
        ),
        RawTransaction(
            id="txn_002",
            date="01/16/2024",
            amount="-123.45",
            description="WALMART SUPERCENTER #5678 BELLEVUE WA",
            payment_method="Debit Card"
        ),
        RawTransaction(
            id="txn_003",
            date="2024-01-17 14:30:00",
            amount="$89.99",
            description="AMAZON.COM AMZN.COM/BILL WA",
            payment_method="Credit Card"
        ),
        RawTransaction(
            id="txn_004",
            date="2024-01-18",
            amount="$12.50",
            description="MCDONALD'S #9876 REDMOND WA",
            payment_method="Apple Pay"
        ),
        RawTransaction(
            id="txn_005",
            date="2024-01-19",
            amount="$250.00",
            description="SHELL GAS STATION #1111 SEATTLE WA",
            payment_method="Credit Card"
        ),
        RawTransaction(
            id="txn_006",
            date="2024-01-20",
            amount="$9.99",
            description="SPOTIFY PREMIUM SUBSCRIPTION",
            payment_method="PayPal"
        ),
        RawTransaction(
            id="txn_007",
            date="2024-01-21",
            amount="$156.78",
            description="TARGET STORE T-1234 BELLEVUE WA",
            payment_method="Debit Card"
        ),
        RawTransaction(
            id="txn_008",
            date="2024-01-22",
            amount="$35.20",
            description="UBER EATS ORDER #AB123 SEATTLE WA",
            payment_method="Credit Card"
        )
    ]


async def demo_complete_pipeline():
    """Demonstrate the complete 6-agent pipeline"""
    print("🚀 FinTrack Demo - Complete 6-Agent Pipeline")
    print("=" * 50)
    
    # Initialize workflow
    workflow = TransactionWorkflow()
    
    # Get sample data
    sample_transactions = get_sample_transactions()
    
    print(f"📊 Processing {len(sample_transactions)} sample transactions...")
    print("\nSample transactions:")
    for i, txn in enumerate(sample_transactions[:3], 1):
        print(f"  {i}. {txn.description} - {txn.amount}")
    print(f"  ... and {len(sample_transactions) - 3} more")
    
    try:
        # Process through complete pipeline
        print("\n🔄 Running complete pipeline...")
        result = await workflow.process_transactions(sample_transactions)
        
        print("\n✅ Pipeline completed successfully!")
        print("\n📈 Results Summary:")
        print(f"  • Processed Transactions: {len(result.get('processed_transactions', []))}")
        print(f"  • Pattern Insights: {len(result.get('insights', []))}")
        print(f"  • Suggestions Generated: {len(result.get('suggestions', []))}")
        print(f"  • Security Alerts: {len(result.get('security_alerts', []))}")
        
        # Display some sample results
        if result.get('processed_transactions'):
            print("\n💳 Sample Processed Transaction:")
            txn = result['processed_transactions'][0]
            print(f"  • Merchant: {txn.get('merchant_standardized', 'Unknown')}")
            print(f"  • Category: {txn.get('predicted_category', 'Unknown')}")
            print(f"  • Confidence: {txn.get('prediction_confidence', 0):.2f}")
        
        if result.get('insights'):
            print("\n🔍 Sample Insight:")
            insight = result['insights'][0]
            print(f"  • Type: {insight.get('insight_type', 'Unknown')}")
            print(f"  • Description: {insight.get('description', 'No description')}")
        
        if result.get('suggestions'):
            print("\n💡 Sample Suggestion:")
            suggestion = result['suggestions'][0]
            print(f"  • Title: {suggestion.get('title', 'No title')}")
            print(f"  • Description: {suggestion.get('description', 'No description')}")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return None
    
    return result


def demo_individual_agents():
    """Demonstrate individual agent functionality"""
    print("\n🤖 Individual Agent Demonstrations")
    print("=" * 40)
    
    from src.agents.ingestion_agent import IngestionAgent
    from src.utils.data_preprocessing import DataPreprocessor
    from src.utils.ner_utils import MerchantExtractor
    
    # Demo Ingestion Agent
    print("\n1️⃣ Ingestion Agent Demo")
    print("-" * 25)
    
    preprocessor = DataPreprocessor()
    sample_raw = get_sample_transactions()[0]
    
    print(f"Raw transaction: {sample_raw.description}")
    print(f"Raw amount: {sample_raw.amount}")
    
    # Process amount
    processed_amount = preprocessor.parse_amount(sample_raw.amount)
    print(f"Processed amount: ${processed_amount:.2f}")
    
    # Process payment method
    processed_payment = preprocessor.standardize_payment_method(sample_raw.payment_method)
    print(f"Standardized payment method: {processed_payment}")
    
    # Demo NER/Merchant Agent
    print("\n2️⃣ NER/Merchant Agent Demo")
    print("-" * 30)
    
    merchant_extractor = MerchantExtractor()
    
    for txn in get_sample_transactions()[:3]:
        merchant = merchant_extractor.extract_merchant(txn.description)
        category = merchant_extractor.get_merchant_category(merchant) if merchant else None
        print(f"'{txn.description}'")
        print(f"  → Merchant: {merchant or 'Unknown'}")
        print(f"  → Category: {category or 'Unknown'}")
        print()


def demo_api_usage():
    """Show example API usage"""
    print("\n🌐 API Usage Examples")
    print("=" * 25)
    
    print("Start the API server:")
    print("  uv run uvicorn src.api.main:app --reload --port 8000")
    print()
    
    print("Example API calls:")
    print("1. Health check:")
    print("   curl http://localhost:8000/health")
    print()
    
    print("2. Process transactions:")
    print("   curl -X POST http://localhost:8000/transactions/process \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '[{\"id\":\"txn_001\",\"date\":\"2024-01-15\",\"amount\":\"$45.67\",\"description\":\"STARBUCKS\",\"payment_method\":\"Credit\"}]'")
    print()
    
    print("3. Get agent status:")
    print("   curl http://localhost:8000/agents/status")


def main():
    """Main demo function"""
    print("🏦 Welcome to FinTrack - Financial Transaction Analysis System")
    print("=" * 60)
    print()
    print("This demo showcases the 6-agent pipeline for processing financial transactions:")
    print("1. 🔄 Ingestion Agent - Normalizes raw data")
    print("2. 🏪 NER/Merchant Agent - Extracts merchant info")
    print("3. 🏷️ Classifier Agent - Predicts categories")
    print("4. 📊 Pattern Analyzer Agent - Detects patterns")
    print("5. 💡 Suggestion Agent - Generates recommendations")
    print("6. 🛡️ Safety Guard Agent - Flags anomalies")
    print()
    
    # Run individual agent demos first
    demo_individual_agents()
    
    # Show API usage examples
    demo_api_usage()
    
    # Run complete pipeline demo
    print("\n" + "=" * 60)
    print("Running complete pipeline demo...")
    result = asyncio.run(demo_complete_pipeline())
    
    if result:
        print("\n✨ Demo completed successfully!")
        print("\nNext steps:")
        print("• Start the API server: uv run uvicorn src.api.main:app --reload")
        print("• Run tests: uv run pytest")
        print("• Check the documentation in the README.md")
    else:
        print("\n⚠️ Demo encountered issues. Please check the error messages above.")


if __name__ == "__main__":
    main()
