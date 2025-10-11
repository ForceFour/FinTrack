import asyncio
from src.core.database_config import init_database, get_db_client

async def check_profiles():
    # Initialize database first
    await init_database()

    client = await get_db_client()
    try:
        result = client.table('profiles').select('*').execute()
        print('Existing profiles:')
        for profile in result.data:
            print(f'  ID: {profile.get("id")}, Email: {profile.get("email")}')
        if not result.data:
            print('  No profiles found')
    except Exception as e:
        print(f'Error checking profiles: {e}')

if __name__ == "__main__":
    asyncio.run(check_profiles())
