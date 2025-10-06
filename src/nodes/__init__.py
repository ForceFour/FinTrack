"""
LangGraph Node Definitions for Transaction Processing Pipeline
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Import states first
try:
    from ..states import TransactionProcessingState, ProcessingStage
    logger.info("States imported successfully")
except Exception as e:
    logger.error(f"Failed to import states: {e}")
    raise

# Delay heavy imports until needed
IngestionAgent = None
IngestionAgentInput = None
NaturalLanguageProcessor = None

def _import_agents():
    """Import agents when needed to avoid hanging on module load"""
    global IngestionAgent, IngestionAgentInput, NaturalLanguageProcessor

    if IngestionAgent is None:
        try:
            from ..agents.ingestion_agent import IngestionAgent, IngestionAgentInput
            logger.info("Ingestion Agent imported")
        except Exception as e:
            logger.warning(f"Ingestion Agent import failed: {e}")

    if NaturalLanguageProcessor is None:
        try:
            from ..agents.components.nl_processor import NaturalLanguageProcessor
            logger.info("NL Processor imported")
        except Exception as e:
            logger.warning(f"NL Processor import failed: {e}")

logger = logging.getLogger(__name__)

class TransactionProcessingNodes:
    """
    Collection of LangGraph nodes for transaction processing workflow
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize nodes with configuration"""
        # Import agents when needed
        _import_agents()

        # Load settings if no config provided
        if not config:
            try:
                from config.settings import get_settings
                settings = get_settings()
                config = {
                    'groq_api_key': settings.groq_api_key,
                    'langgraph_api_key': settings.langgraph_api_key,
                    'openai_api_key': settings.openai_api_key
                }
                logger.info("🔧 Auto-loaded configuration from settings")
            except Exception as e:
                logger.warning(f"Failed to load settings: {e}")
                config = {}

        self.config = config or {}

        # Initialize agents with safe configuration
        try:
            if IngestionAgent:
                self.ingestion_agent = IngestionAgent(config=self.config)
                logger.info("Ingestion Agent initialized")
            else:
                self.ingestion_agent = None
                logger.warning("Ingestion Agent not available")

            if NaturalLanguageProcessor:
                groq_key = self.config.get('groq_api_key')
                if groq_key:
                    self.nl_processor = NaturalLanguageProcessor(groq_api_key=groq_key)
                    logger.info(f"NL Processor initialized with API key: {groq_key[:10]}...")
                else:
                    self.nl_processor = NaturalLanguageProcessor()
                    logger.warning("NL Processor initialized without API key")
            else:
                self.nl_processor = None
                logger.warning("NL Processor not available")

            logger.info("🔧 Transaction Processing Nodes initialized")
        except Exception as e:
            logger.warning(f"Some agents failed to initialize: {e}")
            # Continue with limited functionality for testing
            self.ingestion_agent = None
            self.nl_processor = None

    def initialize_workflow_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Initialize the workflow with advanced setup and metadata
        Merged features from nodes.py
        """
        print(f"WORKFLOW INIT: Starting transaction processing workflow")

        # Generate workflow ID if not present
        if not state.get('workflow_id'):
            state['workflow_id'] = f"txn_workflow_{uuid.uuid4().hex[:8]}"

        # Advanced initialization with better metadata
        state['started_at'] = datetime.now()
        state['current_stage'] = ProcessingStage.INITIAL
        state['processing_history'] = state.get('processing_history', [])
        state['errors'] = state.get('errors', [])
        state['validation_errors'] = state.get('validation_errors', [])
        state['retry_count'] = state.get('retry_count', 0)

        # Advanced metadata
        if 'processing_metadata' not in state:
            state['processing_metadata'] = {}

        state['processing_metadata'].update({
            'version': '2.1_unified',
            'langgraph_enabled': True,
            'groq_enabled': bool(self.config.get('groq_api_key')),
            'unified_agents': True,
            'nl_processor_available': self.nl_processor is not None,
            'ingestion_agent_available': self.ingestion_agent is not None
        })

        # Ensure all required fields exist (advanced error handling)
        required_fields = ['confidence_scores', 'error_log', 'processed_transactions']
        for field in required_fields:
            if field not in state:
                state[field] = []

        # Advanced logging entry
        processing_entry = {
            'stage': ProcessingStage.INITIAL.value,
            'timestamp': datetime.now().isoformat(),
            'action': 'workflow_initialized',
            'workflow_id': state['workflow_id'],
            'metadata': state.get('processing_metadata', {})
        }
        state['processing_history'].append(processing_entry)

        print(f"WORKFLOW INIT: Workflow {state['workflow_id']} initialized")

        return state

    def nl_processing_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Advanced Natural Language Processing using LangChain/Groq
        """
        print(f"NL PROCESSING: Starting NLP with Groq integration")

        try:
            state['current_stage'] = ProcessingStage.NL_PROCESSING

            # Get user input
            user_input = state.get('user_input', '')
            if not user_input:
                raise ValueError("No user input provided for NL processing")

            # Process with enhanced NL processor
            if self.nl_processor and hasattr(self.nl_processor, 'process_input'):
                try:
                    # Use the enhanced NL processor with Groq
                    nl_result = self.nl_processor.process_input(user_input)

                    # Standardize the result format
                    processed_result = {
                        'confidence': nl_result.get('confidence', 0.0),
                        'extraction_method': 'groq_langchain',
                        'transaction_data': {
                            'amount': nl_result.get('amount'),
                            'merchant_name': nl_result.get('merchant'),
                            'description': nl_result.get('description', user_input),
                            'date': nl_result.get('date'),
                            'category': nl_result.get('category'),
                            'payment_method': nl_result.get('payment_method'),
                            'location': nl_result.get('location')
                        },
                        'insights': nl_result.get('insights', {}),
                        'context': nl_result.get('context', {})
                    }

                    print(f"NL PROCESSING: Groq extraction successful with {processed_result['confidence']:.2f} confidence")

                except Exception as groq_error:
                    print(f"Groq processing failed: {groq_error}, falling back to regex")
                    processed_result = self._fallback_nl_extraction(user_input)
            else:
                print(f"NL Processor not available, using fallback regex extraction")
                processed_result = self._fallback_nl_extraction(user_input)

            # Store comprehensive NL results
            state['nl_processing_result'] = processed_result
            state['extracted_transaction'] = processed_result['transaction_data']
            state['nl_confidence'] = processed_result['confidence']
            state['extraction_method'] = processed_result['extraction_method']
            state['language_insights'] = processed_result.get('insights', {})

            # Update confidence tracking
            state['confidence_scores'] = state.get('confidence_scores', [])
            state['confidence_scores'].append({
                'stage': 'nl_processing',
                'confidence': processed_result['confidence'],
                'method': processed_result['extraction_method']
            })

            # Add to processing history
            processing_entry = {
                'stage': ProcessingStage.NL_PROCESSING.value,
                'timestamp': datetime.now().isoformat(),
                'action': 'nl_extraction_completed',
                'data': {
                    'confidence': processed_result['confidence'],
                    'extraction_method': processed_result['extraction_method'],
                    'fields_extracted': len([v for v in processed_result['transaction_data'].values() if v is not None]),
                    'amount_extracted': processed_result['transaction_data'].get('amount') is not None,
                    'merchant_extracted': processed_result['transaction_data'].get('merchant_name') is not None
                }
            }
            state['processing_history'].append(processing_entry)

            print(f"NL PROCESSING: Completed - Amount: ${processed_result['transaction_data'].get('amount', 'N/A')}, Merchant: {processed_result['transaction_data'].get('merchant_name', 'N/A')}")

        except Exception as e:
            error_info = {
                'stage': ProcessingStage.NL_PROCESSING.value,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
            # Ensure error_log exists
            if 'error_log' not in state:
                state['error_log'] = []
            state['error_log'].append(error_info)
            state['current_stage'] = ProcessingStage.ERROR
            logger.error(f"NL Processing failed: {e}")

        return state

    def _fallback_nl_extraction(self, user_input: str) -> Dict[str, Any]:
        """Fallback NL extraction using regex patterns"""
        import re
        from datetime import datetime

        # Enhanced regex patterns
        amount_patterns = [
            r'\$(\d+(?:\.\d{2})?)',  # $123.45
            r'(\d+(?:\.\d{2})?)\s*dollars?',  # 123.45 dollars
            r'spent\s+(\d+(?:\.\d{2})?)',  # spent 123.45
            r'cost\s+(\d+(?:\.\d{2})?)',  # cost 123.45
        ]

        merchant_patterns = [
            r'at\s+([A-Za-z][A-Za-z\s&\'-]+?)(?:\s+(?:for|yesterday|today|on|$))',
            r'from\s+([A-Za-z][A-Za-z\s&\'-]+?)(?:\s+(?:for|yesterday|today|on|$))',
            r'([A-Za-z][A-Za-z\s&\'-]+?)\s+(?:charged|billed)',
            r'paid\s+([A-Za-z][A-Za-z\s&\'-]+?)(?:\s+(?:for|$))',
        ]

        category_keywords = {
            'food': ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonalds', 'food', 'lunch', 'dinner'],
            'gas': ['gas', 'fuel', 'shell', 'exxon', 'chevron', 'bp'],
            'groceries': ['grocery', 'supermarket', 'walmart', 'target', 'wholefds', 'whole foods'],
            'shopping': ['amazon', 'ebay', 'store', 'mall', 'shopping'],
            'entertainment': ['movie', 'netflix', 'spotify', 'entertainment'],
            'transportation': ['uber', 'lyft', 'taxi', 'bus', 'train']
        }

        # Extract amount
        amount = None
        for pattern in amount_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1))
                    break
                except ValueError:
                    continue

        # Extract merchant
        merchant_name = None
        for pattern in merchant_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                potential_merchant = match.group(1).strip()
                if len(potential_merchant) > 1 and not potential_merchant.isdigit():
                    merchant_name = potential_merchant
                    break

        # Determine category
        category = 'miscellaneous'
        user_input_lower = user_input.lower()
        for cat, keywords in category_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                category = cat
                break

        # Calculate confidence
        confidence = 0.3  # Base confidence
        if amount is not None:
            confidence += 0.3
        if merchant_name:
            confidence += 0.3
        if category != 'miscellaneous':
            confidence += 0.1

        return {
            'confidence': min(confidence, 0.9),
            'extraction_method': 'regex_fallback',
            'transaction_data': {
                'amount': amount,
                'merchant_name': merchant_name,
                'description': user_input[:100],
                'date': datetime.now().isoformat(),
                'category': category,
                'payment_method': None,
                'location': None
            },
            'insights': {
                'amount_found': amount is not None,
                'merchant_found': merchant_name is not None,
                'category_inferred': category != 'miscellaneous'
            },
            'context': {'fallback_used': True}
        }

    def ingestion_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Enhanced Ingestion processing - simplified and reliable
        """
        print(f"INGESTION: Starting transaction ingestion and preprocessing")

        try:
            state['current_stage'] = ProcessingStage.INGESTION

            # Get the extracted transaction from NL processing
            extracted_transaction = state.get('extracted_transaction', {})
            user_input = state.get('user_input', '')

            if not extracted_transaction and not user_input:
                raise ValueError("No transaction data available for ingestion")

            # Create a properly formatted transaction from the extracted data
            if extracted_transaction:
                # Convert amount to float if it's a string
                raw_amount = extracted_transaction.get('amount', 0.0)
                if isinstance(raw_amount, str):
                    # Remove currency symbols and convert to float
                    try:
                        clean_amount = float(raw_amount.replace('$', '').replace(',', ''))
                    except (ValueError, AttributeError):
                        clean_amount = 0.0
                else:
                    clean_amount = float(raw_amount) if raw_amount else 0.0

                # Use the data from NL processing
                preprocessed_txn = {
                    'id': f"txn_{uuid.uuid4().hex[:8]}",
                    'amount': clean_amount,
                    'merchant_name': extracted_transaction.get('merchant_name', 'Unknown'),
                    'description': extracted_transaction.get('description', user_input[:100]),
                    'date': extracted_transaction.get('date') or datetime.now().isoformat(),
                    'category': extracted_transaction.get('category', 'miscellaneous'),
                    'payment_method': extracted_transaction.get('payment_method', 'unknown'),
                    'has_discount': False,
                    'metadata': {
                        'processed_by': 'enhanced_ingestion',
                        'source': 'nl_extraction',
                        'confidence': state.get('nl_confidence', 0.0),
                        'extraction_method': state.get('extraction_method', 'unknown')
                    }
                }
            else:
                # Fallback to basic extraction from user input
                preprocessed_txn = self._normalize_transaction_data({}, user_input)

            # Store the preprocessed transaction
            preprocessed_txns = [preprocessed_txn]

            # Calculate confidence based on data completeness
            ingestion_confidence = self._calculate_ingestion_confidence(preprocessed_txn)

            # Calculate data quality scores
            quality_scores = self._calculate_data_quality(preprocessed_txns)

            # Store comprehensive ingestion results
            state['preprocessed_transactions'] = preprocessed_txns
            state['ingestion_metadata'] = {
                'processor': 'enhanced_ingestion_simplified',
                'confidence': ingestion_confidence,
                'processing_timestamp': datetime.now().isoformat()
            }
            state['ingestion_confidence'] = ingestion_confidence
            state['data_quality_scores'] = quality_scores

            # Update confidence tracking
            state['confidence_scores'] = state.get('confidence_scores', [])
            state['confidence_scores'].append({
                'stage': 'ingestion',
                'confidence': ingestion_confidence,
                'quality_score': quality_scores.get('overall', 0.0)
            })

            # Add to processing history
            processing_entry = {
                'stage': ProcessingStage.INGESTION.value,
                'timestamp': datetime.now().isoformat(),
                'action': 'ingestion_completed',
                'data': {
                    'transactions_processed': len(preprocessed_txns),
                    'ingestion_confidence': ingestion_confidence,
                    'quality_scores': quality_scores,
                    'processor': 'enhanced_ingestion_simplified'
                }
            }
            state['processing_history'].append(processing_entry)

            # Display results
            txn = preprocessed_txns[0]
            print(f"   Processed Transaction:")
            print(f"      • ID: {txn['id']}")
            print(f"      • Amount: ${txn['amount']}")
            print(f"      • Merchant: {txn['merchant_name']}")
            print(f"      • Category: {txn['category']}")
            print(f"      • Date: {txn['date'][:10]}")

            print(f"INGESTION: Successfully processed 1 transaction with {ingestion_confidence:.2f} confidence")

        except Exception as e:
            error_info = {
                'stage': ProcessingStage.INGESTION.value,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
            # Ensure error_log exists
            if 'error_log' not in state:
                state['error_log'] = []
            state['error_log'].append(error_info)
            state['current_stage'] = ProcessingStage.ERROR
            logger.error(f"❌ Ingestion failed: {e}")

        return state

    def _calculate_ingestion_confidence(self, transaction: Dict[str, Any]) -> float:
        """Calculate confidence based on transaction data completeness"""
        confidence = 0.0

        # Check amount - handle both string and numeric values
        amount = transaction.get('amount')
        if amount:
            try:
                if isinstance(amount, str):
                    amount_value = float(amount.replace('$', '').replace(',', ''))
                else:
                    amount_value = float(amount)

                if amount_value > 0:
                    confidence += 0.3
            except (ValueError, TypeError, AttributeError):
                pass

        # Check merchant
        if transaction.get('merchant_name') and transaction['merchant_name'] != 'Unknown':
            confidence += 0.3

        # Check category
        if transaction.get('category') and transaction['category'] != 'miscellaneous':
            confidence += 0.2

        # Check date
        if transaction.get('date'):
            confidence += 0.1

        # Check description
        if transaction.get('description') and len(transaction['description']) > 5:
            confidence += 0.1

        return min(confidence, 1.0)

    def _normalize_transaction_data(self, extracted_data: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Normalize transaction data to standard format"""
        from datetime import datetime

        return {
            'id': f"txn_{uuid.uuid4().hex[:8]}",
            'amount': extracted_data.get('amount') or 0.0,
            'merchant_name': extracted_data.get('merchant_name') or 'Unknown Merchant',
            'description': extracted_data.get('description') or user_input[:100],
            'date': extracted_data.get('date') or datetime.now().isoformat(),
            'category': extracted_data.get('category') or 'miscellaneous',
            'payment_method': extracted_data.get('payment_method') or 'unknown',
            'has_discount': False,
            'metadata': {
                'processed_by': 'internal_normalizer',
                'confidence': 0.6,
                'source': 'nl_extraction'
            }
        }

    def _calculate_data_quality(self, transactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate data quality scores for transactions"""
        if not transactions:
            return {'overall': 0.0, 'completeness': 0.0, 'accuracy': 0.0}

        total_fields = 0
        filled_fields = 0
        valid_amounts = 0

        for txn in transactions:
            # Count completeness
            fields = ['amount', 'merchant_name', 'description', 'date', 'category']
            for field in fields:
                total_fields += 1
                value = txn.get(field)
                if value and str(value).strip() and str(value) not in ['Unknown', 'unknown', 'N/A']:
                    filled_fields += 1

            # Check amount validity
            amount = txn.get('amount', 0)
            if isinstance(amount, (int, float)) and amount > 0:
                valid_amounts += 1

        completeness = filled_fields / total_fields if total_fields > 0 else 0.0
        accuracy = valid_amounts / len(transactions) if transactions else 0.0
        overall = (completeness + accuracy) / 2

        return {
            'overall': round(overall, 2),
            'completeness': round(completeness, 2),
            'accuracy': round(accuracy, 2)
        }

    def ner_extraction_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Named Entity Recognition node for merchant and location extraction
        """
        print(f"NER: Starting named entity recognition")

        try:
            state['current_stage'] = ProcessingStage.NER_EXTRACTION

            # Extract description for NER processing
            description = state.get('extracted_transaction', {}).get('description', '')
            if not description:
                description = state.get('raw_input', '')

            # Placeholder for NER processing (to be implemented with spaCy or similar)
            # For now, we'll use the data we already extracted
            extracted_transaction = state.get('extracted_transaction', {})

            state['ner_entities'] = {
                'merchants': [extracted_transaction.get('merchant')] if extracted_transaction.get('merchant') else [],
                'locations': [extracted_transaction.get('location')] if extracted_transaction.get('location') else [],
                'amounts': [extracted_transaction.get('amount')] if extracted_transaction.get('amount') else [],
                'dates': [extracted_transaction.get('date')] if extracted_transaction.get('date') else []
            }

            state['merchant_info'] = {
                'primary_merchant': extracted_transaction.get('merchant'),
                'confidence': 0.8 if extracted_transaction.get('merchant') else 0.1
            }

            state['location_info'] = {
                'primary_location': extracted_transaction.get('location'),
                'confidence': 0.7 if extracted_transaction.get('location') else 0.1
            }

            # Add to processing history
            processing_entry = {
                'stage': ProcessingStage.NER_EXTRACTION.value,
                'timestamp': datetime.now().isoformat(),
                'action': 'ner_completed',
                'data': {
                    'entities_found': sum(len(entities) for entities in state['ner_entities'].values()),
                    'merchant_confidence': state['merchant_info']['confidence']
                }
            }
            state['processing_history'].append(processing_entry)

            print(f"NER: Extracted entities - Merchants: {len(state['ner_entities']['merchants'])}, Locations: {len(state['ner_entities']['locations'])}")

        except Exception as e:
            error_info = {
                'stage': ProcessingStage.NER_EXTRACTION.value,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
            state['errors'].append(error_info)
            logger.error(f"NER extraction failed: {e}")

        return state

    def classification_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Transaction classification node
        """
        print(f"CLASSIFICATION: Starting transaction classification")

        try:
            state['current_stage'] = ProcessingStage.CLASSIFICATION

            # Use the category from NL processing or default
            extracted_transaction = state.get('extracted_transaction', {})
            predicted_category = extracted_transaction.get('category', 'miscellaneous')

            state['predicted_category'] = predicted_category
            state['category_confidence'] = 0.8 if predicted_category != 'miscellaneous' else 0.3

            # Add to processing history
            processing_entry = {
                'stage': ProcessingStage.CLASSIFICATION.value,
                'timestamp': datetime.now().isoformat(),
                'action': 'classification_completed',
                'data': {
                    'predicted_category': state['predicted_category'],
                    'confidence': state['category_confidence']
                }
            }
            state['processing_history'].append(processing_entry)

            print(f"CLASSIFICATION: Classified as '{state['predicted_category']}' with {state['category_confidence']:.2f} confidence")

        except Exception as e:
            error_info = {
                'stage': ProcessingStage.CLASSIFICATION.value,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
            state['errors'].append(error_info)
            logger.error(f"❌ Classification failed: {e}")

        return state

    def validation_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Transaction validation node
        """
        print(f"VALIDATION: Starting transaction validation")

        try:
            state['current_stage'] = ProcessingStage.VALIDATION
            state['validation_errors'] = state.get('validation_errors', [])

            extracted_transaction = state.get('extracted_transaction', {})

            # Validation rules
            if not extracted_transaction.get('amount'):
                state['validation_errors'].append("Missing transaction amount")

            if not extracted_transaction.get('description'):
                state['validation_errors'].append("Missing transaction description")

            if state.get('confidence_score', 0) < 0.3:
                state['validation_errors'].append("Low extraction confidence")

            # Set validation status
            state['is_valid'] = len(state['validation_errors']) == 0

            # Add to processing history
            processing_entry = {
                'stage': ProcessingStage.VALIDATION.value,
                'timestamp': datetime.now().isoformat(),
                'action': 'validation_completed',
                'data': {
                    'is_valid': state['is_valid'],
                    'error_count': len(state['validation_errors'])
                }
            }
            state['processing_history'].append(processing_entry)

            if state['is_valid']:
                print(f"VALIDATION: Transaction is valid")
            else:
                print(f"VALIDATION: {len(state['validation_errors'])} validation errors found")

        except Exception as e:
            error_info = {
                'stage': ProcessingStage.VALIDATION.value,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
            state['errors'].append(error_info)
            logger.error(f"Validation failed: {e}")

        return state

    def finalization_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Final node to complete the workflow
        """
        print(f"FINALIZATION: Completing transaction processing workflow")

        try:
            state['current_stage'] = ProcessingStage.COMPLETED
            state['completed_at'] = datetime.now()

            # Calculate total processing time
            if state.get('started_at'):
                total_time = (state['completed_at'] - state['started_at']).total_seconds()
                state['total_processing_time'] = total_time

            # Build final transaction
            extracted_transaction = state.get('extracted_transaction', {})
            preprocessed_data = state.get('preprocessed_transactions', [])

            final_transaction = {
                **extracted_transaction,
                'workflow_id': state.get('workflow_id'),
                'predicted_category': state.get('predicted_category'),
                'ner_entities': state.get('ner_entities'),
                'confidence_score': state.get('confidence_score', 0.0),
                'extraction_method': state.get('extraction_method'),
                'is_valid': state.get('is_valid', False),
                'processing_time_seconds': state.get('total_processing_time', 0.0),
                'preprocessed_data': preprocessed_data[0] if preprocessed_data else None
            }

            state['final_transaction'] = final_transaction

            # Final processing history entry
            processing_entry = {
                'stage': ProcessingStage.COMPLETED.value,
                'timestamp': datetime.now().isoformat(),
                'action': 'workflow_completed',
                'data': {
                    'total_processing_time': state.get('total_processing_time', 0.0),
                    'final_confidence': state.get('confidence_score', 0.0),
                    'is_valid': state.get('is_valid', False),
                    'error_count': len(state.get('errors', []))
                }
            }
            state['processing_history'].append(processing_entry)

            print(f"🎉 FINALIZATION: Workflow completed in {state.get('total_processing_time', 0):.2f}s with {state.get('confidence_score', 0):.2f} confidence")

        except Exception as e:
            logger.error(f"Finalization failed: {e}")
            state['current_stage'] = ProcessingStage.ERROR

        return state

    def _add_error_to_state(self, state: TransactionProcessingState, stage: str, error: Exception) -> None:
        """
        Enhanced error handling utility from enhanced_nodes.py
        Adds structured error information to state
        """
        error_info = {
            'stage': stage,
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'error_type': type(error).__name__
        }

        # Ensure error_log exists
        if 'error_log' not in state:
            state['error_log'] = []

        state['error_log'].append(error_info)
        state['current_stage'] = ProcessingStage.ERROR
        logger.error(f"{stage.upper()} failed: {error}")

    def _update_confidence_tracking(self, state: TransactionProcessingState, stage: str, confidence: float, method: str = None) -> None:
        """
        Enhanced confidence tracking utility from enhanced_nodes.py
        """
        if 'confidence_scores' not in state:
            state['confidence_scores'] = []

        confidence_entry = {
            'stage': stage,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }

        if method:
            confidence_entry['method'] = method

        state['confidence_scores'].append(confidence_entry)

    def _add_processing_history(self, state: TransactionProcessingState, stage: str, action: str, data: Dict[str, Any] = None) -> None:
        """
        Enhanced processing history utility from enhanced_nodes.py
        """
        if 'processing_history' not in state:
            state['processing_history'] = []

        history_entry = {
            'stage': stage,
            'timestamp': datetime.now().isoformat(),
            'action': action
        }

        if data:
            history_entry['data'] = data

        state['processing_history'].append(history_entry)
