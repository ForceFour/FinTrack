"""Simple test to verify project structure and basic functionality"""

import sys
import os

def test_project_structure():
    """Test that the project structure is correct"""
    print("🔍 Checking project structure...")
    
    required_dirs = [
        'src',
        'src/agents',
        'src/api',
        'src/models',
        'src/schemas',
        'src/utils',
        'src/workflows',
        'config',
        'tests',
        'data'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - Missing!")
    
    print()


def test_required_files():
    """Test that required files exist"""
    print("📁 Checking required files...")
    
    required_files = [
        'pyproject.toml',
        'README.md',
        'src/__init__.py',
        'src/agents/ingestion_agent.py',
        'src/agents/ner_merchant_agent.py',
        'src/agents/classifier_agent.py',
        'src/agents/pattern_analyzer_agent.py',
        'src/agents/suggestion_agent.py',
        'src/agents/safety_guard_agent.py',
        'src/api/main.py',
        'src/schemas/transaction_schemas.py',
        'config/settings.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - Missing!")
    
    print()


def test_basic_imports():
    """Test basic Python imports without dependencies"""
    print("🐍 Testing basic Python functionality...")
    
    try:
        # Test standard library imports
        from datetime import datetime
        from typing import Dict, List, Any
        import json
        import re
        print("  ✅ Standard library imports working")
        
        # Test basic data structures
        sample_data = {
            "transaction_id": "txn_001",
            "amount": 45.67,
            "description": "STARBUCKS STORE #1234",
            "date": "2024-01-15"
        }
        
        # Test JSON serialization
        json_str = json.dumps(sample_data)
        parsed_data = json.loads(json_str)
        assert parsed_data["amount"] == 45.67
        print("  ✅ JSON serialization working")
        
        # Test regex functionality
        amount_pattern = r'\$?(\d+\.?\d*)'
        match = re.search(amount_pattern, "$45.67")
        assert match is not None
        print("  ✅ Regex functionality working")
        
        print("  ✅ All basic Python functionality tests passed")
        
    except Exception as e:
        print(f"  ❌ Error in basic Python functionality: {e}")
    
    print()


def show_project_info():
    """Show project information"""
    print("📊 FinTrack Project Information")
    print("=" * 40)
    print("🏦 Financial Transaction Analysis System")
    print("🤖 6-Agent Pipeline Architecture:")
    print("  1. 🔄 Ingestion Agent - Normalizes raw data")
    print("  2. 🏪 NER/Merchant Agent - Extracts merchant info")
    print("  3. 🏷️ Classifier Agent - Predicts categories")
    print("  4. 📊 Pattern Analyzer Agent - Detects patterns")
    print("  5. 💡 Suggestion Agent - Generates recommendations")
    print("  6. 🛡️ Safety Guard Agent - Flags anomalies")
    print()
    print("🛠️ Technology Stack:")
    print("  • FastAPI for REST API")
    print("  • LangChain + LangGraph for agent orchestration")
    print("  • scikit-learn for ML models")
    print("  • Pydantic for data validation")
    print("  • uv for package management")
    print()


def main():
    """Main test function"""
    print("🚀 FinTrack Project Setup Verification")
    print("=" * 50)
    print()
    
    test_project_structure()
    test_required_files()
    test_basic_imports()
    show_project_info()
    
    print("🎯 Next Steps:")
    print("  1. Install dependencies: uv sync")
    print("  2. Start API server: uv run uvicorn src.api.main:app --reload")
    print("  3. Run full demo: uv run python demo.py")
    print("  4. Run tests: uv run pytest")
    print()
    print("✨ Project setup verification completed!")


if __name__ == "__main__":
    main()
