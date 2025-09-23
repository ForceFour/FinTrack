"""
SQLAlchemy ORM Model for Transactions
Database table definition for transaction storage
"""

from sqlalchemy import Column, String, Float, DateTime, Text, Enum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from enum import Enum as PyEnum

from ...core.database_config import Base


class TransactionType(PyEnum):
    """Transaction types matching your Pydantic model"""
    DEBIT = "debit"
    CREDIT = "credit"


class TransactionStatus(PyEnum):
    """Transaction status matching your Pydantic model"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class TransactionORM(Base):
    """
    SQLAlchemy ORM model for transactions table
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
    
    # Transaction details
    merchant = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    subcategory = Column(String, nullable=True)
    
    # Transaction type and status
    transaction_type = Column(
        Enum(TransactionType), 
        nullable=False, 
        default=TransactionType.DEBIT
    )
    status = Column(
        Enum(TransactionStatus), 
        nullable=False, 
        default=TransactionStatus.COMPLETED
    )
    
    # Additional fields
    notes = Column(Text, nullable=True)
    tags = Column(String, nullable=True)  # JSON string for tags array
    
    # AI/ML fields
    confidence_score = Column(Float, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)
    
    # Location data
    location = Column(String, nullable=True)
    
    # External data
    bank_transaction_id = Column(String, nullable=True, unique=True)
    account_id = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Processing metadata
    processed_by_agent = Column(String, nullable=True)  # Which agent processed this
    processing_version = Column(String, nullable=True)  # Version of processing pipeline
    
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
