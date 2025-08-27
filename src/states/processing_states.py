"""
Specific state schemas for different processing stages
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from ..schemas.transaction_schemas import PreprocessedTransaction

class NLProcessingState(BaseModel):
    """State for Natural Language Processing stage"""
    raw_input: str
    processing_method: str  # "llm" or "regex"
    confidence: float = 0.0
    extracted_fields: Dict[str, Any] = {}
    processing_time_ms: float = 0.0
    groq_model_used: Optional[str] = None
    error_message: Optional[str] = None

class IngestionState(BaseModel):
    """State for Ingestion Agent processing"""
    input_data: Dict[str, Any]
    preprocessed_transactions: List[PreprocessedTransaction] = []
    processing_metadata: Dict[str, Any] = {}
    preprocessing_pipeline_steps: List[str] = []
    data_quality_score: float = 0.0
    outliers_detected: int = 0

class NERState(BaseModel):
    """State for Named Entity Recognition"""
    transaction_description: str
    extracted_entities: Dict[str, List[str]] = {}
    merchant_candidates: List[Dict[str, Any]] = []
    location_entities: List[str] = []
    confidence_scores: Dict[str, float] = {}
    ner_model_used: str = "spacy"

class ClassificationState(BaseModel):
    """State for Transaction Classification"""
    transaction_features: Dict[str, Any]
    predicted_category: Optional[str] = None
    category_probabilities: Dict[str, float] = {}
    classification_confidence: float = 0.0
    model_version: str = "v1.0"
    feature_importance: Dict[str, float] = {}

class ValidationState(BaseModel):
    """State for Transaction Validation"""
    transaction_data: Dict[str, Any]
    validation_rules_applied: List[str] = []
    validation_results: Dict[str, bool] = {}
    error_messages: List[str] = []
    warnings: List[str] = []
    is_valid: bool = True
    confidence_threshold_met: bool = True

class WorkflowState(BaseModel):
    """Overall workflow execution state"""
    workflow_id: str = Field(default_factory=lambda: f"workflow_{datetime.now().timestamp()}")
    started_at: datetime = Field(default_factory=datetime.now)
    current_node: str = ""
    completed_nodes: List[str] = []
    failed_nodes: List[str] = []
    retry_attempts: Dict[str, int] = {}
    total_processing_time: float = 0.0
    
    # Stage-specific states
    nl_state: Optional[NLProcessingState] = None
    ingestion_state: Optional[IngestionState] = None
    ner_state: Optional[NERState] = None
    classification_state: Optional[ClassificationState] = None
    validation_state: Optional[ValidationState] = None
    
    # Final results
    final_transaction: Optional[Dict[str, Any]] = None
    overall_confidence: float = 0.0
    processing_successful: bool = False
