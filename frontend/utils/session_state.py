"""
Session State Management - Utilities for managing Streamlit session state
"""

import streamlit as st
from datetime import datetime
import json
import pandas as pd

class SessionManager:
    """Manage Streamlit session state with persistence and validation"""
    
    @staticmethod
    def initialize_session_state():
        """Initialize default session state variables"""
        default_state = {
            # User data
            'user_id': None,
            'user_profile': {},
            
            # Transaction data
            'transactions': [],
            'filtered_transactions': [],
            'transaction_categories': [],
            
            # Budget and goals
            'budgets': {},
            'financial_goals': [],
            'savings_targets': {},
            
            # Settings and preferences
            'user_preferences': {
                'currency': 'USD',
                'date_format': 'YYYY-MM-DD',
                'theme': 'light',
                'notifications_enabled': True
            },
            
            # AI and automation
            'categorization_rules': [],
            'ai_insights': [],
            'fraud_alerts': [],
            
            # UI state
            'current_page': 'dashboard',
            'selected_date_range': None,
            'selected_categories': [],
            'search_query': '',
            
            # Processing state
            'upload_status': 'idle',
            'processing_progress': 0,
            'last_sync': None,
            
            # Security
            'session_start_time': datetime.now(),
            'last_activity': datetime.now(),
            'security_alerts': []
        }
        
        # Initialize only if not already set
        for key, value in default_state.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def update_last_activity():
        """Update the last activity timestamp"""
        st.session_state.last_activity = datetime.now()
    
    @staticmethod
    def check_session_timeout(timeout_minutes=30):
        """Check if session has timed out"""
        if 'last_activity' in st.session_state:
            time_diff = (datetime.now() - st.session_state.last_activity).total_seconds() / 60
            return time_diff > timeout_minutes
        return False
    
    @staticmethod
    def clear_session_data():
        """Clear sensitive session data"""
        sensitive_keys = [
            'transactions', 'budgets', 'financial_goals', 
            'user_profile', 'categorization_rules'
        ]
        
        for key in sensitive_keys:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def save_user_preferences(preferences):
        """Save user preferences to session state"""
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {}
        
        st.session_state.user_preferences.update(preferences)
        st.session_state.last_activity = datetime.now()
    
    @staticmethod
    def get_user_preference(key, default=None):
        """Get a specific user preference"""
        return st.session_state.get('user_preferences', {}).get(key, default)
    
    @staticmethod
    def add_transaction(transaction_data):
        """Add a new transaction to session state"""
        if 'transactions' not in st.session_state:
            st.session_state.transactions = []
        
        # Add timestamp if not present
        if 'created_at' not in transaction_data:
            transaction_data['created_at'] = datetime.now().isoformat()
        
        st.session_state.transactions.append(transaction_data)
        SessionManager.update_last_activity()
    
    @staticmethod
    def update_transaction(transaction_id, updated_data):
        """Update an existing transaction"""
        if 'transactions' in st.session_state:
            for i, transaction in enumerate(st.session_state.transactions):
                if transaction.get('id') == transaction_id:
                    st.session_state.transactions[i].update(updated_data)
                    st.session_state.transactions[i]['updated_at'] = datetime.now().isoformat()
                    break
        
        SessionManager.update_last_activity()
    
    @staticmethod
    def delete_transaction(transaction_id):
        """Delete a transaction from session state"""
        if 'transactions' in st.session_state:
            st.session_state.transactions = [
                t for t in st.session_state.transactions 
                if t.get('id') != transaction_id
            ]
        
        SessionManager.update_last_activity()
    
    @staticmethod
    def get_transactions_df():
        """Get transactions as a pandas DataFrame"""
        if 'transactions' in st.session_state and st.session_state.transactions:
            return pd.DataFrame(st.session_state.transactions)
        return pd.DataFrame()
    
    @staticmethod
    def set_budget(category, amount, period='monthly'):
        """Set budget for a category"""
        if 'budgets' not in st.session_state:
            st.session_state.budgets = {}
        
        st.session_state.budgets[category] = {
            'amount': amount,
            'period': period,
            'created_at': datetime.now().isoformat()
        }
        
        SessionManager.update_last_activity()
    
    @staticmethod
    def get_budget(category):
        """Get budget for a specific category"""
        return st.session_state.get('budgets', {}).get(category, {})
    
    @staticmethod
    def add_financial_goal(goal_data):
        """Add a financial goal"""
        if 'financial_goals' not in st.session_state:
            st.session_state.financial_goals = []
        
        goal_data['id'] = len(st.session_state.financial_goals) + 1
        goal_data['created_at'] = datetime.now().isoformat()
        
        st.session_state.financial_goals.append(goal_data)
        SessionManager.update_last_activity()
    
    @staticmethod
    def update_goal_progress(goal_id, progress_amount):
        """Update progress on a financial goal"""
        if 'financial_goals' in st.session_state:
            for goal in st.session_state.financial_goals:
                if goal.get('id') == goal_id:
                    goal['current_amount'] = progress_amount
                    goal['updated_at'] = datetime.now().isoformat()
                    break
        
        SessionManager.update_last_activity()
    
    @staticmethod
    def add_categorization_rule(rule_data):
        """Add a categorization rule"""
        if 'categorization_rules' not in st.session_state:
            st.session_state.categorization_rules = []
        
        rule_data['id'] = len(st.session_state.categorization_rules) + 1
        rule_data['created_at'] = datetime.now().isoformat()
        
        st.session_state.categorization_rules.append(rule_data)
        SessionManager.update_last_activity()
    
    @staticmethod
    def get_categorization_rules():
        """Get all categorization rules"""
        return st.session_state.get('categorization_rules', [])
    
    @staticmethod
    def add_ai_insight(insight_data):
        """Add an AI-generated insight"""
        if 'ai_insights' not in st.session_state:
            st.session_state.ai_insights = []
        
        insight_data['timestamp'] = datetime.now().isoformat()
        st.session_state.ai_insights.append(insight_data)
        
        # Keep only last 50 insights
        if len(st.session_state.ai_insights) > 50:
            st.session_state.ai_insights = st.session_state.ai_insights[-50:]
        
        SessionManager.update_last_activity()
    
    @staticmethod
    def get_recent_insights(limit=10):
        """Get recent AI insights"""
        insights = st.session_state.get('ai_insights', [])
        return insights[-limit:] if insights else []
    
    @staticmethod
    def add_security_alert(alert_data):
        """Add a security alert"""
        if 'security_alerts' not in st.session_state:
            st.session_state.security_alerts = []
        
        alert_data['timestamp'] = datetime.now().isoformat()
        alert_data['id'] = len(st.session_state.security_alerts) + 1
        
        st.session_state.security_alerts.append(alert_data)
        SessionManager.update_last_activity()
    
    @staticmethod
    def get_active_alerts():
        """Get active security alerts"""
        alerts = st.session_state.get('security_alerts', [])
        return [alert for alert in alerts if not alert.get('dismissed', False)]
    
    @staticmethod
    def dismiss_alert(alert_id):
        """Dismiss a security alert"""
        if 'security_alerts' in st.session_state:
            for alert in st.session_state.security_alerts:
                if alert.get('id') == alert_id:
                    alert['dismissed'] = True
                    alert['dismissed_at'] = datetime.now().isoformat()
                    break
        
        SessionManager.update_last_activity()
    
    @staticmethod
    def export_session_data():
        """Export session data for backup"""
        export_data = {
            'transactions': st.session_state.get('transactions', []),
            'budgets': st.session_state.get('budgets', {}),
            'financial_goals': st.session_state.get('financial_goals', []),
            'user_preferences': st.session_state.get('user_preferences', {}),
            'categorization_rules': st.session_state.get('categorization_rules', []),
            'exported_at': datetime.now().isoformat()
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    @staticmethod
    def import_session_data(data_json):
        """Import session data from backup"""
        try:
            data = json.loads(data_json)
            
            # Validate data structure
            expected_keys = ['transactions', 'budgets', 'financial_goals', 'user_preferences']
            if not all(key in data for key in expected_keys):
                return False, "Invalid data format"
            
            # Import data
            st.session_state.transactions = data.get('transactions', [])
            st.session_state.budgets = data.get('budgets', {})
            st.session_state.financial_goals = data.get('financial_goals', [])
            st.session_state.user_preferences.update(data.get('user_preferences', {}))
            st.session_state.categorization_rules = data.get('categorization_rules', [])
            
            SessionManager.update_last_activity()
            return True, "Data imported successfully"
            
        except json.JSONDecodeError:
            return False, "Invalid JSON format"
        except Exception as e:
            return False, f"Import error: {str(e)}"
    
    @staticmethod
    def get_session_statistics():
        """Get statistics about current session"""
        stats = {
            'session_duration': (datetime.now() - st.session_state.get('session_start_time', datetime.now())).total_seconds() / 60,
            'transactions_count': len(st.session_state.get('transactions', [])),
            'budgets_count': len(st.session_state.get('budgets', {})),
            'goals_count': len(st.session_state.get('financial_goals', [])),
            'rules_count': len(st.session_state.get('categorization_rules', [])),
            'insights_count': len(st.session_state.get('ai_insights', [])),
            'alerts_count': len(SessionManager.get_active_alerts()),
            'last_activity': st.session_state.get('last_activity', datetime.now()).strftime('%H:%M:%S')
        }
        
        return stats
    
    @staticmethod
    def cleanup_old_data(days_old=30):
        """Clean up old data from session state"""
        cutoff_date = datetime.now() - pd.Timedelta(days=days_old)
        
        # Clean old insights
        if 'ai_insights' in st.session_state:
            st.session_state.ai_insights = [
                insight for insight in st.session_state.ai_insights
                if datetime.fromisoformat(insight.get('timestamp', datetime.now().isoformat())) > cutoff_date
            ]
        
        # Clean old alerts
        if 'security_alerts' in st.session_state:
            st.session_state.security_alerts = [
                alert for alert in st.session_state.security_alerts
                if datetime.fromisoformat(alert.get('timestamp', datetime.now().isoformat())) > cutoff_date
            ]
        
        SessionManager.update_last_activity()

class StateValidator:
    """Validate session state data"""
    
    @staticmethod
    def validate_transaction(transaction_data):
        """Validate transaction data structure"""
        required_fields = ['date', 'amount', 'description']
        
        for field in required_fields:
            if field not in transaction_data:
                return False, f"Missing required field: {field}"
        
        # Validate data types
        try:
            pd.to_datetime(transaction_data['date'])
        except:
            return False, "Invalid date format"
        
        try:
            float(transaction_data['amount'])
        except:
            return False, "Invalid amount format"
        
        return True, "Valid transaction"
    
    @staticmethod
    def validate_budget(budget_data):
        """Validate budget data structure"""
        required_fields = ['amount', 'period']
        
        for field in required_fields:
            if field not in budget_data:
                return False, f"Missing required field: {field}"
        
        try:
            amount = float(budget_data['amount'])
            if amount < 0:
                return False, "Budget amount must be positive"
        except:
            return False, "Invalid amount format"
        
        valid_periods = ['weekly', 'monthly', 'quarterly', 'yearly']
        if budget_data['period'] not in valid_periods:
            return False, f"Invalid period. Must be one of: {valid_periods}"
        
        return True, "Valid budget"
    
    @staticmethod
    def validate_goal(goal_data):
        """Validate financial goal data structure"""
        required_fields = ['name', 'target_amount', 'target_date']
        
        for field in required_fields:
            if field not in goal_data:
                return False, f"Missing required field: {field}"
        
        try:
            amount = float(goal_data['target_amount'])
            if amount <= 0:
                return False, "Target amount must be positive"
        except:
            return False, "Invalid target amount format"
        
        try:
            target_date = pd.to_datetime(goal_data['target_date'])
            if target_date.date() <= datetime.now().date():
                return False, "Target date must be in the future"
        except:
            return False, "Invalid target date format"
        
        return True, "Valid goal"

# Convenience functions for easy access
def init_session():
    """Initialize session state"""
    SessionManager.initialize_session_state()

def get_transactions():
    """Get transactions DataFrame"""
    return SessionManager.get_transactions_df()

def add_transaction(transaction_data):
    """Add transaction with validation"""
    is_valid, message = StateValidator.validate_transaction(transaction_data)
    if is_valid:
        SessionManager.add_transaction(transaction_data)
    return is_valid, message

def save_preferences(preferences):
    """Save user preferences"""
    SessionManager.save_user_preferences(preferences)

def get_preference(key, default=None):
    """Get user preference"""
    return SessionManager.get_user_preference(key, default)

def export_data():
    """Export session data"""
    return SessionManager.export_session_data()

def import_data(data_json):
    """Import session data"""
    return SessionManager.import_session_data(data_json)
