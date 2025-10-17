"""
LangGraph Node Definitions for Transaction Processing Pipeline
"""
import logging
import os
from typing import Dict, Any, List
from datetime import datetime
import uuid
import re

logger = logging.getLogger(__name__)

# Import states first
try:
    from ..states import TransactionProcessingState, ProcessingStage
    from ..schemas.transaction_schemas import TransactionCategory, TransactionType, PaymentMethod
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

            logger.info("Transaction Processing Nodes initialized")
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
        Enhanced Ingestion processing - handles both raw transactions and NL extraction
        """
        print(f"INGESTION: Starting transaction ingestion and preprocessing")

        try:
            state['current_stage'] = ProcessingStage.INGESTION

            # Check if raw transactions are provided (structured input)
            raw_transactions = state.get('raw_transactions', [])
            if raw_transactions and len(raw_transactions) > 0:
                print(f"INGESTION: Processing {len(raw_transactions)} raw transactions")

                # Process raw transactions directly
                preprocessed_txns = []
                for raw_txn in raw_transactions:
                    # Extract merchant from description if not provided in merchant column
                    merchant_name = raw_txn.get('merchant', '').strip()
                    if not merchant_name or merchant_name.lower() in ['unknown', 'unknown merchant']:
                        # Try to extract from description
                        description = raw_txn.get('description', '')
                        if ' from ' in description.lower():
                            # Extract merchant from "Purchased ... from [Merchant]" pattern
                            parts = description.lower().split(' from ')
                            if len(parts) > 1:
                                merchant_name = parts[1].strip()
                                # Clean up common endings
                                merchant_name = merchant_name.split(' (')[0].strip()  # Remove parentheses
                        elif ' at ' in description.lower():
                            # Extract merchant from "at [Merchant]" pattern
                            parts = description.lower().split(' at ')
                            if len(parts) > 1:
                                merchant_name = parts[1].strip()
                        else:
                            # Fallback to first meaningful word
                            words = description.split()
                            if words:
                                merchant_name = words[0].strip()

                    # Extract category from description if not provided in category column
                    category = raw_txn.get('category', '').strip()
                    if not category or category.lower() in ['miscellaneous', 'unknown']:
                        # Try to extract from description
                        description = raw_txn.get('description', '')
                        if 'purchased ' in description.lower():
                            # Extract category from "Purchased [category] from ..." pattern
                            purchased_part = description.lower().split('purchased ')[1].split(' from ')[0].strip()
                            category = purchased_part
                            # Map to standard categories
                            category_mapping = {
                                'donations & charity': 'donations_charity',
                                'fitness & wellness (gym, spa)': 'fitness_wellness',
                                'household (furniture, appliances)': 'household',
                                'shopping (clothes, electronics)': 'shopping',
                                'travel & accommodation': 'travel_accommodation',
                                'beauty & personal care (salons, cosmetics)': 'beauty_personal_care',
                                'business expenses': 'business_expenses'
                            }
                            category = category_mapping.get(category.lower(), category.lower().replace(' ', '_'))

                    # Convert raw transaction dict to preprocessed format
                    amount_value = raw_txn.get('amount', '0')
                    if isinstance(amount_value, str):
                        amount_value = amount_value.replace('$', '').replace(',', '')

                    amount_float = float(amount_value)

                    # Determine transaction type based on amount sign
                    # Positive = income, Negative = expense
                    if raw_txn.get('transaction_type'):
                        # Use explicitly provided transaction type if available
                        transaction_type = raw_txn.get('transaction_type')
                    else:
                        # Determine from amount: positive = income, negative/zero = expense
                        transaction_type = 'income' if amount_float > 0 else 'expense'

                    # Store NEGATIVE amounts for expenses (database convention)
                    # If amount is already negative (expense), keep it
                    # If amount is positive and it's an expense (rare), make it negative
                    # If amount is positive and it's income, keep it positive
                    if transaction_type == 'expense' and amount_float > 0:
                        amount_float = -amount_float
                    elif transaction_type == 'income' and amount_float < 0:
                        # If marked as income but amount is negative, fix it
                        amount_float = abs(amount_float)

                    preprocessed_txn = {
                        'id': raw_txn.get('id', f"txn_{uuid.uuid4().hex[:8]}"),
                        'amount': amount_float,
                        'merchant_name': merchant_name,
                        'description': raw_txn.get('description', ''),
                        'date': raw_txn.get('date', datetime.now().isoformat()),
                        'category': category,
                        'payment_method': raw_txn.get('payment_method', 'unknown'),
                        'transaction_type': transaction_type,
                        'has_discount': False,
                        'metadata': {
                            'processed_by': 'raw_transaction_ingestion',
                            'source': 'structured_input',
                            'confidence': 0.9,  # High confidence for structured input
                            'extraction_method': 'direct'
                        }
                    }
                    preprocessed_txns.append(preprocessed_txn)

                ingestion_confidence = 0.9  # High confidence for structured data

            else:
                # Fall back to NL processing extraction
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
                'processor': 'enhanced_ingestion_with_raw_support',
                'confidence': ingestion_confidence,
                'processing_timestamp': datetime.now().isoformat(),
                'input_type': 'structured' if raw_transactions else 'unstructured',
                'transactions_count': len(preprocessed_txns)
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
                    'processor': 'enhanced_ingestion_with_raw_support'
                }
            }
            state['processing_history'].append(processing_entry)

            # Display results
            if len(preprocessed_txns) == 1:
                txn = preprocessed_txns[0]
                print(f"   Processed Transaction:")
                print(f"      • ID: {txn['id']}")
                print(f"      • Amount: ${txn['amount']}")
                print(f"      • Merchant: {txn['merchant_name']}")
                print(f"      • Category: {txn['category']}")
                print(f"      • Date: {txn['date'][:10]}")
            else:
                print(f"   Processed {len(preprocessed_txns)} transactions:")
                for i, txn in enumerate(preprocessed_txns[:3], 1):  # Show first 3
                    merchant = txn['merchant_name'][:20] if len(txn['merchant_name']) > 20 else txn['merchant_name']
                    print(f"      {i}. {merchant}: ${txn['amount']} ({txn['date'][:10]})")
                if len(preprocessed_txns) > 3:
                    print(f"      ... and {len(preprocessed_txns) - 3} more")

            print(f"INGESTION: Successfully processed {len(preprocessed_txns)} transaction{'s' if len(preprocessed_txns) != 1 else ''} with {ingestion_confidence:.2f} confidence")

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
            logger.error(f"Ingestion failed: {e}")

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
        Transaction classification node using the ClassifierAgent
        """
        print(f"CLASSIFICATION: Starting transaction classification with ClassifierAgent")

        try:
            state['current_stage'] = ProcessingStage.CLASSIFICATION
            # Initialize errors list if not present
            if 'errors' not in state:
                state['errors'] = []
            # Initialize processing_history if not present
            if 'processing_history' not in state:
                state['processing_history'] = []

            # Get preprocessed transactions to classify
            preprocessed_txns = state.get('preprocessed_transactions', [])
            if preprocessed_txns:
                # Import ClassifierAgent
                try:
                    from ..agents.classifier_agent import ClassifierAgent, ClassifierAgentInput
                    classifier_agent = ClassifierAgent()
                except Exception as e:
                    logger.error(f"Failed to import ClassifierAgent: {e}")
                    # Fallback to simple classification
                    return self._fallback_classification(state)

                # Convert preprocessed transactions to MerchantTransaction objects
                merchant_transactions = self._convert_to_merchant_transactions(preprocessed_txns)

                # Use ClassifierAgent for comprehensive classification
                input_data = ClassifierAgentInput(merchant_transactions=merchant_transactions)
                result = classifier_agent.process(input_data)

                # Store the classified transactions
                state['processed_transactions'] = result.classified_transactions
                state['predicted_category'] = 'multiple_categories'  # For backward compatibility
                state['category_confidence'] = sum(result.confidence_scores) / len(result.confidence_scores) if result.confidence_scores else 0.8

                print(f"CLASSIFICATION: ClassifierAgent processed {len(result.classified_transactions)} transactions")
            else:
                # Fallback to single transaction classification
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
                    'predicted_category': state.get('predicted_category', 'unknown'),
                    'confidence': state.get('category_confidence', 0.0),
                    'transactions_classified': len(state.get('processed_transactions', []))
                }
            }
            state['processing_history'].append(processing_entry)

            print(f"CLASSIFICATION: Completed with {state.get('category_confidence', 0):.2f} average confidence")

        except Exception as e:
            error_info = {
                'stage': ProcessingStage.CLASSIFICATION.value,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
            state['errors'].append(error_info)
            logger.error(f"Classification failed: {e}")
            # Fallback to simple classification
            return self._fallback_classification(state)

        return state

    def _convert_to_merchant_transactions(self, preprocessed_txns: List[Dict[str, Any]]) -> List:
        """
        Convert preprocessed transaction dicts to MerchantTransaction objects for ClassifierAgent
        """
        from ..schemas.transaction_schemas import MerchantTransaction, TransactionType, PaymentMethod

        merchant_transactions = []
        for txn_dict in preprocessed_txns:
            try:
                # Parse date
                date_str = txn_dict.get('date', datetime.now().isoformat())
                if isinstance(date_str, str):
                    try:
                        parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        parsed_date = datetime.now()
                else:
                    parsed_date = date_str if isinstance(date_str, datetime) else datetime.now()

                # Handle payment method
                payment_method_str = txn_dict.get('payment_method', 'cash')
                try:
                    payment_method = PaymentMethod(payment_method_str)
                except ValueError:
                    payment_method = PaymentMethod.CASH

                # Handle transaction type
                transaction_type_str = txn_dict.get('transaction_type', 'expense')
                try:
                    transaction_type = TransactionType(transaction_type_str)
                except ValueError:
                    transaction_type = TransactionType.EXPENSE

                # Create MerchantTransaction
                merchant_txn = MerchantTransaction(
                    id=txn_dict.get('id', f"txn_{uuid.uuid4().hex[:8]}"),
                    date=parsed_date,
                    year=parsed_date.year,
                    month=parsed_date.month,
                    day=parsed_date.day,
                    day_of_week=parsed_date.weekday(),
                    amount=float(txn_dict.get('amount', 0.0)),
                    transaction_type=transaction_type,
                    payment_method=payment_method,
                    description_cleaned=txn_dict.get('description', ''),
                    merchant_name=txn_dict.get('merchant_name'),
                    merchant_standardized=txn_dict.get('merchant_name'),
                    merchant_category=txn_dict.get('category'),
                    is_merchant_known=bool(txn_dict.get('merchant_name')),
                    has_discount=txn_dict.get('has_discount', False),
                    metadata=txn_dict.get('metadata', {})
                )
                merchant_transactions.append(merchant_txn)
            except Exception as e:
                logger.warning(f"Failed to convert transaction {txn_dict.get('id')}: {e}")
                continue

        return merchant_transactions

    def _fallback_classification(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Fallback classification using simple keyword-based approach
        """
        print("CLASSIFICATION: Using fallback classification method")

        preprocessed_txns = state.get('preprocessed_transactions', [])
        if preprocessed_txns:
            classified_transactions = []
            for txn in preprocessed_txns:
                description = txn.get('description', '').lower()
                merchant = txn.get('merchant_name', '').lower()
                existing_category = txn.get('category', '').lower()

                if existing_category and existing_category not in ['miscellaneous', 'unknown', '']:
                    category_mapping = {
                        'donations & charity': 'RELIGIOUS_DONATIONS',
                        'fitness & wellness (gym, spa)': 'HEALTHCARE',
                        'household (furniture, appliances)': 'SHOPPING',
                        'shopping (clothes, electronics)': 'SHOPPING',
                        'travel & accommodation': 'TRAVEL',
                        'beauty & personal care (salons, cosmetics)': 'HEALTHCARE',
                        'business expenses': 'MISCELLANEOUS',
                        'miscellaneous': 'MISCELLANEOUS'
                    }
                    category = category_mapping.get(existing_category, 'MISCELLANEOUS')
                    confidence = 0.95
                else:
                    category, confidence = self._classify_transaction(description, merchant)

                classified_txn = self._convert_single_transaction_to_classified_object(txn, category, confidence)
                classified_transactions.append(classified_txn)

            state['processed_transactions'] = classified_transactions
            state['predicted_category'] = 'multiple_categories'
            state['category_confidence'] = 0.8

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

    def pattern_analyzer_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Pattern analysis node - analyzes spending patterns and trends
        """
        print(f"PATTERN ANALYSIS: Starting pattern analysis")

        try:
            from ..agents.pattern_analyzer_agent import PatternAnalyzerAgent

            state['current_stage'] = ProcessingStage.PATTERN_ANALYSIS
            pattern_agent = PatternAnalyzerAgent()

            # Get processed transactions for analysis
            transactions = state.get('processed_transactions', [])
            print(f"PATTERN ANALYSIS: DEBUG - processed_transactions: {len(transactions)} items")
            if not transactions:
                # Try preprocessed transactions and convert them
                preprocessed = state.get('preprocessed_transactions', [])
                print(f"PATTERN ANALYSIS: DEBUG - preprocessed_transactions: {len(preprocessed)} items")
                if preprocessed:
                    transactions = self._convert_to_classified_transactions(preprocessed)
                    print(f"PATTERN ANALYSIS: DEBUG - converted transactions: {len(transactions)} items")
                elif state.get('final_transaction'):
                    transactions = [state['final_transaction']]
                    print(f"PATTERN ANALYSIS: DEBUG - using final_transaction: {len(transactions)} items")

            print(f"PATTERN ANALYSIS: DEBUG - final transactions for analysis: {len(transactions)} items")
            if transactions:
                print(f"PATTERN ANALYSIS: DEBUG - first transaction: {transactions[0] if transactions else 'None'}")

            if transactions:
                # Analyze patterns using the process method
                pattern_result = pattern_agent.process(transactions)

                print(f"PATTERN ANALYSIS: DEBUG - pattern_result keys: {list(pattern_result.keys())}")
                print(f"PATTERN ANALYSIS: DEBUG - pattern_insights count: {len(pattern_result.get('pattern_insights', []))}")
                if pattern_result.get('pattern_insights'):
                    print(f"PATTERN ANALYSIS: DEBUG - first insight: {pattern_result['pattern_insights'][0]}")

                state['spending_patterns'] = pattern_result.get('spending_trends', {})
                state['pattern_insights'] = pattern_result.get('pattern_insights', [])
                state['pattern_confidence'] = 0.85  # Default confidence for pattern analysis

                print(f"PATTERN ANALYSIS: Found {len(state['pattern_insights'])} pattern insights")
            else:
                # For first-time users or no transactions, create baseline pattern structure
                print(f"PATTERN ANALYSIS: No transactions to analyze - creating baseline for new user")

                state['spending_patterns'] = {
                    'transaction_count': 0,
                    'analysis_type': 'new_user_baseline',
                    'message': 'Insufficient transaction history for pattern analysis. Start tracking transactions to unlock insights!'
                }

                # Create default insights for new users
                state['pattern_insights'] = [
                    {
                        'insight_type': 'new_user_guidance',
                        'description': 'Welcome! Track your transactions to unlock spending pattern analysis.',
                        'severity': 'info',
                        'category': 'onboarding',
                        'transactions_involved': [],
                        'metadata': {
                            'guidance': 'Add more transactions to see spending trends and patterns',
                            'next_steps': ['Record daily expenses', 'Categorize transactions accurately', 'Review monthly summaries']
                        }
                    }
                ]

                state['pattern_confidence'] = 0.3  # Lower confidence for new users
                print(f"PATTERN ANALYSIS: Created baseline analysis for new user")

            # Add to processing history
            processing_entry = {
                'stage': 'pattern_analysis',
                'timestamp': datetime.now().isoformat(),
                'action': 'pattern_analysis_completed',
                'data': {
                    'patterns_found': len(state.get('spending_patterns', {})),
                    'confidence': state.get('pattern_confidence', 0.0)
                }
            }
            state['processing_history'].append(processing_entry)

        except Exception as e:
            error_info = {
                'stage': 'pattern_analysis',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
            state['errors'].append(error_info)
            logger.error(f"Pattern analysis failed: {e}")

        return state

    def suggestion_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Suggestion node - generates budget recommendations and spending advice
        """
        print(f"SUGGESTION: Starting suggestion generation")

        try:
            from ..agents.suggestion_agent import SuggestionAgent, SuggestionAgentInput
            from ..schemas.transaction_schemas import PatternInsight
            from ..services.transaction_service import TransactionService
            from supabase import create_client

            state['current_stage'] = ProcessingStage.SUGGESTION

            # Initialize TransactionService for database access
            # Use SERVICE_ROLE key to bypass RLS for backend operations
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Changed from ANON_KEY to SERVICE_ROLE_KEY
            if supabase_url and supabase_key:
                supabase_client = create_client(supabase_url, supabase_key)
                transaction_service = TransactionService(supabase_client)
            else:
                transaction_service = None

            suggestion_agent = SuggestionAgent(transaction_service=transaction_service)

            # Get pattern insights and prepare input
            pattern_insights_data = state.get('pattern_insights', {})
            transactions = state.get('processed_transactions', [])

            # Convert pattern insights to PatternInsight objects
            pattern_insights = []
            if pattern_insights_data:
                if isinstance(pattern_insights_data, list):
                    # Already a list of insights
                    for insight in pattern_insights_data:
                        if isinstance(insight, dict):
                            pattern_insights.append(PatternInsight(**insight))
                elif isinstance(pattern_insights_data, dict):
                    # Convert dict format to PatternInsight objects
                    for key, value in pattern_insights_data.items():
                        if isinstance(value, dict):
                            pattern_insights.append(PatternInsight(
                                insight_type=key,
                                description=f"Pattern analysis for {key}",
                                severity="medium",
                                transactions_involved=[],
                                metadata=value
                            ))

            # No default insights for new users - they should upload transactions first
            # Pattern insights will be generated from actual transaction data

            # Default budget thresholds if not provided
            budget_thresholds = state.get('budget_thresholds', {
                'groceries': 300,
                'dining': 200,
                'entertainment': 150,
                'shopping': 250,
                'transportation': 100,
                'utilities': 200,
                'healthcare': 150,
                'savings': 300
            })

            # Get user preferences from conversation context or state
            user_preferences = state.get('user_preferences', {})
            if not user_preferences:
                conversation_context = state.get('conversation_context', {})
                user_preferences = conversation_context.get('user_preferences', {})

            # Get user_id from state
            user_id = state.get('user_id', 'default_user')

            # Prepare user preferences for the agent
            # The agent will query the database for accurate transaction count
            # We don't set transaction_count here to avoid confusion
            if 'transaction_count' in user_preferences:
                # Remove batch-specific count - let agent query database for accurate total
                print(f"SUGGESTION NODE: Removing batch transaction_count, agent will query database")
                user_preferences.pop('transaction_count', None)

            # Create input for suggestion agent
            input_data = SuggestionAgentInput(
                pattern_insights=pattern_insights,
                budget_thresholds=budget_thresholds,
                user_preferences=user_preferences,
                user_id=user_id
            )

            # Generate suggestions (now async)
            import asyncio
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, create a task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, suggestion_agent.process(input_data))
                        result = future.result()
                else:
                    # No running loop, safe to use run_until_complete
                    result = loop.run_until_complete(suggestion_agent.process(input_data))
            except RuntimeError:
                # No event loop exists, create one
                result = asyncio.run(suggestion_agent.process(input_data))

            # Get all personalized suggestions from agent
            all_suggestions = result.suggestions
            print(f"SUGGESTION: Agent returned {len(all_suggestions)} personalized suggestions")
            for sugg in all_suggestions[:3]:
                print(f"  - {sugg.title} ({sugg.suggestion_type})")

            # Store suggestions in appropriate state fields
            state['budget_recommendations'] = [suggestion.dict() for suggestion in all_suggestions if 'budget' in suggestion.title.lower() or suggestion.suggestion_type in ['budget_adjustment', 'budget_planning']]
            state['spending_suggestions'] = [suggestion.dict() for suggestion in all_suggestions if 'budget' not in suggestion.title.lower() and suggestion.suggestion_type not in ['budget_adjustment', 'budget_planning']]
            state['budget_alerts'] = result.alerts
            state['savings_opportunities'] = result.savings_opportunities
            state['suggestion_confidence'] = result.confidence_score

            print(f"SUGGESTION: Storing in state:")
            print(f"  - budget_recommendations: {len(state.get('budget_recommendations', []))} items")
            print(f"  - spending_suggestions: {len(state.get('spending_suggestions', []))} items")
            print(f"  - savings_opportunities: {len(state.get('savings_opportunities', []))} items")
            print(f"  - suggestion_confidence: {state.get('suggestion_confidence')}")

            print(f"SUGGESTION: Generated {len(all_suggestions)} total suggestions ({len(state['budget_recommendations'])} budget, {len(state['spending_suggestions'])} spending)")

            # Add to processing history
            processing_entry = {
                'stage': 'suggestion',
                'timestamp': datetime.now().isoformat(),
                'action': 'suggestion_generation_completed',
                'data': {
                    'total_suggestions': len(result.suggestions),
                    'budget_recommendations': len(state.get('budget_recommendations', [])),
                    'spending_suggestions': len(state.get('spending_suggestions', [])),
                    'alerts': len(result.alerts),
                    'savings_opportunities': len(result.savings_opportunities),
                    'confidence': state.get('suggestion_confidence', 0.0)
                }
            }
            state['processing_history'].append(processing_entry)

        except Exception as e:
            error_info = {
                'stage': 'suggestion',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
            state['errors'].append(error_info)
            logger.error(f"Suggestion generation failed: {e}")

        return state

    def safety_guard_node(self, state: TransactionProcessingState) -> TransactionProcessingState:
        """
        Safety guard node - performs anomaly detection and security validation
        """
        print(f"SAFETY GUARD: Starting security validation")

        try:
            from ..agents.safety_guard_agent import SafetyGuardAgent

            state['current_stage'] = ProcessingStage.SAFETY_GUARD
            safety_agent = SafetyGuardAgent()

            # Get transactions for security analysis
            transactions = state.get('processed_transactions', [])
            if not transactions:
                # Try preprocessed transactions and convert them
                preprocessed = state.get('preprocessed_transactions', [])
                if preprocessed:
                    transactions = self._convert_to_classified_transactions(preprocessed)
                elif state.get('final_transaction'):
                    transactions = [state['final_transaction']]

            # Always use SafetyGuardAgent for both transactions and baseline security checks
            # The agent handles new user recommendations internally
            from ..agents.safety_guard_agent import SafetyGuardAgentInput

            # Prepare user profile with new user information
            user_profile = state.get('user_profile', {})

            # If no transactions, mark as new user to get default recommendations
            if not transactions:
                user_profile['is_new_user'] = True
                user_profile['has_seen_security_recommendations'] = user_profile.get('has_seen_security_recommendations', False)

            input_data = SafetyGuardAgentInput(
                classified_transactions=transactions if transactions else [],
                user_profile=user_profile
            )

            security_result = safety_agent.process(input_data)

            state['security_alerts'] = [alert.dict() for alert in security_result.security_alerts]
            state['flagged_transactions'] = [tx.dict() for tx in security_result.flagged_transactions] if security_result.flagged_transactions else []
            state['risk_assessment'] = {'risk_score': security_result.risk_score}
            state['safety_confidence'] = 0.9 if transactions else 0.8  # Lower confidence for new users

            print(f"SAFETY GUARD: Found {len(state['security_alerts'])} security alerts (Risk Score: {security_result.risk_score:.2f})")

            # Add to processing history
            processing_entry = {
                'stage': 'safety_guard',
                'timestamp': datetime.now().isoformat(),
                'action': 'security_validation_completed',
                'data': {
                    'alerts_found': len(state.get('security_alerts', [])),
                    'confidence': state.get('safety_confidence', 0.0)
                }
            }
            state['processing_history'].append(processing_entry)

        except Exception as e:
            error_info = {
                'stage': 'safety_guard',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }
            state['errors'].append(error_info)
            logger.error(f"Security validation failed: {e}")

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

            # Save prediction results to database
            try:
                from ..services.prediction_results_service import get_prediction_results_service

                prediction_service = get_prediction_results_service()
                workflow_mode = getattr(state.get('workflow_mode'), 'value', state.get('workflow_mode', 'full_pipeline'))

                prediction_service.save_prediction_result(
                    workflow_id=state.get('workflow_id'),
                    user_id=state.get('user_id', 'default'),
                    workflow_state=dict(state),
                    mode=workflow_mode,
                    status='completed'
                )
                logger.info(f"Saved prediction results to database for workflow {state.get('workflow_id')}")
            except Exception as db_error:
                logger.error(f"Failed to save prediction results to database: {db_error}", exc_info=True)
                # Don't fail the workflow if database save fails

            # Calculate a rough confidence estimate for logging
            ingestion_conf = state.get('ingestion_confidence', 0)
            category_conf = state.get('category_confidence', 0)
            pattern_insights = len(state.get('pattern_insights', []))
            suggestions = len(state.get('budget_recommendations', [])) + len(state.get('spending_suggestions', []))
            alerts = len(state.get('security_alerts', []))

            # Simple confidence estimation
            stage_confidences = [conf for conf in [ingestion_conf, category_conf] if conf > 0]
            if pattern_insights > 0:
                stage_confidences.append(0.75)
            if suggestions > 0:
                stage_confidences.append(0.75)
            if alerts > 0:
                stage_confidences.append(0.8)

            estimated_confidence = sum(stage_confidences) / len(stage_confidences) if stage_confidences else 0

            print(f"FINALIZATION: Workflow completed in {state.get('total_processing_time', 0):.2f}s with {estimated_confidence:.2f} confidence")

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

    def _generate_default_financial_suggestions(self) -> List[Dict[str, Any]]:
        """
        No hardcoded suggestions for new users.
        Frontend will display appropriate onboarding message.
        Real suggestions will be generated after transactions are uploaded.
        """
        return []

    def _convert_to_classified_transactions(self, preprocessed_txns: List[Dict[str, Any]]) -> List:
        """
        Convert preprocessed transaction dicts to ClassifiedTransaction objects
        """
        from ..schemas.transaction_schemas import ClassifiedTransaction, TransactionCategory, TransactionType, PaymentMethod

        classified_transactions = []
        for txn_dict in preprocessed_txns:
            try:
                # Parse date
                date_str = txn_dict.get('date', datetime.now().isoformat())
                if isinstance(date_str, str):
                    try:
                        parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        parsed_date = datetime.now()
                else:
                    parsed_date = date_str if isinstance(date_str, datetime) else datetime.now()

                # Handle payment method - default to CASH for expenses if not valid
                payment_method_str = txn_dict.get('payment_method', 'cash')
                try:
                    payment_method = PaymentMethod(payment_method_str)
                except ValueError:
                    # Default to CASH for invalid payment methods
                    payment_method = PaymentMethod.CASH

                # Create ClassifiedTransaction
                classified_txn = ClassifiedTransaction(
                    id=txn_dict.get('id', f"txn_{uuid.uuid4().hex[:8]}"),
                    date=parsed_date,
                    year=parsed_date.year,
                    month=parsed_date.month,
                    day=parsed_date.day,
                    day_of_week=parsed_date.weekday(),
                    amount=float(txn_dict.get('amount', 0.0)),
                    transaction_type=TransactionType.EXPENSE,  # Assume expense for now
                    payment_method=payment_method,
                    description_cleaned=txn_dict.get('description', ''),
                    merchant_name=txn_dict.get('merchant_name'),
                    merchant_standardized=txn_dict.get('merchant_name'),
                    merchant_category=txn_dict.get('category'),
                    is_merchant_known=bool(txn_dict.get('merchant_name')),
                    predicted_category=TransactionCategory(txn_dict.get('category', 'miscellaneous')),
                    prediction_confidence=0.8,
                    category_probabilities={txn_dict.get('category', 'miscellaneous'): 0.8}
                )
                classified_transactions.append(classified_txn)
            except Exception as e:
                logger.warning(f"Failed to convert transaction {txn_dict.get('id')}: {e}")
                continue

        return classified_transactions

    def _convert_single_transaction_to_classified_object(self, txn_dict: Dict[str, Any], category: str, confidence: float):
        """
        Convert a single preprocessed transaction dict to a ClassifiedTransaction object
        """
        from ..schemas.transaction_schemas import ClassifiedTransaction, TransactionCategory, TransactionType, PaymentMethod

        # Parse date
        date_str = txn_dict.get('date', datetime.now().isoformat())
        if isinstance(date_str, str):
            try:
                parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                parsed_date = datetime.now()
        else:
            parsed_date = date_str if isinstance(date_str, datetime) else datetime.now()

        # Handle payment method
        payment_method_str = txn_dict.get('payment_method', 'cash')
        try:
            payment_method = PaymentMethod(payment_method_str)
        except ValueError:
            payment_method = PaymentMethod.CASH

        # Handle transaction type
        transaction_type_str = txn_dict.get('transaction_type', 'expense')
        try:
            transaction_type = TransactionType(transaction_type_str)
        except ValueError:
            transaction_type = TransactionType.EXPENSE

        # Create ClassifiedTransaction object
        classified_txn = ClassifiedTransaction(
            id=txn_dict.get('id', f"txn_{uuid.uuid4().hex[:8]}"),
            date=parsed_date,
            year=parsed_date.year,
            month=parsed_date.month,
            day=parsed_date.day,
            day_of_week=parsed_date.weekday(),
            amount=float(txn_dict.get('amount', 0.0)),
            transaction_type=transaction_type,  # Use the determined transaction type
            payment_method=payment_method,
            description_cleaned=txn_dict.get('description', ''),
            merchant_name=txn_dict.get('merchant_name', 'Unknown'),
            merchant_standardized=txn_dict.get('merchant_name', 'Unknown'),
            merchant_category=category,
            is_merchant_known=bool(txn_dict.get('merchant_name')),
            predicted_category=TransactionCategory[category],
            prediction_confidence=confidence,
            category_probabilities={category: confidence}
        )

        return classified_txn

    def _classify_transaction(self, description: str, merchant: str) -> tuple[str, float]:
        """
        Enhanced transaction classification based on description and merchant keywords
        Returns (category, confidence) tuple
        """
        # Convert to lowercase for matching
        description_lower = description.lower()
        merchant_lower = merchant.lower()

        # Comprehensive category keywords with weights - mapped to valid TransactionCategory values
        category_keywords = {
            'FOOD_DINING': {
                'keywords': ['restaurant', 'cafe', 'coffee', 'starbucks', 'mcdonalds', 'burger', 'lunch', 'dinner',
                           'pizza', 'sushi', 'taco', 'subway', 'wendys', 'kfc', 'food', 'meal', 'eat', 'dining'],
                'merchant_keywords': ['starbucks', 'mcdonalds', 'subway', 'wendys', 'kfc', 'dominos', 'papa johns',
                                    'chipotle', 'panera', 'dunkin', 'tim hortons', 'cafe', 'restaurant'],
                'weight': 0.9
            },
            'GROCERIES': {
                'keywords': ['grocery', 'supermarket', 'market', 'store', 'whole foods', 'trader joes', 'safeway',
                           'kroger', 'walmart', 'target', 'costco', 'aldi', 'lidl', 'food lion', 'publix'],
                'merchant_keywords': ['whole foods', 'trader joes', 'safeway', 'kroger', 'walmart', 'target',
                                    'costco', 'aldi', 'lidl', 'food lion', 'publix', 'giant', 'stop & shop'],
                'weight': 0.95
            },
            'SHOPPING': {
                'keywords': ['shopping', 'store', 'mall', 'retail', 'amazon', 'ebay', 'etsy', 'clothes', 'clothing',
                           'shoes', 'accessories', 'jewelry', 'department store', 'boutique', 'furniture', 'appliance'],
                'merchant_keywords': ['amazon', 'ebay', 'etsy', 'macy', 'nordstrom', 'bloomingdales', 'saks',
                                    'neiman marcus', 'dillard', 'jcpenney', 'kohls', 'old navy', 'gap', 'h&m',
                                    'ikea', 'bed bath & beyond', 'home depot', 'lowes'],
                'weight': 0.85
            },
            'ENTERTAINMENT': {
                'keywords': ['movie', 'cinema', 'theater', 'netflix', 'spotify', 'hulu', 'disney', 'amazon prime',
                           'hbo', 'showtime', 'entertainment', 'game', 'gaming', 'concert', 'event'],
                'merchant_keywords': ['netflix', 'spotify', 'hulu', 'disney', 'amazon prime', 'hbo', 'showtime',
                                    'steam', 'epic games', 'playstation', 'xbox', 'nintendo'],
                'weight': 0.9
            },
            'TRANSPORTATION': {
                'keywords': ['uber', 'lyft', 'taxi', 'ride', 'bus', 'train', 'subway', 'metro', 'gas', 'fuel',
                           'shell', 'exxon', 'chevron', 'bp', 'mobil', 'parking', 'toll'],
                'merchant_keywords': ['uber', 'lyft', 'shell', 'exxon', 'chevron', 'bp', 'mobil', 'valero',
                                    'speedway', 'sunoco', 'citgo', 'arco'],
                'weight': 0.9
            },
            'UTILITIES': {
                'keywords': ['electric', 'gas', 'water', 'internet', 'phone', 'mobile', 'cable', 'utility',
                           'comcast', 'verizon', 'att', 'tmobile', 'sprint', 'utility bill'],
                'merchant_keywords': ['comcast', 'verizon', 'att', 'tmobile', 'sprint', 'duke energy', 'dominion',
                                    'southern company', 'pge', 'con edison'],
                'weight': 0.95
            },
            'HEALTHCARE': {
                'keywords': ['doctor', 'hospital', 'pharmacy', 'medical', 'dental', 'health', 'clinic', 'medicine',
                           'prescription', 'insurance', 'cvs', 'walgreens', 'rite aid', 'gym', 'fitness', 'spa',
                           'massage', 'yoga', 'pilates', 'workout', 'exercise', 'wellness', 'salon', 'hair', 'nail', 'beauty'],
                'merchant_keywords': ['cvs', 'walgreens', 'rite aid', 'walmart pharmacy', 'kaiser', 'anthem',
                                    'united healthcare', 'aetna', 'cigna', 'planet fitness', 'la fitness', 'equinox',
                                    'great clips', 'supercuts', 'ulta', 'sephora'],
                'weight': 0.9
            },
            'TRAVEL': {
                'keywords': ['hotel', 'airbnb', 'booking', 'travel', 'flight', 'airline', 'vacation', 'trip',
                           'lodging', 'resort', 'motel', 'inn', 'accommodation'],
                'merchant_keywords': ['airbnb', 'booking.com', 'expedia', 'hotels.com', 'marriott', 'hilton',
                                    'hyatt', 'ihg', 'wyndham', 'choice hotels'],
                'weight': 0.9
            },
            'EDUCATION': {
                'keywords': ['school', 'university', 'college', 'education', 'tuition', 'book', 'course', 'class',
                           'training', 'workshop', 'seminar'],
                'merchant_keywords': ['amazon books', 'barnes & noble', 'chegg', 'course hero', 'udemy', 'coursera'],
                'weight': 0.8
            },
            'SUBSCRIPTIONS': {
                'keywords': ['subscription', 'monthly', 'recurring', 'membership', 'club', 'service', 'plan'],
                'merchant_keywords': ['netflix', 'spotify', 'hulu', 'amazon prime', 'disney+', 'hbo max',
                                    'paramount+', 'peacock', 'apple music', 'youtube premium'],
                'weight': 0.95
            },
            'RELIGIOUS_DONATIONS': {
                'keywords': ['donation', 'charity', 'contribution', 'gift', 'nonprofit', 'foundation', 'church',
                           'temple', 'mosque', 'synagogue', 'red cross', 'unicef', 'rotary'],
                'merchant_keywords': ['red cross', 'unicef', 'salvation army', 'goodwill', 'habitat for humanity',
                                    'american cancer society', 'world wildlife fund', 'rotary club'],
                'weight': 0.9
            }
        }

        # Score each category
        category_scores = {}
        for category, rules in category_keywords.items():
            score = 0.0

            # Check description keywords
            for keyword in rules['keywords']:
                if keyword in description_lower:
                    score += rules['weight'] * 0.6  # Description matches are important

            # Check merchant keywords
            for keyword in rules['merchant_keywords']:
                if keyword in merchant_lower:
                    score += rules['weight'] * 0.8  # Merchant matches are very important

            if score > 0:
                category_scores[category] = score

        # Return the highest scoring category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = min(category_scores[best_category] / 1.0, 0.95)  # Cap at 0.95
            return best_category, confidence

        # Default fallback
        return 'MISCELLANEOUS', 0.3

    def _determine_transaction_type(self, description: str, amount: float) -> str:
        """
        Determine transaction type (income/expense) based on description and amount
        """
        description_lower = description.lower()

        # Income patterns - high confidence indicators
        income_patterns = [
            r'\b(salary|wage|payroll|deposit|refund|return|cashback|interest|dividend)\b',
            r'\b(income|payment.*received|credit.*balance|reimbursement)\b',
            r'\b(tax.*refund|bonus|commission|tips|freelance)\b',
            r'\b(social.*security|unemployment|pension|benefits)\b',
            r'\b(gift.*received|inheritance|lottery|settlement)\b',
            r'\b(rental.*income|property.*income|business.*income)\b'
        ]

        # Check for income patterns
        for pattern in income_patterns:
            if re.search(pattern, description_lower, re.IGNORECASE):
                return 'income'

        # Expense patterns
        expense_patterns = [
            r'\b(purchased?|bought|paid|spent|charged|debit|withdrawal)\b',
            r'\b(shopping|store|grocery|restaurant|gas|fuel|utility|bill)\b',
            r'\b(amazon|walmart|target|costco|home.*depot|lowes|ikea)\b',
            r'\b(starbucks|mcdonalds|subway|wendys|chipotle|panera)\b',
            r'\b(netflix|spotify|hulu|electric|internet|phone|insurance)\b',
            r'\b(donation|charity|gift.*given|contribution)\b',
            r'\b(loan.*repayment|installment|emi|mortgage)\b',
            r'\b(medical|hospital|doctor|pharmacy|healthcare)\b',
            r'\b(beauty|salon|cosmetics|spa|haircut)\b',
            r'\b(entertainment|movie|cinema|theater|concert)\b',
            r'\b(furniture|appliance|household|home)\b',
            r'\b(subscription|renewal|membership|service)\b'
        ]

        # Check for expense patterns
        for pattern in expense_patterns:
            if re.search(pattern, description_lower, re.IGNORECASE):
                return 'expense'

        # Amount-based classification: Very large amounts (>10k) are likely income
        if amount > 10000:
            return 'income'

        # Amount-based classification: Small amounts (<100) with expense-like descriptions are expenses
        if amount < 100 and re.search(r'\b(paid|spent|purchased|bought|charged)\b', description_lower, re.IGNORECASE):
            return 'expense'

        # Default based on amount sign
        return 'income' if amount > 0 else 'expense'
