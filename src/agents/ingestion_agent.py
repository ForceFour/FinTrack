"""
Enhanced Ingestion Agent - Agent 1
Role: Process both structured and unstructured transaction data into normalized format
Handles: File uploads (CSV/Excel) and Natural Language conversational input
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, date
from pydantic import BaseModel, Field
import logging
import re

from ..schemas.transaction_schemas import RawTransaction, PreprocessedTransaction, PaymentMethod, TransactionCategory
from ..utils.data_preprocessing import DataPreprocessor
from .components.file_parser import FileParser
from .components.nl_processor import NLProcessor
from .components.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class IngestionAgentInput(BaseModel):
    """Input schema for Enhanced Ingestion Agent"""
    model_config = {"arbitrary_types_allowed": True}
    
    input_type: str = Field(description="Type of input: 'structured' (files) or 'unstructured' (conversation)")
    raw_transactions: Optional[List[Dict[str, Any]]] = Field(None, description="Raw transaction data from CSV/bank")
    natural_language_input: Optional[str] = Field(None, description="Natural language transaction description")
    conversation_context: Optional[Dict[str, Any]] = Field(None, description="Conversation state context")
    dataframe: Optional[pd.DataFrame] = Field(None, description="DataFrame for structured data")


class IngestionAgentOutput(BaseModel):
    """Output schema for Enhanced Ingestion Agent"""
    preprocessed_transactions: List[PreprocessedTransaction] = Field(description="Normalized transaction data")
    metadata: Dict[str, Any] = Field(description="Processing metadata")
    conversation_response: Optional[str] = Field(None, description="Response for conversational input")
    conversation_state: Optional[Dict[str, Any]] = Field(None, description="Updated conversation state")
    requires_user_input: bool = Field(False, description="Whether more user input is needed")


class EnhancedIngestionAgent:
    """
    Enhanced Agent 1: Ingestion Agent with NLP capabilities
    
    Responsibilities:
    - Handle structured data from CSV/Excel files
    - Process unstructured natural language transaction descriptions
    - Manage conversational transaction entry with missing field prompts
    - Apply comprehensive preprocessing pipeline:
      * Date normalization (year, month, day, day_of_week)
      * Amount processing with outlier detection
      * Discount extraction and calculation
      * Payment method and category encoding
      * Description cleaning and normalization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.preprocessor = DataPreprocessor()
        self.file_parser = FileParser()
        self.nl_processor = NLProcessor(groq_api_key=self.config.get('groq_api_key'))
        self.conversation_manager = ConversationManager()
        
        # Categories for one-hot encoding
        self.categories = [cat.value for cat in TransactionCategory]
        self.payment_methods = [pm.value for pm in PaymentMethod]
    
    def process(self, input_data: IngestionAgentInput) -> IngestionAgentOutput:
        """Main processing method for the Enhanced Ingestion Agent"""
        try:
            if input_data.input_type == "structured":
                return self._process_structured_data(input_data)
            elif input_data.input_type == "unstructured":
                return self._process_unstructured_conversation(input_data)
            else:
                raise ValueError(f"Unsupported input_type: {input_data.input_type}. Use 'structured' or 'unstructured'")
        
        except Exception as e:
            logger.error(f"Error in ingestion processing: {e}")
            return IngestionAgentOutput(
                preprocessed_transactions=[],
                metadata={"error": str(e), "status": "failed"},
                conversation_response="Sorry, I encountered an error processing your request.",
                requires_user_input=False
            )
    
    def _process_structured_data(self, input_data: IngestionAgentInput) -> IngestionAgentOutput:
        """Process structured data from CSV/Excel/PDF files"""
        logger.info("Processing structured transaction data")
        
        if input_data.dataframe is not None:
            # Use provided DataFrame directly
            df = input_data.dataframe.copy()
        elif input_data.raw_transactions:
            # Convert raw transaction list to DataFrame
            df = pd.DataFrame(input_data.raw_transactions)
        else:
            raise ValueError("No structured data provided")
        
        # Apply comprehensive preprocessing pipeline
        try:
            processed_df = self.preprocessor.process_dataframe(df)
            
            # Convert processed DataFrame back to transaction objects
            preprocessed_transactions = self._dataframe_to_transactions(processed_df)
            
            schema_info = self.preprocessor.get_schema_info(processed_df)
            
            return IngestionAgentOutput(
                preprocessed_transactions=preprocessed_transactions,
                metadata={
                    "input_type": "structured",
                    "total_input": len(df),
                    "processed_transactions": len(preprocessed_transactions),
                    "status": "completed",
                    "schema_info": schema_info,
                    "final_columns": processed_df.columns.tolist()
                }
            )
            
        except Exception as e:
            logger.error(f"Structured data processing failed: {e}")
            raise
    
    def _process_unstructured_conversation(self, input_data: IngestionAgentInput) -> IngestionAgentOutput:
        """Process unstructured conversational natural language input"""
        logger.info("Processing unstructured conversational input")
        
        if not input_data.natural_language_input:
            raise ValueError("No natural language input provided")
        
        # Manage conversation state
        if input_data.conversation_context:
            # Continue existing conversation
            self.conversation_manager.state = input_data.conversation_context.get('state', 'initial')
            self.conversation_manager.current_transaction = input_data.conversation_context.get('current_transaction', {})
            self.conversation_manager.missing_fields = input_data.conversation_context.get('missing_fields', [])
        
        # Process the input through conversation manager
        response, transaction_data = self.conversation_manager.process_input(input_data.natural_language_input)
        
        # If conversation is completed, process the transaction
        if self.conversation_manager.state.value == "completed" and transaction_data:
            try:
                # Convert conversation data to DataFrame format for preprocessing
                df_data = {
                    'date': [transaction_data.get('date', '')],
                    'amount': [transaction_data.get('amount', '')],
                    'description': [transaction_data.get('description', '')],
                    'merchant': [transaction_data.get('merchant', '')],
                    'category': [transaction_data.get('category', '')],
                    'payment_method': [transaction_data.get('payment_method', '')],
                    'offer_discount': [transaction_data.get('offer_discount', '')]
                }
                df = pd.DataFrame(df_data)
                
                # Apply comprehensive preprocessing pipeline
                processed_df = self.preprocessor.process_dataframe(df)
                preprocessed_transactions = self._dataframe_to_transactions(processed_df)
                
                return IngestionAgentOutput(
                    preprocessed_transactions=preprocessed_transactions,
                    metadata={
                        "input_type": "unstructured",
                        "conversation_completed": True,
                        "confidence": transaction_data.get('confidence', 1.0),
                        "status": "completed"
                    },
                    conversation_response=response,
                    conversation_state=self.conversation_manager.get_conversation_state(),
                    requires_user_input=False
                )
            except Exception as e:
                logger.error(f"Failed to process conversation transaction: {e}")
                return IngestionAgentOutput(
                    preprocessed_transactions=[],
                    metadata={"error": str(e), "status": "failed"},
                    conversation_response="I couldn't process that transaction. Let's start over.",
                    conversation_state=self.conversation_manager.get_conversation_state(),
                    requires_user_input=True
                )
        else:
            # Conversation ongoing
            return IngestionAgentOutput(
                preprocessed_transactions=[],
                metadata={"status": "ongoing"},
                conversation_response=response,
                conversation_state=self.conversation_manager.get_conversation_state(),
                requires_user_input=True
            )
    
    def _dataframe_to_transactions(self, df: pd.DataFrame) -> List[PreprocessedTransaction]:
        """Convert processed DataFrame to PreprocessedTransaction objects"""
        transactions = []
        
        for idx, row in df.iterrows():
            # Extract basic fields with defaults
            transaction_id = f"txn_{datetime.now().timestamp()}_{idx}"
            
            # Handle date - reconstruct from components if needed
            if 'year' in row and 'month' in row and 'day' in row:
                try:
                    transaction_date = datetime(
                        year=int(row.get('year', datetime.now().year)),
                        month=int(row.get('month', datetime.now().month)),
                        day=int(row.get('day', datetime.now().day))
                    )
                except:
                    transaction_date = datetime.now()
            else:
                transaction_date = datetime.now()
            
            # Create transaction object
            transaction = PreprocessedTransaction(
                id=transaction_id,
                date=transaction_date,
                year=int(row.get('year', transaction_date.year)),
                month=int(row.get('month', transaction_date.month)),
                day=int(row.get('day', transaction_date.day)),
                day_of_week=int(row.get('day_of_week', transaction_date.weekday())),
                amount=float(row.get('amount', 0.0)),
                payment_method=self._determine_payment_method(row),
                description_cleaned=str(row.get('description_clean', '')),
                has_discount=bool(row.get('offer_applied', 0)),
                discount_percentage=float(row.get('discount_percent', 0.0)) if row.get('discount_percent') else None,
                metadata={
                    'is_outlier': bool(row.get('is_outlier', 0)),
                    'amount_log': float(row.get('amount_log', 0.0)),
                    'discount_value': float(row.get('discount_value', 0.0)),
                    'effective_amount': float(row.get('effective_amount', row.get('amount', 0.0))),
                    'merchant_encoded': float(row.get('merchant_encoded', 0.0)),
                    'processed_features': {k: v for k, v in row.items() if k.startswith(('pay_', 'cat_'))},
                    'preprocessing_pipeline': 'comprehensive'
                }
            )
            
            transactions.append(transaction)
        
        return transactions
    
    def _determine_payment_method(self, row: pd.Series) -> PaymentMethod:
        """Determine payment method from one-hot encoded columns"""
        # Look for pay_ columns
        pay_columns = [col for col in row.index if col.startswith('pay_') and row[col] == 1]
        
        if pay_columns:
            # Extract the payment method name
            payment_name = pay_columns[0].replace('pay_', '').lower().replace(' ', '_')
            
            # Map to enum
            payment_mapping = {
                'credit_card': PaymentMethod.CREDIT_CARD,
                'debit_card': PaymentMethod.DEBIT_CARD,
                'cash': PaymentMethod.CASH,
                'bank_transfer': PaymentMethod.BANK_TRANSFER,
                'mobile_wallet': PaymentMethod.DIGITAL_WALLET,
                'digital_wallet': PaymentMethod.DIGITAL_WALLET,
                'check': PaymentMethod.CHECK
            }
            
            for key, value in payment_mapping.items():
                if key in payment_name:
                    return value
        
        return PaymentMethod.OTHER
# Backward compatibility alias
IngestionAgent = EnhancedIngestionAgent
