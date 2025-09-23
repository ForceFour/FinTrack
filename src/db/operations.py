"""
Database Operations - CRUD operations for transactions
This provides the actual database persistence layer
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, delete, update
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import json

from .models.transaction import TransactionORM, TransactionType, TransactionStatus
from .models.user import UserORM
from ..models.transaction import TransactionCreate, TransactionResponse


class TransactionCRUD:
    """Database CRUD operations for transactions"""
    
    @staticmethod
    async def create_transaction(
        db: AsyncSession, 
        transaction_data: Dict[str, Any]
    ) -> TransactionORM:
        """Create a new transaction in the database"""
        try:
            # Handle enum conversions
            if 'transaction_type' in transaction_data:
                if isinstance(transaction_data['transaction_type'], str):
                    transaction_data['transaction_type'] = TransactionType(transaction_data['transaction_type'])
            
            if 'status' in transaction_data:
                if isinstance(transaction_data['status'], str):
                    transaction_data['status'] = TransactionStatus(transaction_data['status'])
            
            # Handle tags as JSON string
            if 'tags' in transaction_data and isinstance(transaction_data['tags'], list):
                transaction_data['tags'] = json.dumps(transaction_data['tags'])
            
            # Create ORM instance
            db_transaction = TransactionORM(**transaction_data)
            
            # Add to session and commit
            db.add(db_transaction)
            await db.commit()
            await db.refresh(db_transaction)
            
            return db_transaction
            
        except IntegrityError as e:
            await db.rollback()
            raise ValueError(f"Transaction creation failed: {str(e)}")
        except Exception as e:
            await db.rollback()
            raise e
    
    @staticmethod
    async def get_transaction(
        db: AsyncSession, 
        transaction_id: str, 
        user_id: str
    ) -> Optional[TransactionORM]:
        """Get a specific transaction by ID and user"""
        result = await db.execute(
            select(TransactionORM).where(
                and_(
                    TransactionORM.id == transaction_id,
                    TransactionORM.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_transactions(
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> Tuple[List[TransactionORM], int]:
        """Get transactions with filtering and pagination"""
        
        # Build base query
        query = select(TransactionORM).where(
            TransactionORM.user_id == filters['user_id']
        )
        
        # Apply filters
        if 'category' in filters and filters['category']:
            query = query.where(TransactionORM.category == filters['category'])
        
        if 'start_date' in filters and filters['start_date']:
            query = query.where(TransactionORM.date >= filters['start_date'])
        
        if 'end_date' in filters and filters['end_date']:
            query = query.where(TransactionORM.date <= filters['end_date'])
        
        if 'min_amount' in filters and filters['min_amount'] is not None:
            query = query.where(TransactionORM.amount >= filters['min_amount'])
        
        if 'max_amount' in filters and filters['max_amount'] is not None:
            query = query.where(TransactionORM.amount <= filters['max_amount'])
        
        if 'search' in filters and filters['search']:
            search_term = f"%{filters['search']}%"
            query = query.where(
                or_(
                    TransactionORM.description.ilike(search_term),
                    TransactionORM.merchant.ilike(search_term),
                    TransactionORM.category.ilike(search_term)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(desc(TransactionORM.date))
        query = query.offset(filters.get('offset', 0))
        query = query.limit(filters.get('limit', 100))
        
        # Execute query
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return list(transactions), total
    
    @staticmethod
    async def update_transaction(
        db: AsyncSession,
        transaction_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[TransactionORM]:
        """Update a transaction"""
        try:
            # Handle enum conversions
            if 'transaction_type' in update_data:
                if isinstance(update_data['transaction_type'], str):
                    update_data['transaction_type'] = TransactionType(update_data['transaction_type'])
            
            if 'status' in update_data:
                if isinstance(update_data['status'], str):
                    update_data['status'] = TransactionStatus(update_data['status'])
            
            # Handle tags as JSON string
            if 'tags' in update_data and isinstance(update_data['tags'], list):
                update_data['tags'] = json.dumps(update_data['tags'])
            
            # Add updated timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Execute update
            result = await db.execute(
                update(TransactionORM)
                .where(TransactionORM.id == transaction_id)
                .values(**update_data)
                .returning(TransactionORM)
            )
            
            updated_transaction = result.scalar_one_or_none()
            await db.commit()
            
            return updated_transaction
            
        except Exception as e:
            await db.rollback()
            raise e
    
    @staticmethod
    async def delete_transaction(
        db: AsyncSession,
        transaction_id: str
    ) -> bool:
        """Delete a transaction"""
        try:
            result = await db.execute(
                delete(TransactionORM).where(TransactionORM.id == transaction_id)
            )
            await db.commit()
            return result.rowcount > 0
            
        except Exception as e:
            await db.rollback()
            raise e
    
    @staticmethod
    async def batch_create_transactions(
        db: AsyncSession,
        transactions_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create multiple transactions in batch"""
        created = 0
        failed = 0
        errors = []
        
        for i, transaction_data in enumerate(transactions_data):
            try:
                await TransactionCRUD.create_transaction(db, transaction_data)
                created += 1
            except Exception as e:
                failed += 1
                errors.append(f"Transaction {i}: {str(e)}")
        
        return {
            "created": created,
            "failed": failed,
            "errors": errors
        }
    
    @staticmethod
    async def verify_transaction_ownership(
        db: AsyncSession,
        transaction_ids: List[str],
        user_id: str
    ) -> List[TransactionORM]:
        """Verify that transactions belong to a user"""
        result = await db.execute(
            select(TransactionORM).where(
                and_(
                    TransactionORM.id.in_(transaction_ids),
                    TransactionORM.user_id == user_id
                )
            )
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_transaction_summary(
        db: AsyncSession,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get transaction summary statistics"""
        # Build base query
        query = select(TransactionORM).where(TransactionORM.user_id == user_id)
        
        if start_date:
            query = query.where(TransactionORM.date >= start_date)
        if end_date:
            query = query.where(TransactionORM.date <= end_date)
        
        # Execute query
        result = await db.execute(query)
        transactions = result.scalars().all()
        
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
        total_amount = sum(t.amount for t in transactions)
        category_stats = {}
        
        for transaction in transactions:
            category = transaction.category or "Uncategorized"
            if category not in category_stats:
                category_stats[category] = {"count": 0, "total": 0.0}
            category_stats[category]["count"] += 1
            category_stats[category]["total"] += transaction.amount
        
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


class UserCRUD:
    """Database CRUD operations for users"""
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_data: Dict[str, Any]
    ) -> UserORM:
        """Create a new user"""
        try:
            # Handle preferences as JSON string
            if 'preferences' in user_data and isinstance(user_data['preferences'], dict):
                user_data['preferences'] = json.dumps(user_data['preferences'])
            
            db_user = UserORM(**user_data)
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            
            return db_user
            
        except IntegrityError as e:
            await db.rollback()
            raise ValueError(f"User creation failed: {str(e)}")
    
    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: str
    ) -> Optional[UserORM]:
        """Get user by ID"""
        result = await db.execute(
            select(UserORM).where(UserORM.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(
        db: AsyncSession,
        username: str
    ) -> Optional[UserORM]:
        """Get user by username"""
        result = await db.execute(
            select(UserORM).where(UserORM.username == username)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(
        db: AsyncSession,
        email: str
    ) -> Optional[UserORM]:
        """Get user by email"""
        result = await db.execute(
            select(UserORM).where(UserORM.email == email)
        )
        return result.scalar_one_or_none()
