#!/usr/bin/env python3
"""
Quick test to verify ingestion fixes
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from src.workflows.transaction_workflow import TransactionProcessingWorkflow

async def test_ingestion_fix():
    """Test the ingestion fixes with a simple transaction"""
    print("🧪 Testing Ingestion Fixes")
    print("=" * 50)
    
    workflow = TransactionProcessingWorkflow()
    
    # Simple test case
    test_input = "I spent $4.50 at Starbucks this morning for coffee"
    user_id = "test_user_001"
    
    print(f"📝 Input: {test_input}")
    print()
    
    try:
        result = await workflow.process_transaction(
            user_input=test_input,
            user_id=user_id
        )
        
        print("\n📊 RESULTS:")
        print("=" * 30)
        
        # Check preprocessed transactions
        preprocessed = result.get('preprocessed_transactions', [])
        print(f"✅ Preprocessed transactions: {len(preprocessed)}")
        
        if preprocessed:
            txn = preprocessed[0]
            print(f"   • Amount: ${txn.get('amount', 'N/A')}")
            print(f"   • Merchant: {txn.get('merchant_name', 'N/A')}")
            print(f"   • Category: {txn.get('category', 'N/A')}")
            print(f"   • ID: {txn.get('id', 'N/A')}")
        
        # Check confidence scores
        ingestion_confidence = result.get('ingestion_confidence', 0.0)
        print(f"📈 Ingestion confidence: {ingestion_confidence:.2f}")
        
        # Check errors
        errors = result.get('error_log', [])
        print(f"⚠️ Errors: {len(errors)}")
        for error in errors:
            print(f"   • {error.get('stage', 'unknown')}: {error.get('error', 'unknown error')}")
        
        # Success check
        if preprocessed and len(preprocessed) > 0:
            print("\n🎉 SUCCESS: Ingestion working correctly!")
            return True
        else:
            print("\n❌ FAIL: No transactions were processed")
            return False
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ingestion_fix())
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
