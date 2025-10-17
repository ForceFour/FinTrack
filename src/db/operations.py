"""
Database Operations - CRUD operations for transactions using Supabase
This provides the actual database persistence layer
"""

from supabase import Client
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import json

from ..models.transaction import TransactionCreate, TransactionResponse


class TransactionCRUD:
    """Database CRUD operations for transactions using Supabase"""

    @staticmethod
    async def create_transaction(
        client: Client,
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new transaction in the database"""
        try:
            print(f"DEBUG: Creating transaction with data: {transaction_data}")
            # Insert transaction using Supabase client
            response = client.table("transactions").insert(transaction_data).execute()
            print(f"DEBUG: Supabase response: {response}")

            if response.data:
                print(f"DEBUG: Transaction created successfully: {response.data[0]}")
                return response.data[0]
            else:
                print("DEBUG: No data in response")
                raise ValueError("Failed to create transaction")

        except Exception as e:
            print(f"DEBUG: Transaction creation failed: {str(e)}")
            raise ValueError(f"Transaction creation failed: {str(e)}")

    @staticmethod
    async def get_transaction(
        client: Client,
        transaction_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific transaction by ID and user"""
        try:
            response = client.table("transactions").select("*").eq("id", transaction_id).eq("user_id", user_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            raise ValueError(f"Failed to get transaction: {str(e)}")

    @staticmethod
    async def get_transactions(
        client: Client,
        filters: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get transactions with filtering and pagination"""
        try:
            user_id = filters.get('user_id')
            if not user_id:
                raise ValueError("user_id is required")

            # Build query
            query = client.table("transactions").select("*", count="exact").eq("user_id", user_id)

            # Apply filters
            if 'category' in filters and filters['category']:
                query = query.eq("category", filters['category'])

            if 'start_date' in filters and filters['start_date']:
                query = query.gte("date", filters['start_date'].isoformat() if isinstance(filters['start_date'], date) else filters['start_date'])

            if 'end_date' in filters and filters['end_date']:
                query = query.lte("date", filters['end_date'].isoformat() if isinstance(filters['end_date'], date) else filters['end_date'])

            if 'min_amount' in filters and filters['min_amount'] is not None:
                query = query.gte("amount", filters['min_amount'])

            if 'max_amount' in filters and filters['max_amount'] is not None:
                query = query.lte("amount", filters['max_amount'])

            # Apply ordering and pagination
            query = query.order("date", desc=True)

            offset = filters.get('offset', 0)
            limit = filters.get('limit', 100)
            query = query.range(offset, offset + limit - 1)

            # Execute query
            response = query.execute()

            return response.data or [], response.count or 0

        except Exception as e:
            raise ValueError(f"Failed to get transactions: {str(e)}")

    @staticmethod
    async def update_transaction(
        client: Client,
        transaction_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a transaction"""
        try:
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow().isoformat()

            # Execute update
            response = client.table("transactions").update(update_data).eq("id", transaction_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            raise ValueError(f"Failed to update transaction: {str(e)}")

    @staticmethod
    async def delete_transaction(
        client: Client,
        transaction_id: str
    ) -> bool:
        """Delete a transaction"""
        try:
            response = client.table("transactions").delete().eq("id", transaction_id).execute()
            return len(response.data or []) > 0

        except Exception as e:
            raise ValueError(f"Failed to delete transaction: {str(e)}")

    @staticmethod
    async def batch_create_transactions(
        client: Client,
        transactions_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create multiple transactions in batch"""
        try:
            # Insert multiple transactions
            response = client.table("transactions").insert(transactions_data).execute()

            created = len(response.data or [])
            return {
                "created": created,
                "failed": 0,
                "errors": []
            }

        except Exception as e:
            return {
                "created": 0,
                "failed": len(transactions_data),
                "errors": [str(e)]
            }

    @staticmethod
    async def verify_transaction_ownership(
        client: Client,
        transaction_ids: List[str],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Verify that transactions belong to a user"""
        try:
            response = client.table("transactions").select("*").in_("id", transaction_ids).eq("user_id", user_id).execute()
            return response.data or []
        except Exception as e:
            raise ValueError(f"Failed to verify transaction ownership: {str(e)}")

    @staticmethod
    async def get_transaction_summary(
        client: Client,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get transaction summary statistics"""
        try:
            # Build query
            query = client.table("transactions").select("*").eq("user_id", user_id)

            if start_date:
                query = query.gte("date", start_date.isoformat())
            if end_date:
                query = query.lte("date", end_date.isoformat())

            # Execute query
            response = query.execute()
            transactions = response.data or []

            if not transactions:
                return {
                    "total_transactions": 0,
                    "total_amount": 0.0,
                    "average_amount": 0.0,
                    "categories": {},
                    "period": {
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None
                    }
                }

            # Calculate summary
            total_amount = sum(t.get('amount', 0) for t in transactions)
            category_stats = {}

            for transaction in transactions:
                category = transaction.get('category') or "Uncategorized"
                if category not in category_stats:
                    category_stats[category] = {"count": 0, "total": 0.0}
                category_stats[category]["count"] += 1
                category_stats[category]["total"] += transaction.get('amount', 0)

            return {
                "total_transactions": len(transactions),
                "total_amount": total_amount,
                "average_amount": total_amount / len(transactions),
                "categories": category_stats,
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }

        except Exception as e:
            raise ValueError(f"Failed to get transaction summary: {str(e)}")


class UserCRUD:
    """Database CRUD operations for users using Supabase"""

    @staticmethod
    async def create_user(
        client: Client,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new user"""
        try:
            response = client.table("profiles").insert(user_data).execute()

            if response.data:
                return response.data[0]
            else:
                raise ValueError("Failed to create user")

        except Exception as e:
            raise ValueError(f"User creation failed: {str(e)}")

    @staticmethod
    async def get_user_by_id(
        client: Client,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            response = client.table("profiles").select("*").eq("id", user_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            raise ValueError(f"Failed to get user: {str(e)}")

    @staticmethod
    async def get_user_by_username(
        client: Client,
        username: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            response = client.table("profiles").select("*").eq("username", username).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            raise ValueError(f"Failed to get user by username: {str(e)}")

    @staticmethod
    async def get_user_by_email(
        client: Client,
        email: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            response = client.table("profiles").select("*").eq("email", email).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            raise ValueError(f"Failed to get user by email: {str(e)}")
