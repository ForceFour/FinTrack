"""
Natural Language Processing Component for Transaction Extraction
Enhanced with LangChain/Groq integration
"""
import re
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import calendar

# LangChain imports with fallback
try:
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatGroq = None
    ChatPromptTemplate = None
    JsonOutputParser = None
    BaseModel = None
    Field = None

logger = logging.getLogger(__name__)

@dataclass
class TransactionExtraction:
    """Data class for extracted transaction information"""
    date: Optional[str] = None
    amount: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    category: Optional[str] = None
    payment_method: Optional[str] = None
    offer_discount: Optional[str] = None
    location: Optional[str] = None
    confidence: float = 0.0

# LangChain Pydantic model (only if available)
if LANGCHAIN_AVAILABLE:
    class LangChainTransactionExtraction(BaseModel):
        """Pydantic model for LangChain output parsing"""
        date: Optional[str] = Field(None, description="Transaction date in YYYY-MM-DD format")
        amount: Optional[str] = Field(None, description="Transaction amount with currency")
        description: Optional[str] = Field(None, description="Transaction description")
        merchant: Optional[str] = Field(None, description="Merchant or store name")
        category: Optional[str] = Field(None, description="Expense category")
        payment_method: Optional[str] = Field(None, description="Payment method used")
        offer_discount: Optional[str] = Field(None, description="Any discount or offer")
        location: Optional[str] = Field(None, description="Transaction location")
        confidence: float = Field(0.0, description="Confidence score 0-1")

class NaturalLanguageProcessor:
    """Process natural language transaction descriptions with LLM support"""
    
    def __init__(self, groq_api_key: Optional[str] = None):
        """Initialize the NL processor with optional LLM support"""
        self.llm = None
        self.extraction_chain = None
        
        # Get API key from parameter or environment
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        
        # Initialize LangChain if available and API key provided
        if LANGCHAIN_AVAILABLE and self.groq_api_key:
            try:
                self.llm = ChatGroq(
                    groq_api_key=self.groq_api_key,
                    model_name="llama-3.3-70b-versatile",
                    temperature=0.1
                )
                self._setup_extraction_chain()
                logger.info("LangChain with Groq initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}")
                self.llm = None
                self.extraction_chain = None
        else:
            self.llm = None
            self.extraction_chain = None
            if not LANGCHAIN_AVAILABLE:
                logger.warning("LangChain not available, using regex extraction only")
            elif not self.groq_api_key:
                logger.warning("No Groq API key found, using regex extraction only")
    
    def _setup_extraction_chain(self):
        """Set up the LangChain extraction chain"""
        
        # Create the prompt template
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial transaction analysis expert. Extract transaction information from natural language text.

Today's date is {today_date}.

Extract the following information:
- date: Convert relative dates (yesterday, today, Monday, etc.) to YYYY-MM-DD format
- amount: Extract monetary amount with currency symbol or description
- description: Clean, descriptive transaction description
- merchant: Store, restaurant, or service provider name
- category: Expense category (food_dining, groceries, transportation, entertainment, shopping, utilities, healthcare, travel, miscellaneous)
- payment_method: How payment was made (credit_card, debit_card, cash, bank_transfer, digital_wallet, check, other)
- offer_discount: Any discount, coupon, or special offer mentioned
- location: Physical location if mentioned
- confidence: Your confidence in the extraction (0.0 to 1.0)

Return ONLY a valid JSON object with these fields. If information is missing or unclear, set the field to null.

Examples:
Input: "I spent $25 at Starbucks yesterday using my credit card"
Output: {{"date": "2024-01-14", "amount": "$25", "description": "Coffee purchase at Starbucks", "merchant": "Starbucks", "category": "food_dining", "payment_method": "credit_card", "offer_discount": null, "location": null, "confidence": 0.9}}

Input: "Grocery shopping $120 at Walmart"
Output: {{"date": null, "amount": "$120", "description": "Grocery shopping", "merchant": "Walmart", "category": "groceries", "payment_method": null, "offer_discount": null, "location": null, "confidence": 0.8}}
"""),
            ("human", "Extract transaction information from: {input_text}")
        ])
        
        # Set up output parser
        output_parser = JsonOutputParser(pydantic_object=LangChainTransactionExtraction)
        
        # Create the chain
        self.extraction_chain = extraction_prompt | self.llm | output_parser
        logger.info("LangChain extraction chain set up successfully")
    
    def extract_with_llm(self, text: str) -> TransactionExtraction:
        """Extract transaction info using LLM"""
        if not self.extraction_chain:
            logger.info("LLM not available, falling back to regex extraction")
            return self.extract_with_regex(text)
        
        try:
            logger.info(f"Processing with LLM: {text[:50]}...")
            
            # Get today's date for relative date processing
            today_date = datetime.now().strftime("%Y-%m-%d")
            
            # Invoke the extraction chain
            result = self.extraction_chain.invoke({
                "input_text": text,
                "today_date": today_date
            })
            
            logger.info(f"LLM extraction successful: {result}")
            
            # Extract confidence and log it prominently
            llm_confidence = result.get("confidence", 0.8)
            print(f"LLM CONFIDENCE: {llm_confidence:.2f} | Input: '{text[:60]}{'...' if len(text) > 60 else ''}' | Method: LLM")
            
            # Convert to our TransactionExtraction format
            return TransactionExtraction(
                date=result.get("date"),
                amount=result.get("amount"),
                description=result.get("description"),
                merchant=result.get("merchant"),
                category=result.get("category"),
                payment_method=result.get("payment_method"),
                offer_discount=result.get("offer_discount"),
                location=result.get("location"),
                confidence=llm_confidence
            )
            
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}, falling back to regex")
            return self.extract_with_regex(text)
    
    def extract_with_regex(self, text: str) -> TransactionExtraction:
        """Fallback extraction using regex patterns"""
        try:
            logger.info(f"🔍 Processing with regex: {text[:50]}...")
            
            # Amount patterns
            amount_patterns = [
                r'[\$₹€£¥]\s*(\d+(?:\.\d{2})?)',
                r'(\d+(?:\.\d{2}))\s*(?:dollars?|bucks?|usd|\$)',
                r'paid\s+(\d+(?:\.\d{2})?)',
                r'spent\s+[\$₹€£¥]?\s*(\d+(?:\.\d{2})?)',
                r'cost\s+[\$₹€£¥]?\s*(\d+(?:\.\d{2})?)'
            ]
            
            # Merchant patterns
            merchant_patterns = [
                r'at\s+([A-Za-z][A-Za-z\s&\'-]+?)(?:\s+(?:store|restaurant|cafe|shop|mall|center|outlet|branch))?(?:\s|$|,|\.|for|using|with)',
                r'from\s+([A-Za-z][A-Za-z\s&\'-]+?)(?:\s+(?:store|restaurant|cafe|shop|mall|center|outlet|branch))?(?:\s|$|,|\.|for|using|with)',
                r'(?:bought|purchased|ordered)\s+(?:from\s+)?([A-Za-z][A-Za-z\s&\'-]+?)(?:\s+(?:store|restaurant|cafe|shop|mall|center|outlet|branch))?(?:\s|$|,|\.|for|using|with)'
            ]
            
            # Category keywords
            category_keywords = {
                'food_dining': ['restaurant', 'cafe', 'coffee', 'dinner', 'lunch', 'breakfast', 'food', 'eat', 'dining', 'pizza', 'burger', 'starbucks', 'mcdonalds'],
                'groceries': ['grocery', 'groceries', 'supermarket', 'walmart', 'target', 'costco', 'kroger', 'safeway', 'market'],
                'transportation': ['gas', 'fuel', 'uber', 'lyft', 'taxi', 'bus', 'train', 'metro', 'parking', 'toll'],
                'shopping': ['shopping', 'clothes', 'clothing', 'shoes', 'amazon', 'ebay', 'mall', 'store'],
                'entertainment': ['movie', 'cinema', 'netflix', 'spotify', 'game', 'entertainment', 'concert', 'theater'],
                'utilities': ['electric', 'electricity', 'water', 'gas bill', 'internet', 'phone', 'cable', 'utility'],
                'healthcare': ['doctor', 'hospital', 'pharmacy', 'medicine', 'medical', 'health', 'dental'],
                'travel': ['hotel', 'flight', 'airline', 'booking', 'travel', 'vacation', 'trip']
            }
            
            # Payment method patterns
            payment_patterns = {
                'credit_card': ['credit card', 'visa', 'mastercard', 'amex', 'discover'],
                'debit_card': ['debit card', 'debit'],
                'cash': ['cash', 'cash payment'],
                'digital_wallet': ['paypal', 'venmo', 'apple pay', 'google pay', 'samsung pay'],
                'bank_transfer': ['bank transfer', 'wire', 'ach'],
                'check': ['check', 'cheque']
            }
            
            text_lower = text.lower()
            
            # Extract amount
            amount = None
            for pattern in amount_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    amount_value = match.group(1)
                    # Add currency symbol if not present
                    if not any(symbol in text for symbol in ['$', '₹', '€', '£', '¥']):
                        amount = f"${amount_value}"
                    else:
                        amount = match.group(0)
                    break
            
            # Extract merchant
            merchant = None
            for pattern in merchant_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    merchant = match.group(1).strip().title()
                    break
            
            # Extract category
            category = 'miscellaneous'  # default
            for cat, keywords in category_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    category = cat
                    break
            
            # Extract payment method
            payment_method = None
            for method, keywords in payment_patterns.items():
                if any(keyword in text_lower for keyword in keywords):
                    payment_method = method
                    break
            
            # Extract date (simplified - just check for relative dates)
            date = None
            if 'yesterday' in text_lower:
                date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            elif 'today' in text_lower or 'this morning' in text_lower or 'this afternoon' in text_lower:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Generate description
            description = text.strip()
            if len(description) > 100:
                description = description[:97] + "..."
            
            # Calculate confidence based on extracted fields
            confidence = 0.0
            if amount:
                confidence += 0.3
            if merchant:
                confidence += 0.3
            if category != 'miscellaneous':
                confidence += 0.2
            if payment_method:
                confidence += 0.1
            if date:
                confidence += 0.1
            
            result = TransactionExtraction(
                date=date,
                amount=amount,
                description=description,
                merchant=merchant,
                category=category,
                payment_method=payment_method,
                offer_discount=None,
                location=None,
                confidence=confidence
            )
            
            # Log confidence prominently for regex extraction
            print(f"REGEX CONFIDENCE: {confidence:.2f} | Input: '{text[:60]}{'...' if len(text) > 60 else ''}' | Method: REGEX")
            logger.info(f"Regex extraction successful: confidence={confidence}")
            return result
            
        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")
            return TransactionExtraction(
                description=text,
                confidence=0.1
            )
    
    def process_input(self, text: str) -> Dict[str, Any]:
        """Main method to process natural language input"""
        try:
            logger.info(f"Starting NL processing for: {text[:50]}...")
            
            # Try LLM first if available, fallback to regex
            if self.extraction_chain:
                extraction = self.extract_with_llm(text)
            else:
                extraction = self.extract_with_regex(text)
            
            # Convert to dictionary format
            result = {
                'date': extraction.date,
                'amount': extraction.amount,
                'description': extraction.description or text,
                'merchant': extraction.merchant,
                'category': extraction.category or 'miscellaneous',
                'payment_method': extraction.payment_method,
                'offer_discount': extraction.offer_discount,
                'location': extraction.location,
                'confidence': extraction.confidence,
                'raw_input': text,
                'extraction_method': 'llm' if self.extraction_chain else 'regex'
            }
            
            logger.info(f"NL processing completed with confidence: {extraction.confidence}")
            
            # Prominent confidence logging for pipeline tracking
            print(f"FINAL CONFIDENCE: {extraction.confidence:.2f} | Extraction Method: {result['extraction_method'].upper()} | Ready for NER Agent")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process input: {e}")
            return {
                'description': text,
                'category': 'miscellaneous',
                'confidence': 0.1,
                'raw_input': text,
                'error': str(e),
                'extraction_method': 'error'
            }
