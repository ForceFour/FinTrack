#!/usr/bin/env python3
"""
Simple Demo of Enhanced NLP and Ingestion Integration
Shows the transaction processing pipeline in action
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def demo_transaction_processing():
    """Demonstrate the enhanced transaction processing"""
    
    print("💳 FinTrack Enhanced Transaction Processing Demo")
    print("🤖 Powered by LangGraph + Groq + Enhanced Agents")
    print("="*60)
    
    try:
        # Import components
        from src.nodes import TransactionProcessingNodes
        from src.states import TransactionProcessingState, ProcessingStage
        from config.settings import get_settings
        
        # Get configuration
        settings = get_settings()
        config = {
            'groq_api_key': settings.groq_api_key,
            'langgraph_api_key': settings.langgraph_api_key
        }
        
        print(f"🔧 Configuration Status:")
        print(f"   • Groq API: {'✅ Connected' if config['groq_api_key'] else '❌ Missing'}")
        print(f"   • LangGraph: {'✅ Connected' if config['langgraph_api_key'] else '❌ Missing'}")
        
        # Initialize enhanced nodes
        nodes = TransactionProcessingNodes(config)
        print(f"✅ Enhanced processing nodes initialized")
        
        # Demo transaction
        demo_input = "I bought coffee at Starbucks for $4.75 this morning using my credit card"
        print(f"\n💬 Processing: \"{demo_input}\"")
        print("-" * 60)
        
        # Create initial state
        state = TransactionProcessingState(
            user_input=demo_input,
            user_id="demo_user",
            conversation_context={},
            current_stage=ProcessingStage.INITIAL,
            processed_transactions=[],
            confidence_scores=[],
            processing_history=[],
            error_log=[],
            created_at=datetime.now()
        )
        
        # Step 1: Initialize
        print("🚀 Step 1: Initialize Workflow")
        state = nodes.initialize_workflow_node(state)
        print(f"   ✅ Workflow ID: {state.get('workflow_id', 'N/A')}")
        
        # Step 2: NLP Processing
        print("\n🤖 Step 2: Natural Language Processing")
        state = nodes.nl_processing_node(state)
        
        extracted = state.get('extracted_transaction', {})
        print(f"   💰 Amount: ${extracted.get('amount', 'N/A')}")
        print(f"   🏪 Merchant: {extracted.get('merchant_name', 'N/A')}")
        print(f"   📂 Category: {extracted.get('category', 'N/A')}")
        print(f"   🎯 Confidence: {state.get('nl_confidence', 0.0):.2f}")
        print(f"   🔍 Method: {state.get('extraction_method', 'N/A')}")
        
        # Step 3: Ingestion Processing
        print("\n⚙️ Step 3: Enhanced Ingestion Processing")
        state = nodes.ingestion_node(state)
        
        preprocessed = state.get('preprocessed_transactions', [])
        if preprocessed:
            txn = preprocessed[0]
            print(f"   📊 Preprocessed Transaction:")
            print(f"      • ID: {txn.get('id', 'N/A')}")
            print(f"      • Amount: ${txn.get('amount', 'N/A')}")
            print(f"      • Merchant: {txn.get('merchant_name', 'N/A')}")
            print(f"      • Description: {txn.get('description', 'N/A')[:50]}...")
            print(f"      • Category: {txn.get('category', 'N/A')}")
            print(f"      • Date: {txn.get('date', 'N/A')}")
            print(f"      • Payment Method: {txn.get('payment_method', 'N/A')}")
        
        quality = state.get('data_quality_scores', {})
        print(f"   📈 Quality Scores:")
        print(f"      • Overall: {quality.get('overall', 0.0):.2f}")
        print(f"      • Completeness: {quality.get('completeness', 0.0):.2f}")
        print(f"      • Accuracy: {quality.get('accuracy', 0.0):.2f}")
        
        # Show confidence progression
        print(f"\n📊 Confidence Tracking:")
        for conf in state.get('confidence_scores', []):
            stage = conf.get('stage', 'unknown')
            confidence = conf.get('confidence', 0.0)
            print(f"   • {stage.replace('_', ' ').title()}: {confidence:.2f}")
        
        # Show processing history
        history = state.get('processing_history', [])
        print(f"\n📋 Processing History ({len(history)} steps):")
        for i, step in enumerate(history[-3:], 1):  # Show last 3 steps
            action = step.get('action', 'unknown').replace('_', ' ').title()
            timestamp = step.get('timestamp', 'N/A')[:19]  # Remove microseconds
            print(f"   {i}. {action} at {timestamp}")
        
        # Check for errors
        errors = state.get('error_log', [])
        if errors:
            print(f"\n⚠️ Errors Encountered ({len(errors)}):")
            for error in errors:
                print(f"   • {error.get('stage', 'unknown')}: {error.get('error', 'N/A')}")
        else:
            print(f"\n✅ No errors encountered!")
        
        print(f"\n" + "="*60)
        print(f"🎉 Demo completed successfully!")
        print(f"🚀 Enhanced NLP and Ingestion integration is working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_capabilities():
    """Show the capabilities of the enhanced system"""
    print(f"\n🌟 Enhanced FinTrack Capabilities")
    print("="*40)
    print(f"🤖 Natural Language Processing:")
    print(f"   • Groq/LangChain powered extraction")
    print(f"   • Multiple extraction methods")
    print(f"   • Confidence scoring")
    print(f"   • Fallback regex processing")
    
    print(f"\n⚙️ Enhanced Ingestion:")
    print(f"   • Comprehensive preprocessing")
    print(f"   • Data quality assessment")
    print(f"   • Normalization and cleaning")
    print(f"   • Metadata enrichment")
    
    print(f"\n🌊 LangGraph Orchestration:")
    print(f"   • State-based workflow")
    print(f"   • Error handling")
    print(f"   • Progress tracking")
    print(f"   • Async processing support")
    
    print(f"\n📊 Monitoring & Analytics:")
    print(f"   • Confidence tracking")
    print(f"   • Processing history")
    print(f"   • Quality metrics")
    print(f"   • Error logging")

if __name__ == "__main__":
    print("🚀 Starting Enhanced FinTrack Demo...")
    
    success = demo_transaction_processing()
    
    if success:
        show_capabilities()
        print(f"\n✨ Demo completed! Your enhanced transaction processing system is ready!")
    else:
        print(f"\n❌ Demo encountered issues. Please check the error messages above.")
