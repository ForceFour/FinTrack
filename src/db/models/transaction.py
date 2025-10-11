"""
SQLAlchemy ORM Model for Transactions
Database table definition for transaction storage
"""

from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.sql import func
import uuid

from ...core.database_config import Base


class TransactionORM(Base):
    """
    SQLAlchemy ORM model for transactions table (Supabase schema)
    This creates the actual database table structure
    """
    __tablename__ = "transactions"

    # Primary key - UUID
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )

    # User association
    user_id = Column(String, nullable=False, index=True)

    # Core transaction fields
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False, index=True)

    # Transaction type and status
    transaction_type = Column(String, nullable=False)  # 'debit' or 'credit'
    status = Column(String, nullable=False, default="completed")

    # Categorization
    category = Column(String, nullable=True)
    subcategory = Column(String, nullable=True)
    merchant = Column(String, nullable=True)

    # Additional fields
    payment_method = Column(String, nullable=True)
    account_type = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return (
            f"<TransactionORM(id='{self.id}', "
            f"amount={self.amount}, "
            f"merchant='{self.merchant}', "
            f"category='{self.category}')>"
        )

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "merchant": self.merchant,
            "category": self.category,
            "subcategory": self.subcategory,
            "transaction_type": self.transaction_type,
            "status": self.status,
            "payment_method": self.payment_method,
            "account_type": self.account_type,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "merchant": self.merchant,
            "category": self.category,
            "subcategory": self.subcategory,
            "transaction_type": self.transaction_type.value if self.transaction_type else None,
            "status": self.status.value if self.status else None,
            "notes": self.notes,
            "tags": self.tags,
            "confidence_score": self.confidence_score,
            "is_recurring": self.is_recurring,
            "recurring_pattern": self.recurring_pattern,
            "location": self.location,
            "bank_transaction_id": self.bank_transaction_id,
            "account_id": self.account_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_by_agent": self.processed_by_agent,
            "processing_version": self.processing_version
        }
