#!/usr/bin/env python3
"""
Setup script to create initial user for testing
"""

import asyncio
from src.core.database_config import DatabaseManager
from src.services.auth_service import AuthService
from src.models.user import UserCreate

async def setup_test_user():
    """Create a test user for authentication testing"""
    print("🔐 Setting up test user...")

    try:
        # Initialize database
        db_manager = DatabaseManager()
        await db_manager.initialize()
        print("✅ Database initialized")

        # Create test user
        async with db_manager.get_session() as session:
            auth_service = AuthService(session)

            # Check if test user already exists
            existing_user = await auth_service.get_user_by_username("testuser")
            if existing_user:
                print("ℹ️ Test user already exists")
                return existing_user

            # Create new test user
            user_data = UserCreate(
                username="testuser",
                email="test@example.com",
                password="testpass123",
                full_name="Test User"
            )

            new_user = await auth_service.create_user(user_data)
            print(f"✅ Created test user: {new_user.username} ({new_user.email})")

            # Generate test token
            access_token = auth_service.create_access_token(
                data={"sub": str(new_user.id)}
            )

            print(f"\n🔑 Test authentication token:")
            print(f"Bearer {access_token}")
            print(f"\n📝 Login credentials:")
            print(f"Username: testuser")
            print(f"Password: testpass123")

            return new_user

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'db_manager' in locals():
            await db_manager.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(setup_test_user())
