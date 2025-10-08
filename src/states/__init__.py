"""
LangGraph State Definitions for Transaction Processing Pipeline
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from enum import Enum
import operator
from datetime import datetime

class ProcessingStage(Enum):
    """Enumeration of processing stages"""
    INITIAL = "initial"
    NL_PROCESSING = "nl_processing"
    INGESTION = "ingestion"
    NER_EXTRACTION = "ner_extraction"
    CLASSIFICATION = "classification"
    PATTERN_ANALYSIS = "pattern_analysis"
    SUGGESTION = "suggestion"
    SAFETY_GUARD = "safety_guard"
    VALIDATION = "validation"
    COMPLETED = "completed"
    ERROR = "error"

class TransactionProcessingState(TypedDict):
    """
    Main state for transaction processing workflow

    This state flows through all nodes in the LangGraph workflow
    """
    # Input data - Enhanced for LangGraph workflow
    user_input: str  # Natural language input
    user_id: str  # User identifier
    conversation_context: Dict[str, Any]  # Conversation context
    raw_transactions: Optional[List[Dict[str, Any]]]  # Structured transaction data
    raw_input: Optional[str]  # Legacy field
    input_type: Optional[str]  # "structured" or "unstructured"

    # Processing stage tracking
    current_stage: ProcessingStage
    processing_history: Annotated[List[Dict[str, Any]], operator.add]

    # Enhanced processing tracking
    confidence_scores: Annotated[List[Dict[str, Any]], operator.add]  # Stage-wise confidence
    error_log: Annotated[List[Dict[str, Any]], operator.add]  # Error tracking
    processed_transactions: Optional[List[Dict[str, Any]]]  # Final processed transactions
    created_at: datetime  # Creation timestamp

    # Extracted transaction data
    extracted_transaction: Optional[Dict[str, Any]]
    confidence_score: Optional[float]
    extraction_method: Optional[str]  # "llm", "regex", "manual"

    # NLP Processing results
    nl_processing_result: Optional[Dict[str, Any]]
    nl_confidence: Optional[float]

    # Ingestion results
    preprocessed_transactions: Optional[List[Dict[str, Any]]]
    ingestion_metadata: Optional[Dict[str, Any]]
    ingestion_confidence: Optional[float]  # Added for ingestion tracking
    data_quality_scores: Optional[Dict[str, Any]]  # Added for quality tracking

    # NER results
    ner_entities: Optional[Dict[str, Any]]
    merchant_info: Optional[Dict[str, Any]]
    location_info: Optional[Dict[str, Any]]

    # Classification results
    predicted_category: Optional[str]
    category_confidence: float

    # Pattern Analysis results
    spending_patterns: Optional[Dict[str, Any]]
    pattern_insights: Optional[Dict[str, Any]]
    pattern_confidence: Optional[float]

    # Suggestion results
    budget_recommendations: Optional[List[Dict[str, Any]]]
    spending_suggestions: Optional[List[Dict[str, Any]]]
    suggestion_confidence: Optional[float]

    # Safety Guard results
    security_alerts: Optional[List[Dict[str, Any]]]
    risk_assessment: Optional[Dict[str, Any]]
    safety_confidence: Optional[float]

    # Validation results
    validation_errors: Annotated[List[str], operator.add]
    is_valid: bool

    # Final results
    final_transaction: Optional[Dict[str, Any]]

    # Error handling
    errors: Annotated[List[Dict[str, Any]], operator.add]
    retry_count: int

    # Metadata
    workflow_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    total_processing_time: Optional[float]
    processing_metadata: Optional[Dict[str, Any]]

class ConversationState(TypedDict):
    """
    State for conversational transaction processing
    """
    conversation_id: str
    user_input: str
    conversation_history: Annotated[List[Dict[str, str]], operator.add]

    # Current transaction being built
    current_transaction: Dict[str, Any]
    missing_fields: List[str]

    # Conversation flow
    conversation_stage: str  # "initial", "gathering", "confirmation", "completed"
    clarification_needed: bool
    follow_up_questions: List[str]

    # Results
    extracted_data: Optional[Dict[str, Any]]
    confidence: float

    # Final state
    is_complete: bool
    requires_human_review: bool

class BatchProcessingState(TypedDict):
    """
    State for batch file processing
    """
    batch_id: str
    file_path: str
    file_type: str  # "csv", "excel", "json"

    # Processing progress
    total_rows: int
    processed_rows: int
    failed_rows: int

    # Results
    successful_transactions: Annotated[List[Dict[str, Any]], operator.add]
    failed_transactions: Annotated[List[Dict[str, Any]], operator.add]

    # Batch metadata
    batch_confidence: float
    processing_summary: Dict[str, Any]

    # Status
    is_complete: bool
    processing_errors: Annotated[List[str], operator.add]
