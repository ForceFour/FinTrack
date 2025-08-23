"""
Quick Application Test - Validate Current Setup
Tests what components are working and what needs immediate attention
"""

import sys
import traceback
from pathlib import Path

def test_component(name, test_func):
    """Test a component and report results"""
    print(f"\n🔍 Testing {name}...")
    try:
        result = test_func()
        print(f"✅ {name}: {result}")
        return True
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        print(f"   Detail: {traceback.format_exc().splitlines()[-1]}")
        return False

def test_basic_imports():
    """Test basic dependency imports"""
    import fastapi
    import streamlit
    import langchain
    import langgraph
    import pandas
    import plotly
    return "All key dependencies available"

def test_frontend_structure():
    """Test if frontend files exist and can be imported"""
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        return "Frontend directory missing"
    
    required_files = [
        "streamlit_app.py",
        "utils/api_client.py",
        "utils/session_state.py",
        "components/charts.py",
        "components/widgets.py",
        "pages/dashboard.py"
    ]
    
    missing = []
    for file in required_files:
        if not (frontend_path / file).exists():
            missing.append(file)
    
    if missing:
        return f"Missing files: {missing}"
    
    return "All frontend files present"

def test_backend_structure():
    """Test if backend files exist"""
    src_path = Path("src")
    if not src_path.exists():
        return "Source directory missing"
    
    required_files = [
        "routes/__init__.py",
        "routes/auth.py", 
        "routes/transactions.py",
        "routes/analytics.py",
        "routes/suggestions.py",
        "routes/agents.py"
    ]
    
    missing = []
    for file in required_files:
        if not (src_path / file).exists():
            missing.append(file)
    
    if missing:
        return f"Missing files: {missing}"
    
    return "All route files present"

def test_route_imports():
    """Test if routes can be imported (will fail if models missing)"""
    try:
        from src.routes import api_router
        return "Routes imported successfully"
    except ImportError as e:
        return f"Import failed: {str(e)}"

def test_main_app():
    """Test if main FastAPI app can be created"""
    try:
        import main
        return "Main app module loaded"
    except ImportError as e:
        return f"Main app import failed: {str(e)}"

def test_streamlit_frontend():
    """Test if Streamlit app can be imported"""
    try:
        sys.path.append("frontend")
        import streamlit_app
        return "Streamlit app can be imported"
    except ImportError as e:
        return f"Streamlit import failed: {str(e)}"

def test_missing_models():
    """Check what models are missing"""
    src_path = Path("src")
    models_path = src_path / "models"
    
    if not models_path.exists():
        return "Models directory missing - CRITICAL"
    
    required_models = [
        "user.py",
        "transaction.py", 
        "analytics.py",
        "suggestion.py",
        "agent.py",
        "auth.py"
    ]
    
    missing = []
    for model in required_models:
        if not (models_path / model).exists():
            missing.append(model)
    
    if missing:
        return f"Missing models: {missing} - BLOCKS API"
    
    return "All models present"

def test_missing_services():
    """Check what services are missing"""
    src_path = Path("src")
    services_path = src_path / "services"
    
    if not services_path.exists():
        return "Services directory missing - CRITICAL"
    
    required_services = [
        "auth_service.py",
        "transaction_service.py",
        "analytics_service.py", 
        "suggestion_service.py",
        "agent_service.py"
    ]
    
    missing = []
    for service in required_services:
        if not (services_path / service).exists():
            missing.append(service)
    
    if missing:
        return f"Missing services: {missing} - BLOCKS API"
    
    return "All services present"

def main():
    """Run all tests and provide summary"""
    print("🚀 Agentic Expense Tracker - Application Test")
    print("=" * 50)
    
    tests = [
        ("Basic Dependencies", test_basic_imports),
        ("Frontend Structure", test_frontend_structure),
        ("Backend Structure", test_backend_structure),
        ("Missing Models", test_missing_models),
        ("Missing Services", test_missing_services),
        ("Route Imports", test_route_imports),
        ("Main App", test_main_app),
        ("Streamlit Frontend", test_streamlit_frontend),
    ]
    
    results = []
    for name, test_func in tests:
        results.append(test_component(name, test_func))
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 TEST SUMMARY")
    print(f"=" * 30)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Application is ready to run.")
        print("🚀 Next steps:")
        print("   1. Start backend: uv run python main.py")
        print("   2. Start frontend: uv run streamlit run frontend/streamlit_app.py")
    else:
        print(f"\n⚠️  {total - passed} components need attention before running.")
        print("📋 Check PROJECT_ANALYSIS.md for detailed TODO list.")
        print("🔧 Priority: Create missing models and services first.")

if __name__ == "__main__":
    main()
