"""
Natural Language Processor Component - Handles unstructured conversational input
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Try to import LangChain components, fallback if not available
try:
    from langchain_groq import ChatGroq
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import BaseMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain/Groq not available, using fallback extraction only")
    LANGCHAIN_AVAILABLE = False


class TransactionExtraction(BaseModel):
    """Schema for extracted transaction data"""
    date: Optional[str] = None
    amount: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    category: Optional[str] = None
    payment_method: Optional[str] = None
    offer_discount: Optional[str] = None
    location: Optional[str] = None
    confidence: float = 0.0
    missing_fields: List[str] = []


class NLProcessor:
    """
    Component for processing natural language transaction input using LLM
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        self.groq_api_key = groq_api_key
        if groq_api_key and LANGCHAIN_AVAILABLE:
            try:
                self.llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name="llama3-70b-8192",
                    temperature=0.1
                )
                self.extraction_prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are an expert at extracting transaction information from natural language text.
                    
Extract the following fields from the user's transaction description:
- date: Transaction date (if mentioned)
- amount: Transaction amount with currency
- description: What was purchased/transaction description
- merchant: Store/business name
- category: Type of expense (food_dining, groceries, transportation, etc.)
- payment_method: How payment was made (credit_card, cash, debit_card, etc.)
- offer_discount: Any discount or offer mentioned
- location: City/state if mentioned

If a field is not clearly mentioned, return null for that field.
For amount, include currency symbols if present.
For date, try to parse relative dates like "yesterday", "today", "last week".

Return only a JSON object with the extracted fields and a confidence score (0-1).
"""),
                    ("human", "Extract transaction information from: {text}")
                ])
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}")
                self.llm = None
                self.extraction_prompt = None
        else:
            self.llm = None
            self.extraction_prompt = None
            if not LANGCHAIN_AVAILABLE:
                logger.warning("LangChain not available, using regex extraction only")
    
    def extract_with_llm(self, text: str) -> TransactionExtraction:
        """Extract transaction info using LLM"""
        if not self.llm:
            return self.extract_with_regex(text)
        
        try:
            prompt = self.extraction_prompt.format_messages(text=text)
            response = self.llm.invoke(prompt)
            
            # Parse LLM response (assuming it returns JSON)
            import json
            extracted_data = json.loads(response.content)
            
            # Validate and create TransactionExtraction object
            extraction = TransactionExtraction(
                date=extracted_data.get('date'),
                amount=extracted_data.get('amount'),
                description=extracted_data.get('description'),
                merchant=extracted_data.get('merchant'),
                category=extracted_data.get('category'),
                payment_method=extracted_data.get('payment_method'),
                offer_discount=extracted_data.get('offer_discount'),
                location=extracted_data.get('location'),
                confidence=extracted_data.get('confidence', 0.8)
            )
            
            # Identify missing required fields
            required_fields = ['date', 'amount', 'description']
            missing = [field for field in required_fields 
                      if not getattr(extraction, field) or getattr(extraction, field).strip() == '']
            extraction.missing_fields = missing
            
            return extraction
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self.extract_with_regex(text)
    
    def extract_with_regex(self, text: str) -> TransactionExtraction:
        """Fallback extraction using regex patterns"""
        try:
            # Amount patterns
            amount_patterns = [
                r'[\$₹€£¥]\s*(\d+(?:\.\d{2})?)',
                r'(\d+(?:\.\d{2})?)\s*(?:dollars?|rupees?|euros?|pounds?)',
                r'(?:cost|paid|spent|amount)\s*[\$₹€£¥]?\s*(\d+(?:\.\d{2})?)',
                r'(\d+(?:\.\d{2})?)\s*(?:\$|₹|€|£|¥)'
            ]
            
            # Date patterns
            date_patterns = [
                r'(?:today|yesterday)',
                r'(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'(?:last\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                r'(?:last\s+week|this\s+week|next\s+week)'
            ]
            
            # Merchant patterns
            merchant_patterns = [
                r'(?:at|from)\s+([A-Z][a-zA-Z\s&]+?)(?:\s+(?:store|shop|restaurant|cafe))?',
                r'([A-Z][A-Z\s&]+?)(?:\s+STORE|\s+#\d+)',
                r'(Starbucks|McDonald\'s|Walmart|Target|Amazon|Uber|Lyft)',  # Common merchants
            ]
            
            # Payment method patterns
            payment_patterns = [
                r'(?:with|using|via)\s+(credit card|debit card|cash|paypal|venmo|apple pay|google pay)',
                r'(visa|mastercard|amex|american express)',
                r'paid\s+(?:in\s+)?(cash|card)',
            ]
            
            # Discount patterns
            discount_patterns = [
                r'(\d+)%\s*(?:off|discount)',
                r'(?:discount|off)\s*(?:of\s*)?(\d+)%',
                r'save[d]?\s*(\d+)%',
            ]
            
            extraction = TransactionExtraction()
            
            # Extract amount
            for pattern in amount_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extraction.amount = match.group(1)
                    break
            
            # Extract date
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if pattern == r'(?:today|yesterday)':
                        extraction.date = match.group(0)
                    else:
                        extraction.date = match.group(1) if match.lastindex else match.group(0)
                    break
            
            # Extract merchant
            for pattern in merchant_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extraction.merchant = match.group(1).strip()
                    break
            
            # Extract payment method
            for pattern in payment_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extraction.payment_method = match.group(1).lower().replace(' ', '_')
                    break
            
            # Extract discount
            for pattern in discount_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    extraction.offer_discount = f"{match.group(1)}% off"
                    break
            
            # Set description as the full text if no specific description found
            extraction.description = text
            
            # Set confidence based on how many fields were extracted
            fields_found = sum(1 for field in ['date', 'amount', 'merchant', 'payment_method'] 
                             if getattr(extraction, field))
            extraction.confidence = fields_found / 4.0
            
            # Identify missing required fields
            required_fields = ['date', 'amount', 'description']
            missing = [field for field in required_fields 
                      if not getattr(extraction, field) or getattr(extraction, field).strip() == '']
            extraction.missing_fields = missing
            
            logger.info(f"Regex extraction completed with confidence: {extraction.confidence}")
            return extraction
            
        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")
            # Return minimal extraction with original text as description
            return TransactionExtraction(
                description=text,
                confidence=0.1,
                missing_fields=['date', 'amount']
            )
    
    def process_natural_language(self, text: str) -> Dict[str, Any]:
        """Main method to process natural language input"""
        logger.info(f"Processing natural language input: {text[:100]}...")
        
        # Extract information using LLM or fallback
        extraction = self.extract_with_llm(text)
        
        # Convert to standardized format
        transaction = {
            'input_type': 'unstructured',
            'original_text': text,
            'date': extraction.date or '',
            'amount': extraction.amount or '',
            'description': extraction.description or text,
            'merchant': extraction.merchant or '',
            'category': extraction.category or '',
            'payment_method': extraction.payment_method or '',
            'offer_discount': extraction.offer_discount or '',
            'location': extraction.location or '',
            'confidence': extraction.confidence,
            'missing_fields': extraction.missing_fields
        }
        
        logger.info(f"Extracted transaction with confidence: {extraction.confidence}")
        if extraction.missing_fields:
            logger.warning(f"Missing required fields: {extraction.missing_fields}")
        
        return transaction
    
    def normalize_relative_dates(self, date_str: str) -> str:
        """Convert relative dates to actual dates"""
        if not date_str:
            return ''
        
        today = date.today()
        date_str_lower = date_str.lower().strip()
        
        if date_str_lower == 'today':
            return today.strftime('%Y-%m-%d')
        elif date_str_lower == 'yesterday':
            yesterday = date.today().replace(day=today.day-1) if today.day > 1 else today
            return yesterday.strftime('%Y-%m-%d')
        elif 'last week' in date_str_lower:
            last_week = date.today().replace(day=today.day-7) if today.day > 7 else today
            return last_week.strftime('%Y-%m-%d')
        
        return date_str
