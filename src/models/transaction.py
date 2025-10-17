"""
Transaction Models - Data models for financial transactions
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from datetime import date as Date
from decimal import Decimal
from enum import Enum

class TransactionType(str, Enum):
    """Transaction types"""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class TransactionStatus(str, Enum):
    """Transaction processing status"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    DUPLICATE = "duplicate"

class TransactionBase(BaseModel):
    """Base transaction model"""
    amount: Decimal = Field(..., description="Transaction amount")
    description: str = Field(..., min_length=1, max_length=500)
    date: Date = Field(..., description="Transaction date")
    category: Optional[str] = Field(None, max_length=100)
    merchant: Optional[str] = Field(None, max_length=200)
    account: Optional[str] = Field(None, max_length=100)
    transaction_type: TransactionType = TransactionType.EXPENSE
    offer_discount: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v == 0:
            raise ValueError('Amount cannot be zero')
        return v

class TransactionCreate(TransactionBase):
    """Transaction creation model"""
    pass

class TransactionUpdate(BaseModel):
    """Transaction update model - all fields optional"""
    amount: Optional[Decimal] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    date: Optional[Date] = None
    category: Optional[str] = Field(None, max_length=100)
    merchant: Optional[str] = Field(None, max_length=200)
    account: Optional[str] = Field(None, max_length=100)
    transaction_type: Optional[TransactionType] = None
    offer_discount: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=1000)

class TransactionResponse(TransactionBase):
    """Transaction response model"""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: TransactionStatus = TransactionStatus.PROCESSED
    ai_categorized: bool = False
    categorization_confidence: Optional[float] = None
    fraud_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class Transaction(TransactionResponse):
    """Complete transaction model with internal fields"""
    raw_data: Optional[Dict[str, Any]] = {}
    processing_metadata: Optional[Dict[str, Any]] = {}

    model_config = ConfigDict(from_attributes=True)

class TransactionBatch(BaseModel):
    """Batch transaction processing model"""
    transactions: List[TransactionCreate]
    source_file: Optional[str] = None
    batch_id: Optional[str] = None

class TransactionSummary(BaseModel):
    """Transaction summary statistics"""
    total_count: int
    total_amount: Decimal
    average_amount: Decimal
    date_range: Dict[str, Date]
    categories: Dict[str, int]
    transaction_types: Dict[str, int]

class TransactionFilter(BaseModel):
    """Transaction filtering options"""
    start_date: Optional[Date] = None
    end_date: Optional[Date] = None
    category: Optional[str] = None
    merchant: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    transaction_type: Optional[TransactionType] = None
    search: Optional[str] = None
    tags: Optional[List[str]] = None

class TransactionExport(BaseModel):
    """Transaction export configuration"""
    format: str = Field(..., pattern="^(csv|excel|json)$")
    filters: Optional[TransactionFilter] = None
    include_metadata: bool = False
