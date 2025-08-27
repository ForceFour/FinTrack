"""
Specialized nodes for different processing capabilities
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..states import TransactionProcessingState, ProcessingStage

logger = logging.getLogger(__name__)

class ConditionalNodes:
    """
    Conditional nodes for workflow routing and decision making
    """
    
    @staticmethod
    def should_use_llm_node(state: TransactionProcessingState) -> str:
        """
        Determine whether to use LLM or regex processing
        """
        # Check if we have confidence threshold and API availability
        nl_confidence = state.get('nl_confidence', 0.0)
        extraction_method = state.get('extraction_method', 'unknown')
        
        print(f"ROUTING: Extraction method={extraction_method}, confidence={nl_confidence:.2f}")
        
        if extraction_method == 'llm' and nl_confidence > 0.6:
            print(f"ROUTING: High LLM confidence, proceeding to ingestion")
            return "ingestion_node"
        elif nl_confidence < 0.4:
            print(f"ROUTING: Low confidence, needs human review")
            return "human_review_node"
        else:
            print(f"ROUTING: Standard processing flow")
            return "ingestion_node"
    
    @staticmethod
    def should_retry_node(state: TransactionProcessingState) -> str:
        """
        Determine if processing should be retried
        """
        retry_count = state.get('retry_count', 0)
        errors = state.get('errors', [])
        
        if errors and retry_count < 2:
            print(f"ROUTING: Retry attempt {retry_count + 1}")
            return "retry_processing"
        elif errors:
            print(f"ROUTING: Max retries reached, marking as failed")
            return "error_handling_node"
        else:
            print(f"ROUTING: No errors, proceeding")
            return "ner_extraction_node"
    
    @staticmethod
    def needs_human_review_node(state: TransactionProcessingState) -> str:
        """
        Determine if human review is needed
        """
        confidence = state.get('confidence_score', 0.0)
        validation_errors = state.get('validation_errors', [])
        is_valid = state.get('is_valid', True)
        
        print(f"REVIEW CHECK: confidence={confidence:.2f}, valid={is_valid}, errors={len(validation_errors)}")
        
        if confidence < 0.3 or not is_valid or len(validation_errors) > 2:
            print(f"ROUTING: Human review required")
            return "human_review_node"
        else:
            print(f"ROUTING: Automated processing sufficient")
            return "finalization_node"

class ErrorHandlingNodes:
    """
    Error handling and recovery nodes
    """
    
    @staticmethod
    def error_handler_node(state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Handle errors in the processing pipeline
        """
        print(f"ERROR HANDLER: Processing errors in workflow")
        
        state['current_stage'] = ProcessingStage.ERROR
        errors = state.get('errors', [])
        
        # Log all errors
        for error in errors:
            logger.error(f"Error in {error.get('stage', 'unknown')}: {error.get('error', 'Unknown error')}")
        
        # Attempt recovery strategies
        recovery_strategies = []
        
        # If NL processing failed, try regex fallback
        if any('nl_processing' in error.get('stage', '') for error in errors):
            recovery_strategies.append("fallback_to_regex")
        
        # If validation failed, try manual entry
        if not state.get('is_valid', True):
            recovery_strategies.append("manual_entry_required")
        
        # Add error handling to processing history
        processing_entry = {
            'stage': ProcessingStage.ERROR.value,
            'timestamp': datetime.now().isoformat(),
            'action': 'error_handling',
            'data': {
                'error_count': len(errors),
                'recovery_strategies': recovery_strategies
            }
        }
        state['processing_history'].append(processing_entry)
        
        print(f"ERROR HANDLER: {len(recovery_strategies)} recovery strategies available")
        
        return state
    
    @staticmethod
    def human_review_node(state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Node for human review requirement
        """
        print(f"👨‍💻 HUMAN REVIEW: Transaction requires manual review")
        
        # Create review summary
        review_data = {
            'workflow_id': state.get('workflow_id'),
            'confidence_score': state.get('confidence_score', 0.0),
            'validation_errors': state.get('validation_errors', []),
            'extracted_transaction': state.get('extracted_transaction', {}),
            'processing_errors': state.get('errors', []),
            'review_reason': 'low_confidence' if state.get('confidence_score', 0) < 0.3 else 'validation_failed'
        }
        
        # Add to processing history
        processing_entry = {
            'stage': 'human_review',
            'timestamp': datetime.now().isoformat(),
            'action': 'human_review_required',
            'data': review_data
        }
        state['processing_history'].append(processing_entry)
        
        # Mark for human review
        state['requires_human_review'] = True
        
        print(f"HUMAN REVIEW: Review request created for workflow {state.get('workflow_id')}")
        
        return state

class UtilityNodes:
    """
    Utility nodes for common operations
    """
    
    @staticmethod
    def logging_node(state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Comprehensive logging node
        """
        workflow_id = state.get('workflow_id', 'unknown')
        current_stage = state.get('current_stage', ProcessingStage.INITIAL)
        confidence = state.get('confidence_score', 0.0)
        
        print(f"WORKFLOW STATUS: {workflow_id} | Stage: {current_stage.value if hasattr(current_stage, 'value') else current_stage} | Confidence: {confidence:.2f}")
        
        return state
    
    @staticmethod
    def metrics_collection_node(state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Collect metrics for monitoring and analytics
        """
        metrics = {
            'workflow_id': state.get('workflow_id'),
            'processing_time': state.get('total_processing_time', 0.0),
            'confidence_score': state.get('confidence_score', 0.0),
            'extraction_method': state.get('extraction_method'),
            'error_count': len(state.get('errors', [])),
            'validation_status': state.get('is_valid', False),
            'nodes_executed': len(state.get('processing_history', [])),
            'retry_count': state.get('retry_count', 0)
        }
        
        # In a real implementation, this would send to monitoring system
        logger.info(f"Workflow metrics: {metrics}")
        
        return state
