#!/usr/bin/env python3
"""
Check recent transactions in the database
"""

import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_async_client, AsyncClient

from supabase import create_async_client, AsyncClient

async def check_recent_transactions():
    # Initialize Supabase async client with service role key for admin operations
    supabase_admin: AsyncClient = await create_async_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )

    # Also create client with anon key for regular operations
    supabase: AsyncClient = await create_async_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_ANON_KEY')
    )

    try:
        # Check all profiles using admin client
        print("Checking all profiles in the database...")
        profiles = await supabase_admin.table('profiles').select('*').execute()
        print(f"Found {len(profiles.data)} profiles:")
        for profile in profiles.data:
            print(f"  ID: {profile['id']}, Email: {profile.get('email', 'N/A')}")

        # If no profiles, try to create the dummy user using admin client
        if not profiles.data:
            print("No profiles found. Creating dummy user...")
            dummy_user = {
                "id": "e6afed5f-6e3b-4349-8526-0fc2d9658915",
                "email": "duwaragie22@gmail.com",
                "username": "testuser",
                "created_at": "2024-01-01T00:00:00Z"
            }
            result = await supabase_admin.table('profiles').insert(dummy_user).execute()
            print(f"Created dummy user: {result.data}")

        # Check transactions for the specific user
        user_id = "e6afed5f-6e3b-4349-8526-0fc2d9658915"
        transactions = await supabase.table('transactions').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(10).execute()
        print(f'Found {len(transactions.data)} transactions for user {user_id}:')
        for tx in transactions.data:
            print(f'ID: {tx["id"][:8]}... Type: {tx.get("transaction_type")}, Amount: {tx["amount"]}, Merchant: {tx.get("merchant")}, Category: {tx.get("category")}, Description: {tx.get("description", "")[:50]}...')

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_recent_transactions())
