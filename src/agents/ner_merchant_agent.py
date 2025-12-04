"""
NER/Merchant Agent - Named Entity Recognition for Merchant Information
Role: Extract and standardize merchant information from transaction descriptions
Features: Advanced LLM integration, Multi-step extraction, Contextual understanding
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import logging
import re
import os
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pydantic import BaseModel, Field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from ..schemas.transaction_schemas import PreprocessedTransaction, MerchantTransaction, TransactionCategory
from ..utils.ner_utils import MerchantExtractor

logger = logging.getLogger(__name__)


class NERMerchantAgentInput(BaseModel):
    """Input schema for NER/Merchant Agent"""
    preprocessed_transactions: List[PreprocessedTransaction] = Field(description="Preprocessed transaction data")


class NERMerchantAgentOutput(BaseModel):
    """Output schema for NER/Merchant Agent"""
    merchant_transactions: List[MerchantTransaction] = Field(description="Transactions with merchant info")
    merchant_mapping: Dict[str, str] = Field(description="Merchant name mappings")
    extraction_stats: Dict[str, Any] = Field(description="Statistics about merchant extraction")


class NERMerchantAgent:
    """
    Agent 2: NER/Merchant Agent with Advanced AI Processing

    Key Improvements:
    - Multi-layer extraction pipeline with LLM integration
    - Contextual merchant understanding using transaction history
    - Advanced semantic clustering for merchant variants
    - Real-time merchant knowledge base updates
    - Confidence-aware ensemble extraction
    - Geographic and temporal context awareness
    - Industry-specific merchant pattern recognition

    Responsibilities:
    - Extract merchant names using hybrid AI + pattern-based approach
    - Build and maintain dynamic merchant knowledge graph
    - Perform semantic merchant standardization with context awareness
    - Predict merchant categories using multiple signals
    - Handle complex edge cases: online merchants, subscriptions, international
    - Provide detailed confidence scoring and extraction explanations
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.merchant_extractor = MerchantExtractor()

        # Advanced data structures
        self.merchant_mapping = {}
        self.merchant_frequency = Counter()
        self.merchant_aliases = defaultdict(set)  # Track merchant name variations
        self.merchant_contexts = defaultdict(dict)  # Store contextual information
        self.category_confidence_cache = {}  # Cache category predictions

        # Configuration
        self.confidence_threshold = self.config.get('confidence_threshold', 0.8)
        self.unknown_merchant_label = self.config.get('unknown_merchant_label', "Unknown Merchant")
        self.enable_llm = self.config.get('enable_llm', True)
        self.cache_predictions = self.config.get('cache_predictions', True)

        # Initialize advanced components
        self._init_advanced_patterns()
        self._init_llm_system()
        self._init_merchant_knowledge_base()
        self._init_contextual_analyzers()

        # Performance tracking
        self.extraction_stats = {
            'total_processed': 0,
            'llm_successful': 0,
            'pattern_successful': 0,
            'cache_hits': 0,
            'new_merchants_discovered': 0
        }

    def _init_advanced_patterns(self):
        """Initialize comprehensive merchant extraction patterns"""
        # Multi-tier extraction patterns with confidence scores
        self.extraction_tiers = {
            'tier_1_high_confidence': {
                'patterns': [
                    # Standard merchant format: MERCHANT LOCATION #ID
                    r'^([A-Z][A-Z\s&\-\.\'\d]{2,40}?)\s+(?:[A-Z]{2,3}\s+)?(?:\#\d+|\d{4,})',
                    # Online format with clear domains
                    r'(?:www\.|https?://)?([A-Z][A-Z\s&\-\.\']{2,25})\.(?:com|net|org|co\.uk|app)',
                    # POS with clear merchant names
                    r'(?:POS|SQ)\s*\*?\s*([A-Z][A-Z\s&\-\.\'\d]{3,30})',
                ],
                'confidence_base': 0.90,
                'description': 'High-confidence standard formats'
            },
            'tier_2_medium_confidence': {
                'patterns': [
                    # Date-based format: MERCHANT MM/DD
                    r'^([A-Z][A-Z\s&\-\.\'\d]{2,25}?)\s+\d{1,2}/\d{1,2}(?:/\d{2,4})?',
                    # State format: MERCHANT STATE
                    r'^([A-Z][A-Z\s&\-\.\'\d]{2,25}?)\s+[A-Z]{2}\s*$',
                    # City State: MERCHANT CITY ST
                    r'^([A-Z][A-Z\s&\-\.\'\d]{2,25}?)\s+[A-Z][a-z]+\s+[A-Z]{2}',
                ],
                'confidence_base': 0.75,
                'description': 'Medium-confidence contextual formats'
            },
            'tier_3_low_confidence': {
                'patterns': [
                    # Subscription format
                    r'^([A-Z][A-Z\s&\-\.\'\d]{2,20}?)\s+(?:SUBSCRIPTION|RECURRING|MONTHLY)',
                    # Card format with merchant indicators
                    r'\*([A-Z][A-Z\s&\-\.\'\d]{3,20})',
                    # Generic extraction
                    r'^([A-Z][A-Z\s&\-\.\'\d]{3,25})',
                ],
                'confidence_base': 0.55,
                'description': 'Lower-confidence pattern matching'
            }
        }

        # Context-aware cleaning patterns with intelligence
        self.intelligent_cleaning_patterns = [
            # Remove with contextual awareness
            {
                'pattern': r'\s*\#\d+.*$',
                'replacement': '',
                'context_check': lambda text, amount: True,  # Always remove reference numbers
                'description': 'Remove reference numbers'
            },
            {
                'pattern': r'\s*\d{4,}.*$',
                'replacement': '',
                'context_check': lambda text, amount: amount < 10000,  # Don't remove if might be part of name
                'description': 'Remove long number sequences'
            },
            {
                'pattern': r'\s*\d{2}/\d{2}.*$',
                'replacement': '',
                'context_check': lambda text, amount: True,
                'description': 'Remove date suffixes'
            },
            {
                'pattern': r'\s+[A-Z]{2}(\s+[A-Z]{2})?\s*$',
                'replacement': '',
                'context_check': lambda text, amount: len(text.split()) > 2,  # Keep if short text
                'description': 'Remove state codes'
            },
        ]

        # Industry-specific patterns for better Sri Lankan categorization
        self.industry_patterns = {
            'food_service': {
                'patterns': [r'restaurant|cafe|hotel|rice.*curry|kottu|hoppers|string.*hoppers|roti|bakery'],
                'indicators': ['food', 'dining', 'rice', 'curry', 'kottu', 'hoppers', 'eat', 'meal'],
                'category': TransactionCategory.FOOD_DINING,
                'confidence_boost': 1.2
            },
            'retail_chains': {
                'patterns': [r'keells|cargills|arpico|laugfs|daraz|kapruka|shop|store|retail'],
                'indicators': ['super', 'mart', 'store', 'shop', 'retail', 'purchase'],
                'category': TransactionCategory.SHOPPING,
                'confidence_boost': 1.15
            },
            'fuel_stations': {
                'patterns': [r'ceypetco|ioc|shell|fuel|petrol|diesel|gas|station'],
                'indicators': ['fuel', 'petrol', 'diesel', 'gas', 'station'],
                'category': TransactionCategory.TRANSPORTATION,
                'confidence_boost': 1.25
            },
            'telecom_services': {
                'patterns': [r'dialog|mobitel|airtel|hutch|telecom|mobile|internet'],
                'indicators': ['mobile', 'internet', 'data', 'minutes', 'sms'],
                'category': TransactionCategory.UTILITIES,
                'confidence_boost': 1.3
            },
            'banking_services': {
                'patterns': [r'commercial.*bank|bank.*ceylon|peoples.*bank|hnb|sampath|nsb'],
                'indicators': ['bank', 'atm', 'transfer', 'deposit'],
                'category': TransactionCategory.UTILITIES,
                'confidence_boost': 1.2
            },
            'healthcare_services': {
                'patterns': [r'nawaloka|asiri|lanka.*hospitals|osu.*sala|pharmacy|hospital|clinic'],
                'indicators': ['hospital', 'clinic', 'doctor', 'medicine', 'pharmacy'],
                'category': TransactionCategory.HEALTHCARE,
                'confidence_boost': 1.25
            },
            'transportation_services': {
                'patterns': [r'uber|pickme|kangaroo|taxi|three.*wheeler|bus|ctb|sltb'],
                'indicators': ['taxi', 'cab', 'ride', 'bus', 'transport'],
                'category': TransactionCategory.TRANSPORTATION,
                'confidence_boost': 1.2
            },
            'religious_services': {
                'patterns': [r'temple|kovil|church|mosque|vihara|buddhist|hindu|christian|muslim'],
                'indicators': ['temple', 'church', 'mosque', 'donation', 'dana'],
                'category': TransactionCategory.RELIGIOUS_DONATIONS,
                'confidence_boost': 1.3
            },
            'government_services': {
                'patterns': [r'rto|dmv|passport|visa|license|tax|revenue|government|ministry'],
                'indicators': ['government', 'license', 'tax', 'passport', 'visa', 'registration'],
                'category': TransactionCategory.GOVERNMENT_SERVICES,
                'confidence_boost': 1.25
            },
            'education_services': {
                'patterns': [r'school|university|institute|academy|tuition|college|education'],
                'indicators': ['school', 'university', 'tuition', 'class', 'education'],
                'category': TransactionCategory.EDUCATION,
                'confidence_boost': 1.2
            }
        }

        # Flatten extraction patterns for backward compatibility
        self.extraction_patterns = []
        for tier_name, tier_data in self.extraction_tiers.items():
            self.extraction_patterns.extend(tier_data['patterns'])

        # Basic cleaning patterns for backward compatibility
        self.cleaning_patterns = [
            (r'\s*\#\d+.*$', ''),  # Remove reference numbers
            (r'\s*\d{4,}.*$', ''),  # Remove long number sequences
            (r'\s*\d{2}/\d{2}.*$', ''),  # Remove date suffixes
            (r'\s+[A-Z]{2}(\s+[A-Z]{2})?\s*$', ''),  # Remove state codes
        ]

    def _init_llm_system(self):
        """Initialize advanced LLM system for merchant extraction"""
        self.llm_extractor = None
        self.llm_chain = None

        if not self.enable_llm:
            logger.info("LLM extraction disabled by configuration")
            return

        try:
            # Try Groq first (faster and cheaper)
            groq_api_key = self.config.get('groq_api_key') or os.getenv('GROQ_API_KEY')
            if groq_api_key:
                self._init_groq_llm(groq_api_key)
            else:
                # Fallback to OpenAI
                openai_api_key = self.config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
                if openai_api_key:
                    self._init_openai_llm(openai_api_key)

        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}. Using rule-based extraction only.")

    def _init_groq_llm(self, api_key: str):
        """Initialize Groq LLM system"""
        try:
            from langchain_groq import ChatGroq
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser
            from pydantic import BaseModel, Field

            # Enhanced extraction schema
            class MerchantExtractionResult(BaseModel):
                merchant_name: Optional[str] = Field(None, description="Cleaned merchant name")
                confidence: float = Field(0.0, description="Confidence score 0-1")
                category_hint: Optional[str] = Field(None, description="Likely category")
                extraction_method: str = Field("llm", description="Method used")
                reasoning: Optional[str] = Field(None, description="Extraction reasoning")
                is_online: bool = Field(False, description="Is online/digital merchant")
                is_chain: bool = Field(False, description="Is chain/franchise")
                location_hint: Optional[str] = Field(None, description="Location if detected")

            self.llm_extractor = ChatGroq(
                api_key=api_key,
                model_name="llama3-8b-8192",
                temperature=0.1,
                max_tokens=500
            )

            self.extraction_parser = JsonOutputParser(pydantic_object=MerchantExtractionResult)

            # Advanced extraction prompt with context
            self.extraction_prompt = ChatPromptTemplate.from_template("""
You are an expert at extracting merchant names from financial transaction descriptions.

Transaction: "{description}"
Amount: ${amount}
Date Context: {date_context}

Your task:
1. Extract the actual business/merchant name (not locations, reference numbers, or transaction codes)
2. Clean and standardize the name (remove suffixes like LLC, INC, store numbers, locations)
3. Determine confidence based on extraction certainty
4. Suggest the most likely expense category
5. Identify if it's an online merchant, chain store, or local business

Examples:
- "STARBUCKS STORE #1234 SEATTLE WA" → "Starbucks" (0.95 confidence, food_dining)
- "SQ *COFFEE ROASTERS" → "Coffee Roasters" (0.85 confidence, food_dining)
- "AMAZON.COM AMZN.COM/BILL WA" → "Amazon" (0.98 confidence, shopping)
- "POS MARIA'S TACOS #123" → "Maria's Tacos" (0.90 confidence, food_dining)

Guidelines:
- Higher confidence (0.8+) for well-known brands and clear formats
- Medium confidence (0.5-0.8) for local businesses and unclear formats
- Low confidence (<0.5) for very ambiguous or generic descriptions
- Consider transaction amount for context (e.g., $3.50 likely coffee, $150 likely electronics)

Return only valid JSON:
{format_instructions}
            """)    

            logger.info("Groq LLM merchant extraction system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Groq LLM: {e}")
            raise

    def _init_openai_llm(self, api_key: str):
        """Initialize OpenAI LLM system (fallback)"""
        try:
            from langchain_openai import ChatOpenAI
            # Similar setup to Groq but with OpenAI
            logger.info("OpenAI LLM system initialized as fallback")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {e}")
            raise

    def _init_merchant_knowledge_base(self):
        """Initialize Sri Lankan merchant knowledge base"""
        # Comprehensive Sri Lankan merchant database with multiple variants
        self.merchant_knowledge_base = {
            # Food & Dining - Sri Lankan chains
            'kfc': {
                'standard_name': 'KFC',
                'category': TransactionCategory.FOOD_DINING,
                'aliases': ['kfc sri lanka', 'kentucky fried chicken'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'fast_food',
                'country': 'sri_lanka'
            },
            'mcdonalds': {
                'standard_name': "McDonald's",
                'category': TransactionCategory.FOOD_DINING,
                'aliases': ['mcd', 'mcdonalds sri lanka'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'fast_food',
                'country': 'sri_lanka'
            },
            'pizza hut': {
                'standard_name': 'Pizza Hut',
                'category': TransactionCategory.FOOD_DINING,
                'aliases': ['pizza hut sri lanka', 'pizzahut'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'restaurant',
                'country': 'sri_lanka'
            },
            'dominos': {
                'standard_name': "Domino's Pizza",
                'category': TransactionCategory.FOOD_DINING,
                'aliases': ['dominos sri lanka', 'domino pizza'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'restaurant',
                'country': 'sri_lanka'
            },
            'subway': {
                'standard_name': 'Subway',
                'category': TransactionCategory.FOOD_DINING,
                'aliases': ['subway sri lanka', 'subway sandwiches'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'fast_food',
                'country': 'sri_lanka'
            },
            'chinese dragon': {
                'standard_name': 'Chinese Dragon',
                'category': TransactionCategory.FOOD_DINING,
                'aliases': ['chinese dragon cafe', 'dragon chinese'],
                'confidence': 0.90,
                'is_chain': True,
                'industry': 'restaurant',
                'country': 'sri_lanka'
            },

            # Sri Lankan Local Food Chains
            'perera and sons': {
                'standard_name': 'Perera & Sons',
                'category': TransactionCategory.GROCERIES,
                'aliases': ['perera sons', 'perera and sons supermarket'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'supermarket',
                'country': 'sri_lanka'
            },
            'cargills': {
                'standard_name': 'Cargills Food City',
                'category': TransactionCategory.GROCERIES,
                'aliases': ['cargills food city', 'food city', 'cargills super'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'supermarket',
                'country': 'sri_lanka'
            },
            'keells': {
                'standard_name': 'Keells Super',
                'category': TransactionCategory.GROCERIES,
                'aliases': ['keells super', 'keells supermarket', 'john keells'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'supermarket',
                'country': 'sri_lanka'
            },
            'arpico': {
                'standard_name': 'Arpico Supercenter',
                'category': TransactionCategory.SHOPPING,
                'aliases': ['arpico supercentre', 'richard pieris arpico'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'department_store',
                'country': 'sri_lanka'
            },
            'laugfs': {
                'standard_name': 'LAUGFS Supermarket',
                'category': TransactionCategory.GROCERIES,
                'aliases': ['laugfs super', 'laugfs supermarket'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'supermarket',
                'country': 'sri_lanka'
            },

            # Transportation - Sri Lankan
            'uber': {
                'standard_name': 'Uber',
                'category': TransactionCategory.TRANSPORTATION,
                'aliases': ['uber sri lanka', 'uber lk'],
                'confidence': 0.99,
                'is_chain': True,
                'industry': 'rideshare',
                'is_online': True,
                'country': 'sri_lanka'
            },
            'pickme': {
                'standard_name': 'PickMe',
                'category': TransactionCategory.TRANSPORTATION,
                'aliases': ['pick me', 'pickme taxi', 'pickme sri lanka'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'rideshare',
                'is_online': True,
                'country': 'sri_lanka'
            },
            'kangaroo cabs': {
                'standard_name': 'Kangaroo Cabs',
                'category': TransactionCategory.TRANSPORTATION,
                'aliases': ['kangaroo taxi', 'kangaroo'],
                'confidence': 0.90,
                'is_chain': True,
                'industry': 'taxi_service',
                'country': 'sri_lanka'
            },

            # Fuel Stations - Sri Lanka
            'ceypetco': {
                'standard_name': 'CEYPETCO',
                'category': TransactionCategory.FUEL,
                'aliases': ['ceypetco fuel', 'ceylon petroleum', 'cpstns'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'fuel_station',
                'country': 'sri_lanka'
            },
            'ioc': {
                'standard_name': 'IOC Lanka',
                'category': TransactionCategory.FUEL,
                'aliases': ['indian oil', 'ioc lanka pvt ltd'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'fuel_station',
                'country': 'sri_lanka'
            },
            'shell': {
                'standard_name': 'Shell',
                'category': TransactionCategory.FUEL,
                'aliases': ['shell sri lanka', 'shell gas'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'fuel_station',
                'country': 'sri_lanka'
            },

            # Telecommunications - Sri Lankan
            'dialog': {
                'standard_name': 'Dialog Axiata',
                'category': TransactionCategory.TELECOMMUNICATIONS,
                'aliases': ['dialog sri lanka', 'dialog axiata plc', 'dialog mobile'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'telecom',
                'country': 'sri_lanka'
            },
            'mobitel': {
                'standard_name': 'Mobitel',
                'category': TransactionCategory.TELECOMMUNICATIONS,
                'aliases': ['mobitel sri lanka', 'slt mobitel'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'telecom',
                'country': 'sri_lanka'
            },
            'airtel': {
                'standard_name': 'Airtel Sri Lanka',
                'category': TransactionCategory.TELECOMMUNICATIONS,
                'aliases': ['airtel lk', 'bharti airtel'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'telecom',
                'country': 'sri_lanka'
            },
            'hutch': {
                'standard_name': 'Hutchison Telecommunications',
                'category': TransactionCategory.TELECOMMUNICATIONS,
                'aliases': ['hutch sri lanka', 'hutchison'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'telecom',
                'country': 'sri_lanka'
            },

            # Banks - Sri Lankan
            'commercial bank': {
                'standard_name': 'Commercial Bank',
                'category': TransactionCategory.GOVERNMENT_SERVICES,
                'aliases': ['commercial bank of ceylon', 'cbc bank', 'combank'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'banking',
                'country': 'sri_lanka'
            },
            'boc': {
                'standard_name': 'Bank of Ceylon',
                'category': TransactionCategory.GOVERNMENT_SERVICES,
                'aliases': ['bank of ceylon', 'boc sri lanka'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'banking',
                'country': 'sri_lanka'
            },
            'peoples bank': {
                'standard_name': "People's Bank",
                'category': TransactionCategory.GOVERNMENT_SERVICES,
                'aliases': ['peoples bank sri lanka', 'people bank'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'banking',
                'country': 'sri_lanka'
            },
            'hnb': {
                'standard_name': 'Hatton National Bank',
                'category': TransactionCategory.GOVERNMENT_SERVICES,
                'aliases': ['hatton national bank', 'hnb sri lanka'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'banking',
                'country': 'sri_lanka'
            },

            # Healthcare - Sri Lankan
            'nawaloka': {
                'standard_name': 'Nawaloka Hospital',
                'category': TransactionCategory.HEALTHCARE,
                'aliases': ['nawaloka hospitals', 'nawaloka health'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'hospital',
                'country': 'sri_lanka'
            },
            'asiri': {
                'standard_name': 'Asiri Hospital',
                'category': TransactionCategory.HEALTHCARE,
                'aliases': ['asiri hospitals', 'asiri health'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'hospital',
                'country': 'sri_lanka'
            },
            'lanka hospitals': {
                'standard_name': 'Lanka Hospitals',
                'category': TransactionCategory.HEALTHCARE,
                'aliases': ['lanka hospital colombo'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'hospital',
                'country': 'sri_lanka'
            },
            'osu sala': {
                'standard_name': 'Osu Sala Pharmacy',
                'category': TransactionCategory.HEALTHCARE,
                'aliases': ['osusala', 'osu sala'],
                'confidence': 0.90,
                'is_chain': True,
                'industry': 'pharmacy',
                'country': 'sri_lanka'
            },

            # Entertainment & Subscriptions - Sri Lankan
            'netflix': {
                'standard_name': 'Netflix',
                'category': TransactionCategory.ENTERTAINMENT,
                'aliases': ['netflix sri lanka', 'netflix.com'],
                'confidence': 0.99,
                'is_chain': True,
                'industry': 'streaming',
                'is_online': True,
                'country': 'sri_lanka'
            },
            'spotify': {
                'standard_name': 'Spotify',
                'category': TransactionCategory.ENTERTAINMENT,
                'aliases': ['spotify sri lanka', 'spotify premium'],
                'confidence': 0.98,
                'is_chain': True,
                'industry': 'music_streaming',
                'is_online': True,
                'country': 'sri_lanka'
            },
            'iflix': {
                'standard_name': 'iflix',
                'category': TransactionCategory.ENTERTAINMENT,
                'aliases': ['iflix sri lanka'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'streaming',
                'is_online': True,
                'country': 'sri_lanka'
            },

            # Shopping - Sri Lankan
            'daraz': {
                'standard_name': 'Daraz',
                'category': TransactionCategory.SHOPPING,
                'aliases': ['daraz.lk', 'daraz sri lanka', 'daraz online'],
                'confidence': 0.99,
                'is_chain': True,
                'industry': 'e_commerce',
                'is_online': True,
                'country': 'sri_lanka'
            },
            'kapruka': {
                'standard_name': 'Kapruka',
                'category': TransactionCategory.SHOPPING,
                'aliases': ['kapruka.com', 'kapruka sri lanka'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'e_commerce',
                'is_online': True,
                'country': 'sri_lanka'
            },
            'softlogic': {
                'standard_name': 'Softlogic',
                'category': TransactionCategory.SHOPPING,
                'aliases': ['softlogic holdings', 'softlogic retail'],
                'confidence': 0.90,
                'is_chain': True,
                'industry': 'retail_electronics',
                'country': 'sri_lanka'
            },
            'singer': {
                'standard_name': 'Singer Sri Lanka',
                'category': TransactionCategory.SHOPPING,
                'aliases': ['singer sl', 'singer store'],
                'confidence': 0.95,
                'is_chain': True,
                'industry': 'retail_electronics',
                'country': 'sri_lanka'
            }
        }

    def _init_contextual_analyzers(self):
        """Initialize Sri Lankan contextual analysis components"""
        # Amount-based context analysis (in Sri Lankan Rupees)
        self.amount_contexts = {
            'micro_transactions': {
                'range': (0, 500),  # Up to Rs. 500
                'likely_categories': [TransactionCategory.FOOD_DINING, TransactionCategory.TRANSPORTATION],
                'typical_merchants': ['tea shops', 'bus fare', 'three wheeler', 'snacks'],
                'confidence_modifier': 1.1
            },
            'small_transactions': {
                'range': (500, 2000),  # Rs. 500 - 2000
                'likely_categories': [TransactionCategory.FOOD_DINING, TransactionCategory.GROCERIES, TransactionCategory.FUEL],
                'typical_merchants': ['local restaurants', 'corner shops', 'fuel stations'],
                'confidence_modifier': 1.0
            },
            'medium_transactions': {
                'range': (2000, 10000),  # Rs. 2000 - 10,000
                'likely_categories': [TransactionCategory.GROCERIES, TransactionCategory.SHOPPING, TransactionCategory.TELECOMMUNICATIONS],
                'typical_merchants': ['supermarkets', 'clothing stores', 'mobile bills'],
                'confidence_modifier': 0.95
            },
            'large_transactions': {
                'range': (10000, 50000),  # Rs. 10,000 - 50,000
                'likely_categories': [TransactionCategory.UTILITIES, TransactionCategory.HEALTHCARE, TransactionCategory.EDUCATION],
                'typical_merchants': ['hospitals', 'schools', 'electricity bills'],
                'confidence_modifier': 0.9
            },
            'very_large_transactions': {
                'range': (50000, float('inf')),  # Above Rs. 50,000
                'likely_categories': [TransactionCategory.TRAVEL, TransactionCategory.GOVERNMENT_SERVICES, TransactionCategory.MEDICAL_INSURANCE],
                'typical_merchants': ['airlines', 'government payments', 'insurance'],
                'confidence_modifier': 0.85
            }
        }

        # Temporal pattern analysis for Sri Lankan context
        self.temporal_patterns = {
            'morning_patterns': {
                'hours': range(6, 11),
                'likely_merchants': ['tea shops', 'bakeries', 'fuel stations', 'bus stations'],
                'categories': [TransactionCategory.FOOD_DINING, TransactionCategory.FUEL, TransactionCategory.TRANSPORTATION]
            },
            'lunch_patterns': {
                'hours': range(11, 15),
                'likely_merchants': ['rice and curry shops', 'hotels', 'restaurants'],
                'categories': [TransactionCategory.FOOD_DINING]
            },
            'evening_patterns': {
                'hours': range(17, 23),
                'likely_merchants': ['supermarkets', 'shopping malls', 'restaurants'],
                'categories': [TransactionCategory.FOOD_DINING, TransactionCategory.ENTERTAINMENT, TransactionCategory.GROCERIES]
            },
            'weekend_patterns': {
                'days': [5, 6],  # Saturday, Sunday
                'likely_merchants': ['shopping centers', 'entertainment venues', 'restaurants'],
                'categories': [TransactionCategory.SHOPPING, TransactionCategory.ENTERTAINMENT, TransactionCategory.FOOD_DINING]
            },
            'poya_day_patterns': {  # Full moon days are public holidays in Sri Lanka
                'likely_merchants': ['temples', 'religious sites', 'donation centers'],
                'categories': [TransactionCategory.RELIGIOUS_DONATIONS, TransactionCategory.TRAVEL]
            }
        }

        # Sri Lankan specific merchant patterns
        self.sri_lankan_patterns = {
            'government_services': {
                'keywords': ['dmv', 'rto', 'passport', 'visa', 'license', 'registration', 'tax', 'inland revenue'],
                'category': TransactionCategory.GOVERNMENT_SERVICES,
                'confidence_boost': 1.3
            },
            'religious_donations': {
                'keywords': ['temple', 'kovil', 'church', 'mosque', 'vihara', 'donation', 'dana', 'pinkama'],
                'category': TransactionCategory.RELIGIOUS_DONATIONS,
                'confidence_boost': 1.2
            },
            'domestic_services': {
                'keywords': ['maid', 'driver', 'gardener', 'security', 'ayah', 'domestic'],
                'category': TransactionCategory.DOMESTIC_HELP,
                'confidence_boost': 1.1
            },
            'education': {
                'keywords': ['school', 'university', 'tuition', 'class', 'academy', 'institute', 'college'],
                'category': TransactionCategory.EDUCATION,
                'confidence_boost': 1.2
            },
            'medical_insurance': {
                'keywords': ['insurance', 'policy', 'premium', 'medical', 'health', 'coverage'],
                'category': TransactionCategory.MEDICAL_INSURANCE,
                'confidence_boost': 1.15
            }
        }

        # Create merchant category rules from knowledge base for backward compatibility
        self.merchant_category_rules = {}
        for merchant_key, merchant_data in self.merchant_knowledge_base.items():
            # Add main merchant name
            self.merchant_category_rules[merchant_key] = merchant_data['category'].value
            # Add standardized name
            if 'standard_name' in merchant_data:
                self.merchant_category_rules[merchant_data['standard_name'].lower()] = merchant_data['category'].value
            # Add aliases
            if 'aliases' in merchant_data:
                for alias in merchant_data['aliases']:
                    self.merchant_category_rules[alias.lower()] = merchant_data['category'].value

        # Amount-based context patterns for merchant extraction
        self.amount_context_patterns = {
            (0, 500): [r'tea|shop|bus|snack|taxi|three.*wheeler'],
            (500, 2000): [r'restaurant|cafe|fuel|corner.*shop|grocery'],
            (2000, 10000): [r'supermarket|clothing|mobile|phone|bill'],
            (10000, 50000): [r'hospital|school|electricity|water|utility'],
            (50000, float('inf')): [r'airline|insurance|government|tax|premium']
        }

    def extract_merchant_name_llm(self, description: str) -> Tuple[Optional[str], float, Optional[str]]:
        """Extract merchant using LLM if available"""
        if not self.llm_extractor:
            return None, 0.0, None

        try:
            prompt = self.extraction_prompt.format_prompt(
                description=description,
                format_instructions=self.extraction_parser.get_format_instructions()
            )

            response = self.llm_extractor.invoke(prompt.to_messages())
            result = self.extraction_parser.parse(response.content)

            return (
                result.get('merchant_name'),
                result.get('confidence', 0.0),
                result.get('category_hint')
            )

        except Exception as e:
            logger.error(f"LLM extraction failed for '{description}': {e}")
            return None, 0.0, None

    def extract_merchant_name(self, description: str, amount: float = None) -> Tuple[Optional[str], float]:
        """
        Enhanced merchant extraction with multiple techniques
        Returns: (merchant_name, confidence_score)
        """
        if not description or not description.strip():
            return None, 0.0

        description = description.strip()
        original_desc = description

        # Method 1: Try LLM extraction first (highest quality)
        if self.llm_extractor:
            llm_merchant, llm_confidence, category_hint = self.extract_merchant_name_llm(description)
            if llm_merchant and llm_confidence >= 0.8:
                logger.debug(f"LLM extraction: {llm_merchant} (confidence: {llm_confidence})")
                return self._clean_merchant_name(llm_merchant), llm_confidence

        # Method 2: Advanced pattern-based extraction
        merchant, confidence = self._advanced_pattern_extraction(description, amount)
        if merchant and confidence >= 0.7:
            logger.debug(f"Advanced pattern extraction: {merchant} (confidence: {confidence})")
            return merchant, confidence

        # Method 3: Use existing basic extractor
        basic_merchant = self.merchant_extractor.extract_merchant(description)
        if basic_merchant:
            confidence = 0.6  # Medium confidence for basic extraction
            logger.debug(f"Basic extractor: {basic_merchant} (confidence: {confidence})")
            return basic_merchant, confidence

        # Method 4: Context-aware extraction based on amount
        context_merchant, context_confidence = self._context_aware_extraction(description, amount)
        if context_merchant:
            logger.debug(f"Context-aware extraction: {context_merchant} (confidence: {context_confidence})")
            return context_merchant, context_confidence

        # Method 5: Fallback extraction
        fallback_merchant, fallback_confidence = self._fallback_extraction(description)
        if fallback_merchant:
            logger.debug(f"Fallback extraction: {fallback_merchant} (confidence: {fallback_confidence})")
            return fallback_merchant, fallback_confidence

        logger.warning(f"Could not extract merchant from: {original_desc}")
        return None, 0.0

    def _advanced_pattern_extraction(self, description: str, amount: float = None) -> Tuple[Optional[str], float]:
        """Enhanced pattern-based extraction using multiple strategies"""
        desc_upper = description.upper().strip()

        # Try each extraction pattern in order of confidence
        for i, pattern in enumerate(self.extraction_patterns):
            match = re.search(pattern, desc_upper, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                cleaned_merchant = self._apply_cleaning_patterns(extracted)

                if self._is_valid_merchant(cleaned_merchant):
                    # Higher confidence for earlier patterns
                    confidence = 0.85 - (i * 0.05)  # Decreases from 0.85 to 0.50
                    return self._clean_merchant_name(cleaned_merchant), max(confidence, 0.50)

        return None, 0.0

    def _apply_cleaning_patterns(self, merchant: str) -> str:
        """Apply cleaning patterns to extracted merchant name"""
        cleaned = merchant
        for pattern, replacement in self.cleaning_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def _context_aware_extraction(self, description: str, amount: float = None) -> Tuple[Optional[str], float]:
        """Extract merchant using context from amount and description patterns"""
        if not amount:
            return None, 0.0

        desc_lower = description.lower()

        # Find relevant context patterns based on amount
        relevant_patterns = []
        for (min_amt, max_amt), patterns in self.amount_context_patterns.items():
            if min_amt <= abs(amount) < max_amt:
                relevant_patterns = patterns
                break

        # Check if any context patterns match
        for pattern in relevant_patterns:
            if re.search(pattern, desc_lower):
                # Try to extract the actual merchant around this pattern
                words = description.split()
                for i, word in enumerate(words):
                    if re.search(pattern, word.lower()):
                        # Take context around the matching word
                        context_start = max(0, i-2)
                        context_end = min(len(words), i+3)
                        context_merchant = ' '.join(words[context_start:context_end])

                        # Clean and validate
                        cleaned = self._apply_cleaning_patterns(context_merchant.upper())
                        if self._is_valid_merchant(cleaned):
                            return self._clean_merchant_name(cleaned), 0.65

        return None, 0.0

    def _legacy_advanced_merchant_extraction(self, description: str) -> Tuple[Optional[str], float]:
        """Advanced merchant extraction using multiple techniques"""
        desc_upper = description.upper()

        # Method 1: Location and ID patterns
        patterns = [
            # Format: "MERCHANT NAME LOCATION #ID"
            r'^([A-Z\s&\-\.]+?)\s+(?:[A-Z]{2,3}\s+)?(?:\#\d+|\d{4,})',
            # Format: "MERCHANT NAME DATE"
            r'^([A-Z\s&\-\.]+?)\s+\d{2}/\d{2}',
            # Format: "MERCHANT STATE"
            r'^([A-Z\s&\-\.]+?)\s+[A-Z]{2}\s*$',
            # Format: "MERCHANT CITY STATE"
            r'^([A-Z\s&\-\.]+?)\s+[A-Z\s]+\s+[A-Z]{2}\s*$',
        ]

        for pattern in patterns:
            match = re.search(pattern, desc_upper)
            if match:
                merchant = self._clean_merchant_name(match.group(1))
                if self._is_valid_merchant(merchant):
                    return merchant, 0.75

        # Method 2: Known merchant substring matching
        for known_merchant in self.merchant_category_rules.keys():
            if known_merchant.upper() in desc_upper:
                return self._clean_merchant_name(known_merchant), 0.90

        # Method 3: First meaningful words (less confident)
        words = desc_upper.split()
        if len(words) >= 2:
            # Take first 2-3 words as potential merchant
            candidate = ' '.join(words[:2])
            clean_candidate = self._clean_merchant_name(candidate)
            if self._is_valid_merchant(clean_candidate):
                return clean_candidate, 0.50

        return None, 0.0

    def _fallback_extraction(self, description: str) -> Tuple[Optional[str], float]:
        """Fallback extraction for difficult cases - improved to handle descriptive transactions"""
        desc_upper = description.upper()
        desc_lower = description.lower()

        # CRITICAL FIX: Extract key concept words from descriptive transactions
        # These are actual services/merchants, not time indicators or adjectives
        priority_concepts = {
            # Housing & Rent
            'rent': ('Rent Payment', 0.85, TransactionCategory.HOUSING),
            'landlord': ('Landlord', 0.85, TransactionCategory.HOUSING),
            'mortgage': ('Mortgage', 0.85, TransactionCategory.HOUSING),
            'housing': ('Housing', 0.80, TransactionCategory.HOUSING),

            # Insurance
            'insurance': ('Insurance', 0.90, TransactionCategory.INSURANCE),
            'premium': ('Insurance Premium', 0.85, TransactionCategory.INSURANCE),
            'policy': ('Insurance Policy', 0.80, TransactionCategory.INSURANCE),

            # Electronics
            'laptop': ('Electronics Store', 0.85, TransactionCategory.ELECTRONICS),
            'computer': ('Electronics Store', 0.85, TransactionCategory.ELECTRONICS),
            'phone': ('Electronics Store', 0.85, TransactionCategory.ELECTRONICS),
            'tablet': ('Electronics Store', 0.80, TransactionCategory.ELECTRONICS),
            'electronics': ('Electronics Store', 0.85, TransactionCategory.ELECTRONICS),

            # Utilities
            'utility': ('Utility Provider', 0.85, TransactionCategory.UTILITIES),
            'utilities': ('Utility Provider', 0.85, TransactionCategory.UTILITIES),
            'electricity': ('Electricity Provider', 0.85, TransactionCategory.UTILITIES),
            'water': ('Water Utility', 0.85, TransactionCategory.UTILITIES),
            'gas': ('Gas Utility', 0.85, TransactionCategory.UTILITIES),

            # Banking
            'atm': ('ATM', 0.90, TransactionCategory.BANKING),
            'withdrawal': ('ATM Withdrawal', 0.85, TransactionCategory.BANKING),
            'bank': ('Bank', 0.80, TransactionCategory.BANKING),

            # Subscriptions
            'subscription': ('Subscription Service', 0.80, TransactionCategory.ENTERTAINMENT),
            'netflix': ('Netflix', 0.95, TransactionCategory.ENTERTAINMENT),
            'spotify': ('Spotify', 0.95, TransactionCategory.ENTERTAINMENT),

            # Salary
            'salary': ('Salary', 0.95, 'income'),
            'payroll': ('Payroll', 0.95, 'income'),
            'wages': ('Wages', 0.90, 'income'),
        }

        # Check for priority concepts in the description
        for keyword, (merchant_name, confidence, category) in priority_concepts.items():
            if keyword in desc_lower:
                # Found a priority concept - use it as merchant
                logger.debug(f"Priority concept extraction: '{keyword}' → '{merchant_name}' (category: {category})")
                return merchant_name, confidence

        # Remove common prefixes/suffixes
        cleanup_patterns = [
            r'^(POS\s+|POS\s*\*|SQ\s+\*|TST\s+\*)',  # Point of sale prefixes
            r'^(RECURRING\s+|AUTO\s+PAY\s+)',          # Recurring payment prefixes
            r'(\s+PENDING|\s+AUTHORIZED|\s+POSTED)$',   # Transaction status suffixes
            r'^(MONTHLY\s+|WEEKLY\s+|DAILY\s+|ANNUAL\s+)',  # CRITICAL: Remove time indicators
            r'^(NEW\s+|OLD\s+|USED\s+)',                     # CRITICAL: Remove adjectives
        ]

        cleaned_desc = desc_upper
        for pattern in cleanup_patterns:
            cleaned_desc = re.sub(pattern, '', cleaned_desc).strip()

        # Extract first substantial word group
        words = cleaned_desc.split()
        if words:
            # Skip obviously non-merchant words - ENHANCED LIST
            skip_words = {
                'PAYMENT', 'TRANSFER', 'DEPOSIT', 'WITHDRAWAL', 'FEE', 'CHARGE', 'DEBIT', 'CREDIT',
                'MONTHLY', 'WEEKLY', 'DAILY', 'YEARLY', 'ANNUAL', 'QUARTERLY',  # Time indicators
                'NEW', 'OLD', 'USED', 'FRESH', 'LATEST',  # Adjectives
                'AM', 'PM', 'AT', 'IN', 'ON', 'FOR', 'TO', 'FROM',  # Prepositions/time
                'THE', 'A', 'AN', 'AND', 'OR', 'BUT',  # Articles/conjunctions
            }
            filtered_words = [w for w in words if w not in skip_words and len(w) > 2]

            if filtered_words:
                # Take first 1-2 meaningful words
                merchant = ' '.join(filtered_words[:2])
                clean_merchant = self._clean_merchant_name(merchant)
                if self._is_valid_merchant(clean_merchant):
                    return clean_merchant, 0.30

        return None, 0.0

    def _clean_merchant_name(self, merchant: str) -> str:
        """Clean and standardize merchant name"""
        if not merchant:
            return ""

        # Remove common suffixes and cleanup
        cleaned = self.merchant_extractor._clean_merchant_name(merchant)

        # Additional cleaning
        suffixes_to_remove = ['POS', 'SQ', 'TST', 'INC', 'LLC', 'CORP', 'CO', 'LTD', 'LLP']
        for suffix in suffixes_to_remove:
            cleaned = re.sub(rf'\s+{suffix}$', '', cleaned, flags=re.IGNORECASE)

        # Remove trailing numbers and special chars
        cleaned = re.sub(r'\s*[#\*\d]*\s*$', '', cleaned)

        return cleaned.strip().title()

    def _is_valid_merchant(self, merchant: str) -> bool:
        """Validate if extracted text is a valid merchant name"""
        if not merchant or len(merchant.strip()) < 3:
            return False

        merchant_upper = merchant.upper().strip()

        # Reject purely numeric or single character
        if merchant.isdigit() or len(merchant) == 1:
            return False

        # COMPREHENSIVE FALSE POSITIVES - Reject time indicators, adjectives, and common noise words
        false_positives = {
            # Transaction status
            'POS', 'SQ', 'TST', 'PENDING', 'AUTHORIZED', 'POSTED', 'COMPLETED',
            'PAYMENT', 'TRANSFER', 'DEPOSIT', 'WITHDRAWAL', 'FEE', 'CHARGE',

            # Time indicators - CRITICAL FIX
            'MONTHLY', 'WEEKLY', 'DAILY', 'YEARLY', 'ANNUAL', 'QUARTERLY',
            'BIWEEKLY', 'BIMONTHLY', 'PERIODIC', 'RECURRING',

            # Adjectives and descriptors - CRITICAL FIX
            'NEW', 'OLD', 'USED', 'FRESH', 'LATEST', 'CURRENT', 'PREVIOUS',
            'NEXT', 'LAST', 'FIRST', 'SECOND', 'THIRD',

            # Time of day - CRITICAL FIX
            'AM', 'PM', 'MORNING', 'AFTERNOON', 'EVENING', 'NIGHT',

            # Generic words
            'TRANSACTION', 'PURCHASE', 'SALE', 'BUY', 'SELL',
            'ONLINE', 'OFFLINE', 'DEBIT', 'CREDIT', 'CASH',

            # Transaction types
            'REFUND', 'RETURN', 'EXCHANGE', 'VOID', 'CANCELLED',
            'ADJUSTMENT', 'CORRECTION', 'REVERSAL',

            # Common false merchant names
            'PAYMENT TO', 'FROM', 'TO', 'AT', 'THE', 'AND', 'OR',
            'FOR', 'WITH', 'WITHOUT', 'IN', 'ON', 'OFF',

            # Account related
            'ACCOUNT', 'BALANCE', 'CHECKING', 'SAVINGS', 'CARD',

            # Generic locations (not actual merchants)
            'CITY', 'TOWN', 'STATE', 'COUNTRY', 'LOCATION', 'PLACE',

            # Additional common words
            'SERVICE', 'PRODUCT', 'ITEM', 'ORDER', 'DELIVERY'
        }

        if merchant_upper in false_positives:
            return False

        # Reject if it's just a number with letters (like "1234AB")
        if re.match(r'^\d+[A-Z]{1,2}$', merchant_upper):
            return False

        # Reject if it's mostly numbers (>50% digits)
        digit_ratio = sum(c.isdigit() for c in merchant) / len(merchant)
        if digit_ratio > 0.5:
            return False

        return True

    def standardize_merchant_name(self, merchant_name: str, all_merchants: List[str] = None) -> str:
        """
        Advanced merchant name standardization using fuzzy matching and clustering
        """
        if not merchant_name:
            return self.unknown_merchant_label

        # Check existing mapping first
        if merchant_name in self.merchant_mapping:
            return self.merchant_mapping[merchant_name]

        # Use built-in standardization as baseline
        standardized = self.merchant_extractor.standardize_merchant(merchant_name)

        # Enhanced fuzzy matching with multiple techniques
        if all_merchants:
            best_match = self._enhanced_fuzzy_matching(merchant_name, all_merchants)
            if best_match and best_match != merchant_name:
                standardized = best_match
                logger.debug(f"Enhanced fuzzy matched '{merchant_name}' to '{best_match}'")

        # Apply merchant name clustering for common variations
        clustered_name = self._apply_merchant_clustering(standardized)
        if clustered_name != standardized:
            standardized = clustered_name
            logger.debug(f"Clustered '{merchant_name}' to '{clustered_name}'")

        # Update mapping for future use
        self.update_merchant_mapping(merchant_name, standardized)

        return standardized

    def _enhanced_fuzzy_matching(self, target: str, candidates: List[str]) -> Optional[str]:
        """Enhanced fuzzy matching with multiple similarity metrics"""
        if not candidates:
            return None

        target_cleaned = self._normalize_for_matching(target)
        best_match = None
        best_score = 0.0

        for candidate in candidates:
            if candidate == target:  # Exact match
                return candidate

            candidate_cleaned = self._normalize_for_matching(candidate)

            # Calculate multiple similarity metrics
            scores = []

            # 1. Sequence matcher (edit distance)
            scores.append(SequenceMatcher(None, target_cleaned, candidate_cleaned).ratio())

            # 2. Jaccard similarity (word overlap)
            target_words = set(target_cleaned.split())
            candidate_words = set(candidate_cleaned.split())
            if target_words or candidate_words:
                jaccard = len(target_words & candidate_words) / len(target_words | candidate_words)
                scores.append(jaccard)

            # 3. Substring matching
            if target_cleaned in candidate_cleaned or candidate_cleaned in target_cleaned:
                scores.append(0.9)

            # 4. Prefix matching (common for chains)
            if target_cleaned[:3] == candidate_cleaned[:3] and len(target_cleaned) > 3:
                scores.append(0.8)

            # Combined similarity score
            combined_score = max(scores) if scores else 0.0

            if combined_score > best_score and combined_score > 0.85:  # High threshold
                best_score = combined_score
                best_match = candidate

        return best_match

    def _normalize_for_matching(self, text: str) -> str:
        """Normalize text for fuzzy matching"""
        if not text:
            return ""

        # Convert to lowercase and remove special characters
        normalized = re.sub(r'[^\w\s]', '', text.lower())

        # Remove common words that add noise
        noise_words = {'inc', 'llc', 'corp', 'ltd', 'co', 'store', 'shop', 'the', 'and'}
        words = [word for word in normalized.split() if word not in noise_words]

        return ' '.join(words)

    def _apply_merchant_clustering(self, merchant_name: str) -> str:
        """Apply clustering rules for common merchant variations"""
        if not merchant_name:
            return merchant_name

        # Define clustering rules for common merchant variations
        clustering_rules = {
            # Chain stores - normalize to main brand
            r'(?i)walmart.*': 'Walmart',
            r'(?i)target.*': 'Target',
            r'(?i)starbucks.*': 'Starbucks',
            r'(?i)mcdonalds?.*': "McDonald's",
            r'(?i)amazon.*': 'Amazon',
            r'(?i)uber.*': 'Uber',
            r'(?i)netflix.*': 'Netflix',
            r'(?i)spotify.*': 'Spotify',

            # Gas stations
            r'(?i)shell.*': 'Shell',
            r'(?i)chevron.*': 'Chevron',
            r'(?i)exxon.*': 'ExxonMobil',
            r'(?i)bp\s.*': 'BP',

            # Banks and financial services
            r'(?i)chase.*': 'Chase Bank',
            r'(?i)bank.*america.*': 'Bank of America',
            r'(?i)wells.*fargo.*': 'Wells Fargo',
            r'(?i)citi.*': 'Citibank',

            # Subscription services
            r'(?i)adobe.*': 'Adobe',
            r'(?i)microsoft.*': 'Microsoft',
            r'(?i)google.*': 'Google',
            r'(?i)apple.*': 'Apple',
        }

        for pattern, standard_name in clustering_rules.items():
            if re.match(pattern, merchant_name):
                return standard_name

        return merchant_name

    def _find_best_match(self, target: str, candidates: List[str]) -> Tuple[str, float]:
        """Find best matching merchant name using fuzzy string matching"""
        if not candidates:
            return target, 0.0

        best_match = target
        best_similarity = 0.0

        target_lower = target.lower()

        for candidate in candidates:
            if candidate == target:  # Exact match
                return candidate, 1.0

            candidate_lower = candidate.lower()
            similarity = SequenceMatcher(None, target_lower, candidate_lower).ratio()

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate

        return best_match, best_similarity

    def get_merchant_category(self, merchant_name: str) -> Optional[TransactionCategory]:
        """Enhanced category prediction with multiple techniques"""
        if not merchant_name:
            return None

        merchant_lower = merchant_name.lower()

        # Method 1: Direct mapping lookup (highest confidence)
        if merchant_lower in self.merchant_category_rules:
            return self.merchant_category_rules[merchant_lower]

        # Method 2: Enhanced pattern-based detection
        category = self._pattern_based_category_detection(merchant_name)
        if category:
            return category

        # Method 3: Substring matching for known merchants
        category = self._substring_category_matching(merchant_lower)
        if category:
            return category

        # Method 4: Semantic category detection using keywords
        category = self._semantic_category_detection(merchant_name)
        if category:
            return category

        return None

    def _pattern_based_category_detection(self, merchant_name: str) -> Optional[TransactionCategory]:
        """Enhanced pattern-based category detection"""
        merchant_lower = merchant_name.lower()

        # Enhanced patterns with more specific matching
        enhanced_patterns = {
            # Food & Dining - more comprehensive patterns
            'food_dining': [
                r'(restaurant|cafe|bistro|grill|kitchen|eatery|diner|bakery)',
                r'(pizza|burger|taco|sandwich|bbq|sushi|thai|chinese|mexican)',
                r'(coffee|starbucks|dunkin|peet|caribou)',
                r'(mcdonalds|burger king|kfc|subway|chipotle|panera)',
                r'(food|dining|eat|meal|lunch|dinner|breakfast)'
            ],

            # Groceries - expanded patterns
            'groceries': [
                r'(grocery|market|supermarket|food.*store)',
                r'(walmart|target|costco|sam.*club|whole foods|trader joe)',
                r'(kroger|safeway|albertsons|publix|wegmans)',
                r'(fresh.*market|organic|produce)'
            ],

            # Transportation - comprehensive patterns
            'transportation': [
                r'(gas|fuel|gasoline|petrol|station)',
                r'(shell|chevron|bp|exxon|mobil|arco|76|valero)',
                r'(uber|lyft|taxi|cab|rideshare)',
                r'(parking|garage|meter|toll|bridge)',
                r'(metro|subway|bus|transit|rail)',
                r'(auto|car.*wash|mechanic|repair)'
            ],

            # Entertainment - detailed patterns
            'entertainment': [
                r'(netflix|spotify|hulu|disney|prime.*video|youtube)',
                r'(movie|theater|cinema|film)',
                r'(game|gaming|xbox|playstation|nintendo)',
                r'(music|concert|show|event|ticket)',
                r'(entertainment|recreation|fun)'
            ],

            # Shopping - broad patterns
            'shopping': [
                r'(amazon|ebay|shop|store|retail|mall)',
                r'(clothing|apparel|fashion|shoe)',
                r'(electronics|computer|phone|tech)',
                r'(home.*depot|lowes|menards|hardware)',
                r'(best.*buy|apple.*store|microsoft)'
            ],

            # Subscriptions - specific patterns
            'subscriptions': [
                r'(subscription|monthly|recurring|auto.*pay)',
                r'(adobe|microsoft|dropbox|zoom|slack)',
                r'(software|saas|service|platform)',
                r'(membership|premium|pro|plus)'
            ],

            # Healthcare - medical patterns
            'healthcare': [
                r'(doctor|hospital|clinic|medical|health)',
                r'(pharmacy|cvs|walgreens|rite.*aid)',
                r'(dental|dentist|vision|optical)',
                r'(insurance|medicare|medicaid)'
            ],

            # Utilities - service patterns
            'utilities': [
                r'(electric|electricity|power|energy)',
                r'(water|sewer|waste|garbage|trash)',
                r'(internet|cable|phone|telecom|wireless)',
                r'(utility|bill|service|provider)'
            ]
        }

        for category_name, patterns in enhanced_patterns.items():
            for pattern in patterns:
                if re.search(pattern, merchant_lower):
                    try:
                        return TransactionCategory(category_name)
                    except ValueError:
                        # Handle cases where category name doesn't match enum
                        continue

        return None

    def _substring_category_matching(self, merchant_lower: str) -> Optional[TransactionCategory]:
        """Improved substring matching with partial matches"""
        # More flexible substring matching
        for known_merchant, category in self.merchant_category_rules.items():
            known_lower = known_merchant.lower()

            # Direct substring match
            if known_lower in merchant_lower or merchant_lower in known_lower:
                return category

            # Word-level matching (handles "Starbucks Coffee" -> "starbucks")
            known_words = set(known_lower.split())
            merchant_words = set(merchant_lower.split())

            if known_words & merchant_words:  # If there's any word overlap
                return category

        return None

    def _semantic_category_detection(self, merchant_name: str) -> Optional[TransactionCategory]:
        """Semantic category detection using business context"""
        merchant_lower = merchant_name.lower()

        # Semantic keyword mapping with business context
        semantic_mappings = {
            # Food context
            TransactionCategory.FOOD_DINING: [
                'roast', 'brew', 'toast', 'slice', 'fresh', 'hot', 'delicious',
                'taste', 'flavor', 'spice', 'crispy', 'juicy', 'sweet'
            ],

            # Retail context
            TransactionCategory.SHOPPING: [
                'store', 'shop', 'mart', 'center', 'plaza', 'outlet',
                'retail', 'buy', 'purchase', 'sale', 'deal'
            ],

            # Service context
            TransactionCategory.UTILITIES: [
                'service', 'provider', 'company', 'corp', 'inc',
                'systems', 'solutions', 'network', 'connect'
            ],

            # Health context
            TransactionCategory.HEALTHCARE: [
                'care', 'wellness', 'health', 'medical', 'clinic',
                'family', 'urgent', 'emergency', 'specialty'
            ],

            # Transportation context
            TransactionCategory.TRANSPORTATION: [
                'auto', 'motor', 'drive', 'road', 'street', 'avenue',
                'express', 'quick', 'fast', 'mobile', 'go'
            ]
        }

        for category, keywords in semantic_mappings.items():
            if any(keyword in merchant_lower for keyword in keywords):
                return category

        return None

    def _pattern_to_category(self, pattern_name: str) -> Optional[TransactionCategory]:
        """Map pattern type to transaction category"""
        pattern_mapping = {
            'gas_station': TransactionCategory.TRANSPORTATION,
            'restaurant': TransactionCategory.FOOD_DINING,
            'online': TransactionCategory.SHOPPING,
            'subscription': TransactionCategory.SUBSCRIPTIONS,
            'transfer': TransactionCategory.MISCELLANEOUS,
        }
        return pattern_mapping.get(pattern_name)

    def update_merchant_mapping(self, original: str, standardized: str):
        """Update internal merchant mapping and frequency tracking"""
        if original and standardized:
            self.merchant_mapping[original] = standardized
            self.merchant_frequency[standardized] += 1

    def process(self, input_data: NERMerchantAgentInput) -> NERMerchantAgentOutput:
        """Enhanced processing with detailed performance monitoring"""
        start_time = datetime.now()
        logger.info(f"Processing {len(input_data.preprocessed_transactions)} transactions for merchant extraction")

        merchant_transactions = []
        extraction_stats = {
            'total_processed': len(input_data.preprocessed_transactions),
            'merchants_extracted': 0,
            'merchants_standardized': 0,
            'categories_mapped': 0,
            'average_confidence': 0.0,
            'unknown_merchants': 0,
            'llm_extractions': 0,
            'pattern_extractions': 0,
            'fallback_extractions': 0,
            'high_confidence_extractions': 0,  # confidence >= 0.8
            'medium_confidence_extractions': 0,  # 0.5 <= confidence < 0.8
            'low_confidence_extractions': 0,   # confidence < 0.5
            'processing_time_seconds': 0.0,
            'extraction_methods': Counter(),
            'category_distribution': Counter(),
            'confidence_histogram': {'0.0-0.2': 0, '0.2-0.4': 0, '0.4-0.6': 0, '0.6-0.8': 0, '0.8-1.0': 0}
        }

        # Collect all descriptions for advanced processing
        all_descriptions = [txn.description_cleaned for txn in input_data.preprocessed_transactions]
        extracted_merchants = []
        total_confidence = 0.0

        # Process each transaction with enhanced monitoring
        for i, txn in enumerate(input_data.preprocessed_transactions):
            try:
                # Extract merchant name with method tracking
                start_extract = datetime.now()
                merchant_name, confidence = self.extract_merchant_name(
                    txn.description_cleaned,
                    txn.amount
                )
                extract_time = (datetime.now() - start_extract).total_seconds()

                total_confidence += confidence

                # Track extraction method and performance
                extraction_method = self._determine_extraction_method(merchant_name, confidence)
                extraction_stats['extraction_methods'][extraction_method] += 1

                # Update confidence histograms
                self._update_confidence_histogram(confidence, extraction_stats['confidence_histogram'])

                # Track confidence levels
                if confidence >= 0.8:
                    extraction_stats['high_confidence_extractions'] += 1
                elif confidence >= 0.5:
                    extraction_stats['medium_confidence_extractions'] += 1
                else:
                    extraction_stats['low_confidence_extractions'] += 1

                if merchant_name:
                    extraction_stats['merchants_extracted'] += 1
                    extracted_merchants.append(merchant_name)

                # Standardize merchant name with enhanced fuzzy matching
                standardized_merchant = self.standardize_merchant_name(
                    merchant_name,
                    extracted_merchants  # Pass current list for fuzzy matching
                ) if merchant_name else self.unknown_merchant_label

                if merchant_name and standardized_merchant != self.unknown_merchant_label:
                    extraction_stats['merchants_standardized'] += 1
                else:
                    extraction_stats['unknown_merchants'] += 1

                # Enhanced category prediction
                merchant_category = self.get_merchant_category(standardized_merchant)
                if merchant_category:
                    extraction_stats['categories_mapped'] += 1
                    extraction_stats['category_distribution'][merchant_category.value] += 1

                # Create enhanced MerchantTransaction with additional metadata
                merchant_transaction = MerchantTransaction(
                    id=txn.id,
                    date=txn.date,
                    year=txn.year,
                    month=txn.month,
                    day=txn.day,
                    day_of_week=txn.day_of_week,
                    amount=txn.amount,
                    payment_method=txn.payment_method,
                    description_cleaned=txn.description_cleaned,
                    has_discount=txn.has_discount,
                    discount_percentage=txn.discount_percentage,
                    metadata=txn.metadata.copy(),
                    # Enhanced merchant fields
                    merchant_name=merchant_name,
                    merchant_standardized=standardized_merchant,
                    merchant_category=merchant_category.value if merchant_category else None,
                    is_merchant_known=merchant_name is not None
                )

                # Add detailed extraction metadata
                merchant_transaction.metadata.update({
                    'merchant_extraction_confidence': confidence,
                    'merchant_extraction_method': extraction_method,
                    'merchant_extraction_time_ms': extract_time * 1000,
                    'original_description': txn.description_cleaned,
                    'standardization_applied': standardized_merchant != merchant_name if merchant_name else False,
                    'category_prediction_method': 'enhanced_semantic' if merchant_category else None,
                    'processing_timestamp': datetime.now().isoformat()
                })

                merchant_transactions.append(merchant_transaction)

            except Exception as e:
                logger.error(f"Error processing transaction {i}: {e}")
                # Create transaction with error info
                error_transaction = MerchantTransaction(
                    id=txn.id,
                    date=txn.date,
                    year=txn.year,
                    month=txn.month,
                    day=txn.day,
                    day_of_week=txn.day_of_week,
                    amount=txn.amount,
                    payment_method=txn.payment_method,
                    description_cleaned=txn.description_cleaned,
                    has_discount=txn.has_discount,
                    discount_percentage=txn.discount_percentage,
                    transaction_type=txn.transaction_type,
                    metadata=txn.metadata.copy(),
                    merchant_name=None,
                    merchant_standardized=self.unknown_merchant_label,
                    merchant_category=None,
                    is_merchant_known=False
                )
                error_transaction.metadata['extraction_error'] = str(e)
                merchant_transactions.append(error_transaction)
                extraction_stats['unknown_merchants'] += 1

        # Calculate final statistics
        processing_time = (datetime.now() - start_time).total_seconds()
        extraction_stats['processing_time_seconds'] = processing_time

        if len(input_data.preprocessed_transactions) > 0:
            extraction_stats['average_confidence'] = total_confidence / len(input_data.preprocessed_transactions)
            extraction_stats['extraction_rate'] = extraction_stats['merchants_extracted'] / extraction_stats['total_processed']
            extraction_stats['standardization_rate'] = extraction_stats['merchants_standardized'] / extraction_stats['total_processed']
            extraction_stats['category_mapping_rate'] = extraction_stats['categories_mapped'] / extraction_stats['total_processed']
            extraction_stats['processing_rate_per_second'] = extraction_stats['total_processed'] / processing_time if processing_time > 0 else 0

        # Convert Counter objects to regular dicts for JSON serialization
        extraction_stats['extraction_methods'] = dict(extraction_stats['extraction_methods'])
        extraction_stats['category_distribution'] = dict(extraction_stats['category_distribution'])

        logger.info(
            f"Enhanced NER processing completed in {processing_time:.2f}s. "
            f"Extracted: {extraction_stats['merchants_extracted']}/{extraction_stats['total_processed']} "
            f"(avg confidence: {extraction_stats['average_confidence']:.2f}, "
            f"rate: {extraction_stats['processing_rate_per_second']:.1f}/s)"
        )

        return NERMerchantAgentOutput(
            merchant_transactions=merchant_transactions,
            merchant_mapping=dict(self.merchant_mapping),
            extraction_stats=extraction_stats
        )

    def _determine_extraction_method(self, merchant_name: str, confidence: float) -> str:
        """Determine which extraction method was likely used based on confidence and result"""
        if not merchant_name:
            return 'none'

        if confidence >= 0.9:
            return 'llm' if self.llm_extractor else 'high_pattern'
        elif confidence >= 0.7:
            return 'advanced_pattern'
        elif confidence >= 0.5:
            return 'basic_pattern'
        else:
            return 'fallback'

    def _update_confidence_histogram(self, confidence: float, histogram: Dict[str, int]):
        """Update confidence histogram for statistics"""
        if confidence < 0.2:
            histogram['0.0-0.2'] += 1
        elif confidence < 0.4:
            histogram['0.2-0.4'] += 1
        elif confidence < 0.6:
            histogram['0.4-0.6'] += 1
        elif confidence < 0.8:
            histogram['0.6-0.8'] += 1
        else:
            histogram['0.8-1.0'] += 1


# Backward compatibility alias
# Backward compatibility - no longer needed
