"""
Conversational Transaction Entry Component - Chat-based transaction input
"""

import streamlit as st
import requests
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import time

def conversational_transaction_entry():
    """Create a conversational chat interface for transaction entry"""
    
    # Initialize session state for conversation
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'conversation_context' not in st.session_state:
        st.session_state.conversation_context = {}
    if 'pending_transaction' not in st.session_state:
        st.session_state.pending_transaction = None
    
    # Chat input - placed at the top for better UX
    user_input = st.chat_input("Type your transaction here... (e.g., 'I spent $25 at Starbucks yesterday')")
    
    # Chat container for message history
    chat_container = st.container()
    
    with chat_container:
        # Display conversation history
        for message in st.session_state.conversation_history:
            if message['type'] == 'user':
                with st.chat_message("user"):
                    st.write(message['content'])
            else:
                with st.chat_message("assistant"):
                    st.write(message['content'])
    
    if user_input:
        # Add user message to history
        st.session_state.conversation_history.append({
            'type': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        # Process the input
        process_conversational_input(user_input)
        
        # Rerun to update the chat
        st.rerun()

def process_conversational_input(user_input: str):
    """Process user input through the conversational transaction service"""
    
    try:
        # Show processing indicator
        with st.spinner("Processing your transaction..."):
            # Call the transaction service API
            result = call_transaction_service_api(user_input)
            
            if result['status'] == 'conversation_ongoing':
                # More information needed - add assistant response
                st.session_state.conversation_history.append({
                    'type': 'assistant',
                    'content': result['response'],
                    'timestamp': datetime.now().isoformat()
                })
                
                # Update conversation context
                st.session_state.conversation_context = result.get('conversation_state', {})
                
            elif result['status'] == 'completed':
                # Transaction completed - show success and details
                success_message = f"✅ {result['response']}\n\n**Transaction Details:**"
                if 'processed_transactions' in result:
                    success_message += f"\n• Processed: {result['processed_transactions']} transaction(s)"
                if 'insights' in result:
                    success_message += f"\n• Insights generated: {result['insights']}"
                if 'suggestions' in result:
                    success_message += f"\n• Suggestions: {result['suggestions']}"
                if 'alerts' in result:
                    success_message += f"\n• Alerts: {result['alerts']}"
                
                st.session_state.conversation_history.append({
                    'type': 'assistant',
                    'content': success_message,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Clear conversation context for new transaction
                st.session_state.conversation_context = {}
                
                # Show completion actions
                show_completion_actions()
                
            elif result['status'] == 'failed':
                # Processing failed
                error_message = f"❌ {result['response']}"
                if result.get('error'):
                    error_message += f"\n\nError details: {result['error']}"
                
                st.session_state.conversation_history.append({
                    'type': 'assistant',
                    'content': error_message,
                    'timestamp': datetime.now().isoformat()
                })
                
    except Exception as e:
        # Handle API errors
        st.session_state.conversation_history.append({
            'type': 'assistant',
            'content': f"❌ Sorry, I encountered an error processing your request: {str(e)}\n\nPlease try again or use the file upload option.",
            'timestamp': datetime.now().isoformat()
        })

def call_transaction_service_api(user_input: str) -> Dict[str, Any]:
    """Call the transaction service API for natural language processing"""
    
    API_BASE_URL = "http://localhost:8000"
    
    try:
        # Try to make HTTP request to FastAPI backend
        response = requests.post(
            f"{API_BASE_URL}/api/transactions/natural-language",
            json={
                "user_input": user_input,
                "user_id": "demo_user",  # In real app, get from session
                "conversation_context": st.session_state.conversation_context
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            # API error, fall back to simulation
            return simulate_transaction_processing(user_input)
            
    except requests.exceptions.RequestException:
        # Backend not available, fall back to simulation
        return simulate_transaction_processing(user_input)
    except Exception as e:
        return {
            'status': 'failed',
            'response': 'Failed to process transaction.',
            'error': str(e)
        }

def simulate_transaction_processing(user_input: str) -> Dict[str, Any]:
    """Simulate transaction processing (placeholder for actual API call)"""
    
    # This is a mock implementation - in reality, this would call your backend
    # For now, we'll simulate different conversation flows
    
    conversation_context = st.session_state.conversation_context
    
    # Simple pattern matching for demo purposes
    if not conversation_context:
        # First message - extract what we can and ask for missing info
        missing_fields = []
        
        # Check for amount
        if not any(char in user_input for char in ['$', '₹', '€', '£']) and not any(word in user_input.lower() for word in ['dollar', 'euro', 'pound', 'rupee']):
            missing_fields.append('amount')
        
        # Check for date
        if not any(word in user_input.lower() for word in ['yesterday', 'today', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
            date_found = False
            for pattern in ['2024', '2025', '/', '-']:
                if pattern in user_input:
                    date_found = True
                    break
            if not date_found:
                missing_fields.append('date')
        
        if missing_fields:
            if 'amount' in missing_fields:
                return {
                    'status': 'conversation_ongoing',
                    'response': 'I need a bit more information. What was the amount of this transaction?',
                    'conversation_state': {
                        'missing_fields': missing_fields,
                        'original_input': user_input,
                        'current_field': 'amount'
                    }
                }
            elif 'date' in missing_fields:
                return {
                    'status': 'conversation_ongoing',
                    'response': 'When did this transaction occur? (Please provide the date)',
                    'conversation_state': {
                        'missing_fields': missing_fields,
                        'original_input': user_input,
                        'current_field': 'date'
                    }
                }
        else:
            # All info available - complete the transaction
            return {
                'status': 'completed',
                'response': 'Transaction processed successfully!',
                'processed_transactions': 1,
                'insights': 2,
                'suggestions': 1,
                'alerts': 0
            }
    
    else:
        # Continuing conversation - we have context
        missing_fields = conversation_context.get('missing_fields', [])
        current_field = conversation_context.get('current_field')
        
        # Remove the current field from missing
        if current_field in missing_fields:
            missing_fields.remove(current_field)
        
        if missing_fields:
            # Still have missing fields
            next_field = missing_fields[0]
            prompts = {
                'date': 'When did this transaction occur? (Please provide the date)',
                'amount': 'What was the amount of this transaction?',
                'merchant': 'Where did this transaction take place? (Store/merchant name)',
                'payment_method': 'How did you pay for this? (credit card, cash, debit card, etc.)'
            }
            
            return {
                'status': 'conversation_ongoing',
                'response': prompts.get(next_field, f'Please provide {next_field}:'),
                'conversation_state': {
                    'missing_fields': missing_fields,
                    'original_input': conversation_context.get('original_input', ''),
                    'current_field': next_field
                }
            }
        else:
            # All fields collected - complete the transaction
            return {
                'status': 'completed',
                'response': 'Perfect! I have all the information I need. Transaction processed successfully!',
                'processed_transactions': 1,
                'insights': 2,
                'suggestions': 1,
                'alerts': 0
            }

def show_completion_actions():
    """Show action buttons after transaction completion"""
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add Another", type="secondary"):
            # Clear conversation for new transaction
            st.session_state.conversation_history = []
            st.session_state.conversation_context = {}
            st.rerun()
    
    with col2:
        if st.button("📊 View Dashboard", type="primary"):
            st.switch_page("pages/dashboard.py")
    
    with col3:
        if st.button("📈 Analytics"):
            st.switch_page("pages/analytics.py")
    
    with col4:
        if st.button("💡 Suggestions"):
            st.switch_page("pages/suggestions.py")

def clear_conversation():
    """Clear the conversation history"""
    st.session_state.conversation_history = []
    st.session_state.conversation_context = {}
    st.session_state.pending_transaction = None

def show_conversation_tips():
    """Show tips for using the conversational interface"""
    
    with st.expander("💡 Tips for Chat-based Entry"):
        st.markdown("""
        **Examples of what you can say:**
        
        ✅ **Good examples:**
        - "I spent $25 at Starbucks yesterday"
        - "Paid $120 for groceries at Walmart today using my credit card"
        - "Gas station charge of $45.50 on Monday"
        - "Coffee shop $4.75 this morning"
        
        ✅ **What I can understand:**
        - **Amounts:** $25, 25 dollars, twenty-five bucks
        - **Dates:** yesterday, today, Monday, 01/15/2024
        - **Places:** Starbucks, grocery store, gas station
        - **Payment:** credit card, cash, debit, Apple Pay
        
        ℹ️ **Don't worry if you forget something** - I'll ask for any missing details!
        """)

def conversation_stats():
    """Show conversation statistics"""
    
    if st.session_state.conversation_history:
        total_messages = len(st.session_state.conversation_history)
        user_messages = len([m for m in st.session_state.conversation_history if m['type'] == 'user'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Messages", total_messages)
        with col2:
            st.metric("Your Inputs", user_messages)
        with col3:
            if st.button("🗑️ Clear Chat"):
                clear_conversation()
                st.rerun()
