import asyncio
from src.services.transaction_service import TransactionService
from src.core.database_config import get_db_client, init_database

async def check_db_transactions():
    # Initialize database first
    await init_database()

    # Initialize service with Supabase client
    client = await get_db_client()
    service = TransactionService(client)

    # Get a user ID
    profiles = client.table('profiles').select('id').limit(1).execute()
    if profiles.data:
        user_id = profiles.data[0]['id']
        print(f"Using user_id: {user_id}")

        transactions = client.table('transactions').select('id,date,amount,description,merchant').eq('user_id', user_id).order('created_at', desc=True).limit(50).execute()
        print(f'Found {len(transactions.data)} transactions in database:')
        for tx in transactions.data:
            desc = tx.get('description', '')[:50]
            merchant = tx.get('merchant', '')
            print(f'ID: {tx["id"][:8]}... Date: {tx["date"]}, Amount: {tx["amount"]}, Description: {desc}..., Merchant: {merchant}')
    else:
        print('No profiles found')

if __name__ == "__main__":
    asyncio.run(check_db_transactions())
