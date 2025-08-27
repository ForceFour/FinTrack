"""
Conversation Manager Component - Handles chat state and missing field prompts
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """States in the conversation flow"""
    INITIAL = "initial"
    EXTRACTING = "extracting"
    PROMPTING_MISSING = "prompting_missing"
    CONFIRMING = "confirming"
    COMPLETED = "completed"
    ERROR = "error"


class ConversationManager:
    """
    Manages conversation state for natural language transaction entry
    """
    
    def __init__(self):
        self.state = ConversationState.INITIAL
        self.current_transaction = {}
        self.missing_fields = []
        self.conversation_history = []
        self.required_fields = ['date', 'amount', 'description']
        
        self.field_prompts = {
            'date': "When did this transaction occur? (Please provide the date)",
            'amount': "What was the amount of this transaction? (Please include currency if applicable)",
            'description': "Can you provide more details about what this transaction was for?",
            'merchant': "Where did this transaction take place? (Store/merchant name)",
            'payment_method': "How did you pay for this? (credit card, cash, debit card, etc.)",
            'category': "What category would this transaction fall under? (food_dining, groceries, transportation, etc.)"
        }
    
    def start_conversation(self, initial_input: str) -> Tuple[str, Dict[str, Any]]:
        """Start a new conversation with initial input"""
        self.state = ConversationState.INITIAL
        self.current_transaction = {}
        self.missing_fields = []
        self.conversation_history = [{"user": initial_input, "timestamp": "now"}]
        
        logger.info("Started new conversation for transaction entry")
        return self.process_input(initial_input)
    
    def process_input(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """Process user input based on current state"""
        self.conversation_history.append({"user": user_input, "timestamp": "now"})
        
        if self.state == ConversationState.INITIAL:
            return self._handle_initial_input(user_input)
        elif self.state == ConversationState.PROMPTING_MISSING:
            return self._handle_missing_field_input(user_input)
        elif self.state == ConversationState.CONFIRMING:
            return self._handle_confirmation(user_input)
        else:
            return "I'm not sure how to help with that. Let's start over.", {}
    
    def _handle_initial_input(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """Handle the initial transaction description"""
        # Import here to avoid circular imports
        from .nl_processor import NaturalLanguageProcessor
        
        # Process with NL processor
        nl_processor = NaturalLanguageProcessor()
        extracted_data = nl_processor.process_input(user_input)
        
        self.current_transaction.update(extracted_data)
        self.missing_fields = extracted_data.get('missing_fields', [])
        
        if not self.missing_fields:
            # All required fields found
            self.state = ConversationState.CONFIRMING
            return self._generate_confirmation_message(), self.current_transaction
        else:
            # Some fields missing
            self.state = ConversationState.PROMPTING_MISSING
            return self._prompt_for_missing_field(), {}
    
    def _handle_missing_field_input(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """Handle input for missing fields"""
        if not self.missing_fields:
            self.state = ConversationState.CONFIRMING
            return self._generate_confirmation_message(), self.current_transaction
        
        # Get the current missing field
        current_field = self.missing_fields[0]
        
        # Update the transaction with the provided value
        self.current_transaction[current_field] = user_input.strip()
        
        # Remove this field from missing list
        self.missing_fields.pop(0)
        
        # Check if more fields are missing
        if self.missing_fields:
            return self._prompt_for_missing_field(), {}
        else:
            self.state = ConversationState.CONFIRMING
            return self._generate_confirmation_message(), self.current_transaction
    
    def _handle_confirmation(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """Handle confirmation response"""
        user_input_lower = user_input.lower().strip()
        
        if user_input_lower in ['yes', 'y', 'correct', 'looks good', 'ok', 'okay']:
            self.state = ConversationState.COMPLETED
            return "Great! Your transaction has been recorded.", self.current_transaction
        elif user_input_lower in ['no', 'n', 'incorrect', 'wrong']:
            # Start over
            self.state = ConversationState.INITIAL
            self.current_transaction = {}
            self.missing_fields = []
            return "Let's start over. Please describe your transaction again.", {}
        else:
            return "Please respond with 'yes' to confirm or 'no' to start over.", {}
    
    def _prompt_for_missing_field(self) -> str:
        """Generate prompt for the next missing field"""
        if not self.missing_fields:
            return "All required information collected!"
        
        current_field = self.missing_fields[0]
        prompt = self.field_prompts.get(current_field, f"Please provide {current_field}:")
        
        return f"I need a bit more information. {prompt}"
    
    def _generate_confirmation_message(self) -> str:
        """Generate confirmation message showing extracted data"""
        message = "I've extracted the following information from your transaction:\\n\\n"
        
        # Show extracted fields
        field_display = {
            'date': 'Date',
            'amount': 'Amount',
            'description': 'Description',
            'merchant': 'Merchant',
            'category': 'Category',
            'payment_method': 'Payment Method',
            'offer_discount': 'Discount/Offer'
        }
        
        for field, display_name in field_display.items():
            value = self.current_transaction.get(field, '')
            if value and value.strip():
                message += f"• {display_name}: {value}\\n"
        
        message += "\\nIs this information correct? (Yes/No)"
        return message
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """Get current conversation state"""
        return {
            'state': self.state.value,
            'current_transaction': self.current_transaction,
            'missing_fields': self.missing_fields,
            'conversation_history': self.conversation_history
        }
    
    def reset_conversation(self):
        """Reset conversation to initial state"""
        self.state = ConversationState.INITIAL
        self.current_transaction = {}
        self.missing_fields = []
        self.conversation_history = []
        logger.info("Conversation reset to initial state")
