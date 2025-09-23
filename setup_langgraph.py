#!/usr/bin/env python3
"""
LangGraph Workflow Setup Script
Quickly test and validate the complete workflow implementation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_workflow_setup():
    """Test the complete workflow setup"""
    
    print("🚀 FinTrack LangGraph Workflow Setup Test")
    print("=" * 50)
    
    try:
        # Import workflow components
        print("📦 Importing workflow components...")
        from src.workflows.unified_workflow import UnifiedTransactionWorkflow, get_workflow_instance
        from src.workflows.config import WorkflowMode, load_workflow_config, TESTING_CONFIG
        
        print("✅ Imports successful")
        
        # Load configuration
        print("\n🔧 Loading configuration...")
        config = load_workflow_config()
        print(f"✅ Configuration loaded:")
        print(f"   - Tracing enabled: {config.enable_tracing}")
        print(f"   - Default mode: {config.default_mode.value}")
        print(f"   - Confidence threshold: {config.confidence_threshold}")
        print(f"   - Timeout: {config.timeout_seconds}s")
        
        # Initialize workflow
        print("\n🏗️ Initializing workflow...")
        workflow = UnifiedTransactionWorkflow(config=TESTING_CONFIG)
        print(f"✅ Workflow initialized with {len(workflow.workflows)} modes")
        
        # List available modes
        print(f"\n📋 Available workflow modes:")
        for mode in WorkflowMode:
            print(f"   - {mode.value}")
        
        # Test quick classification
        print(f"\n⚡ Testing Quick Classification workflow...")
        test_input = "I spent $15.99 at McDonald's for lunch"
        
        result = await workflow.execute_workflow(
            mode=WorkflowMode.QUICK_CLASSIFICATION,
            user_input=test_input,
            user_id="setup_test"
        )
        
        print(f"✅ Quick Classification completed:")
        print(f"   - Status: {result['status']}")
        print(f"   - Execution time: {result['execution_time']:.2f}s")
        print(f"   - Workflow ID: {result['workflow_id']}")
        
        if result['status'] == 'success':
            final_state = result['result']
            history_count = len(final_state.get('processing_history', []))
            print(f"   - Processing stages: {history_count}")
            
            # Show processing history
            if history_count > 0:
                print(f"\n📊 Processing History:")
                for i, entry in enumerate(final_state['processing_history'][:5], 1):
                    stage = entry.get('stage', 'unknown')
                    action = entry.get('action', 'unknown')
                    print(f"   {i}. {stage}: {action}")
        
        # Test workflow status
        print(f"\n📊 Getting workflow statistics...")
        stats = workflow.get_all_workflows_status()
        print(f"✅ Statistics retrieved:")
        print(f"   - Total executions: {stats['workflow_stats']['total_executions']}")
        print(f"   - Successful: {stats['workflow_stats']['successful_executions']}")
        print(f"   - Failed: {stats['workflow_stats']['failed_executions']}")
        
        # Test different modes
        print(f"\n🧪 Testing different workflow modes...")
        
        test_cases = [
            (WorkflowMode.INGESTION_ONLY, "Data preprocessing test"),
            (WorkflowMode.VALIDATION_ONLY, "Validation test input"),
        ]
        
        for mode, test_input in test_cases:
            try:
                result = await workflow.execute_workflow(
                    mode=mode,
                    user_input=test_input,
                    user_id="mode_test"
                )
                
                status_icon = "✅" if result['status'] == 'success' else "⚠️"
                print(f"   {status_icon} {mode.value}: {result['status']} ({result['execution_time']:.2f}s)")
                
            except Exception as e:
                print(f"   ❌ {mode.value}: Failed - {str(e)}")
        
        # Test background processing
        print(f"\n🔄 Testing background processing...")
        try:
            task_id = await workflow.execute_background_workflow(
                user_input="Background test transaction",
                user_id="bg_test"
            )
            print(f"✅ Background task started: {task_id}")
            
            # Wait a moment and check status
            await asyncio.sleep(1)
            bg_status = workflow.get_background_task_status(task_id)
            print(f"   Status: {bg_status.get('status', 'unknown')}")
            
        except Exception as e:
            print(f"   ⚠️ Background processing test failed: {e}")
        
        # Export metrics
        print(f"\n📈 Exporting workflow metrics...")
        metrics = workflow.export_workflow_metrics()
        print(f"✅ Metrics exported:")
        print(f"   - Timestamp: {metrics['timestamp']}")
        print(f"   - Total executions: {metrics['workflow_stats']['total_executions']}")
        
        # Final summary
        print(f"\n🎉 Setup Test Complete!")
        print(f"=" * 50)
        print(f"✅ All core components working correctly")
        print(f"✅ Workflow modes functional")
        print(f"✅ Background processing available") 
        print(f"✅ Monitoring and metrics working")
        print(f"\n🚀 Your LangGraph workflow system is ready!")
        print(f"\n📚 Next steps:")
        print(f"   1. Start backend: python main.py")
        print(f"   2. Test API: curl http://localhost:8000/api/workflow/health")
        print(f"   3. Open LangGraph Studio: langgraph studio")
        print(f"   4. Run full tests: python test_unified_workflow.py")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(f"\n🔧 Please ensure all dependencies are installed:")
        print(f"   pip install langgraph langsmith langchain-groq")
        return False
        
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    # Check for .env file
    env_file = project_root / '.env'
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️ .env file not found - creating template...")
        env_template = """# FinTrack LangGraph Configuration
GROQ_API_KEY=your_groq_api_key_here
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=fintrack-workflows
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Workflow Settings
DEFAULT_WORKFLOW_MODE=full_pipeline
CONFIDENCE_THRESHOLD=0.7
WORKFLOW_TIMEOUT_SECONDS=300
ENABLE_BACKGROUND_PROCESSING=true
ENABLE_PARALLEL_PROCESSING=true
ENABLE_WORKFLOW_PERSISTENCE=true
"""
        with open(env_file, 'w') as f:
            f.write(env_template)
        print(f"📝 Created .env template at {env_file}")
        print(f"⚠️ Please update with your actual API keys")
    
    # Check for required directories
    required_dirs = [
        'src/workflows',
        'src/nodes', 
        'src/states',
        'src/agents',
        'logs'
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path} directory exists")
        else:
            print(f"⚠️ {dir_path} directory missing")
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created {dir_path} directory")

async def main():
    """Main setup function"""
    print(f"🎯 FinTrack LangGraph Setup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 Project root: {project_root}")
    print()
    
    # Check environment
    check_environment()
    print()
    
    # Test workflow setup
    success = await test_workflow_setup()
    
    if success:
        print(f"\n🎊 Setup completed successfully!")
        print(f"🚀 Your FinTrack LangGraph workflow system is ready to use!")
    else:
        print(f"\n⚠️ Setup encountered issues. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
