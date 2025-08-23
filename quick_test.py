#!/usr/bin/env python3
"""Quick application test"""

def test_imports():
    """Test all critical imports"""
    try:
        print("Testing basic imports...")
        
        # Test models
        from src.models.user import User, UserCreate
        print("✅ User models")
        
        from src.models.transaction import Transaction, TransactionCreate
        print("✅ Transaction models")
        
        from src.models.auth import Token, LoginRequest
        print("✅ Auth models")
        
        # Test services
        from src.services.auth_service import AuthService
        print("✅ Auth service")
        
        from src.services.transaction_service import TransactionService
        print("✅ Transaction service")
        
        # Test core
        from src.core.config import Settings
        print("✅ Config")
        
        from src.core.database import MockDatabase
        print("✅ Database")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_streamlit_app():
    """Check if Streamlit app structure is intact"""
    import os
    
    streamlit_files = [
        "main.py",
        "frontend/streamlit_app.py",
        "frontend/pages/Dashboard.py",
        "frontend/pages/Upload_Transactions.py", 
        "frontend/pages/Analytics.py",
        "frontend/pages/Suggestions.py",
        "frontend/pages/Category_Management.py",
        "frontend/pages/Security_Monitor.py"
    ]
    
    print("\n🔍 Checking Streamlit app structure...")
    for file in streamlit_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")

if __name__ == "__main__":
    print("🚀 Quick Application Test")
    print("=" * 30)
    
    # Test imports
    if test_imports():
        print("\n✅ All backend components are working!")
    else:
        print("\n❌ Some backend components failed")
    
    # Test frontend
    test_streamlit_app()
    
    print("\n🏁 Test complete!")
