"""
API Clien    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):   def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None): - Client for communicating with the FastAPI backend
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd

class APIClient:
    """Client for communicating with the FastAPI backend"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })

    def set_auth_token(self, token: str):
        """Set authentication token for API requests"""
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })

    def clear_auth_token(self):
        """Clear authentication token"""
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            # In a real app, you'd want more sophisticated error handling
            print(f"API request failed: {e}")
            raise

    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response and return JSON data"""
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response"}

    # Transaction endpoints
    def upload_transactions(self, file_data: bytes, file_type: str = "csv") -> Dict:
        """Upload transaction file to backend"""
        try:
            files = {'file': file_data}
            data = {'file_type': file_type}

            response = self._make_request(
                'POST',
                '/api/transactions/upload',
                files=files,
                data=data
            )

            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def get_transactions(self, limit: int = 100, offset: int = 0, filters: Optional[Dict] = None) -> Dict:
        """Get transactions from backend"""
        params = {'limit': limit, 'offset': offset}

        if filters:
            params.update(filters)

        try:
            response = self._make_request('GET', '/api/transactions', params=params)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "transactions": []}

    def create_transaction(self, transaction_data: Dict) -> Dict:
        """Create a new transaction"""
        try:
            response = self._make_request('POST', '/api/transactions', json=transaction_data)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def batch_create_transactions(self, transactions: List[Dict]) -> Dict:
        """Create multiple transactions in batch"""
        try:
            response = self._make_request('POST', '/api/transactions/batch', json=transactions)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def update_transaction(self, transaction_id: str, transaction_data: Dict) -> Dict:
        """Update an existing transaction"""
        try:
            response = self._make_request(
                'PUT',
                f'/api/transactions/{transaction_id}',
                json=transaction_data
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    def delete_transaction(self, transaction_id: str) -> Dict:
        """Delete a transaction"""
        try:
            response = self._make_request('DELETE', f'/api/transactions/{transaction_id}')
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    # Categorization endpoints
    def categorize_transaction(self, transaction_data: Dict) -> Dict:
        """Get AI categorization for a transaction"""
        try:
            response = self._make_request('POST', '/api/categorize', json=transaction_data)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "category": "Unknown", "confidence": 0.0}

    def batch_categorize(self, transactions: List[Dict]) -> Dict:
        """Batch categorize multiple transactions"""
        try:
            response = self._make_request('POST', '/api/categorize/batch', json={"transactions": transactions})
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "results": []}

    def get_categorization_rules(self) -> Dict:
        """Get categorization rules"""
        try:
            response = self._make_request('GET', '/api/categorization/rules')
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "rules": []}

    def create_categorization_rule(self, rule_data: Dict) -> Dict:
        """Create a new categorization rule"""
        try:
            response = self._make_request('POST', '/api/categorization/rules', json=rule_data)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    # Analytics endpoints
    def get_spending_analytics(self, period: str = "monthly", filters: Optional[Dict] = None) -> Dict:
        """Get spending analytics"""
        params = {'period': period}
        if filters:
            params.update(filters)

        try:
            response = self._make_request('GET', '/api/analytics/spending', params=params)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "analytics": {}}

    def get_category_breakdown(self, period: str = "monthly") -> Dict:
        """Get category breakdown analytics"""
        try:
            response = self._make_request('GET', f'/api/analytics/categories/{period}')
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "breakdown": {}}

    def get_trends(self, metric: str = "spending", period: str = "daily") -> Dict:
        """Get trend analysis"""
        params = {'metric': metric, 'period': period}

        try:
            response = self._make_request('GET', '/api/analytics/trends', params=params)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "trends": []}

    # Suggestions endpoints
    def get_suggestions(self, suggestion_type: str = "all") -> Dict:
        """Get AI-generated suggestions"""
        try:
            response = self._make_request('GET', f'/api/suggestions/{suggestion_type}')
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "suggestions": []}

    def get_budget_recommendations(self, income: float, current_spending: Dict) -> Dict:
        """Get budget recommendations"""
        data = {
            "income": income,
            "current_spending": current_spending
        }

        try:
            response = self._make_request('POST', '/api/suggestions/budget', json=data)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "recommendations": {}}

    def get_savings_opportunities(self, transactions: List[Dict]) -> Dict:
        """Get savings opportunities"""
        try:
            response = self._make_request('POST', '/api/suggestions/savings', json={"transactions": transactions})
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "opportunities": []}

    # Security endpoints
    def run_fraud_detection(self, transactions: List[Dict]) -> Dict:
        """Run fraud detection on transactions"""
        try:
            response = self._make_request('POST', '/api/security/fraud-detection', json={"transactions": transactions})
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "results": []}

    def get_security_alerts(self) -> Dict:
        """Get security alerts"""
        try:
            response = self._make_request('GET', '/api/security/alerts')
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "alerts": []}

    def report_suspicious_activity(self, activity_data: Dict) -> Dict:
        """Report suspicious activity"""
        try:
            response = self._make_request('POST', '/api/security/report', json=activity_data)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    # User management endpoints
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user"""
        data = {
            "username": username,
            "password": password
        }

        try:
            response = self._make_request('POST', '/api/auth/login', json=data)
            result = self._handle_response(response)

            # Update session with auth token
            if 'access_token' in result:
                self.session.headers.update({
                    'Authorization': f'Bearer {result["access_token"]}'
                })

            return result
        except Exception as e:
            return {"error": str(e), "authenticated": False}

    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh authentication token"""
        data = {"refresh_token": refresh_token}

        try:
            response = self._make_request('POST', '/api/auth/refresh', json=data)
            result = self._handle_response(response)

            # Update session with new token
            if 'access_token' in result:
                self.session.headers.update({
                    'Authorization': f'Bearer {result["access_token"]}'
                })

            return result
        except Exception as e:
            return {"error": str(e), "refreshed": False}

    def logout(self) -> Dict:
        """Logout user"""
        try:
            response = self._make_request('POST', '/api/auth/logout')

            # Clear authorization header
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']

            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "logged_out": True}  # Consider it successful even on error

    def get_user_profile(self) -> Dict:
        """Get user profile"""
        try:
            response = self._make_request('GET', '/api/user/profile')
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "profile": {}}

    def update_user_profile(self, profile_data: Dict) -> Dict:
        """Update user profile"""
        try:
            response = self._make_request('PUT', '/api/user/profile', json=profile_data)
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    # Health check
    def health_check(self) -> Dict:
        """Check API health"""
        try:
            response = self._make_request('GET', '/health')
            return self._handle_response(response)
        except Exception as e:
            return {"error": str(e), "healthy": False}

class MockAPIClient(APIClient):
    """Mock API client for development/testing when backend is not available"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        # Don't call parent __init__ to avoid creating real session
        self.base_url = base_url
        self.api_key = api_key

        # Mock data
        self.mock_transactions = []
        self.mock_rules = []
        self.mock_alerts = []

    def upload_transactions(self, file_data: bytes, file_type: str = "csv") -> Dict:
        """Mock transaction upload"""
        import time
        time.sleep(1)  # Simulate processing time

        return {
            "status": "success",
            "message": "File processed successfully",
            "transactions_processed": 150,
            "new_transactions": 145,
            "duplicates_found": 5
        }

    def get_transactions(self, limit: int = 100, offset: int = 0, filters: Optional[Dict] = None) -> Dict:
        """Mock get transactions"""
        # Return sample transactions
        sample_transactions = [
            {
                "id": "1",
                "date": "2024-01-15",
                "amount": -45.67,
                "description": "STARBUCKS COFFEE",
                "category": "Food & Dining",
                "merchant": "Starbucks",
                "confidence": 0.95
            },
            {
                "id": "2",
                "date": "2024-01-14",
                "amount": -120.00,
                "description": "GROCERY STORE",
                "category": "Groceries",
                "merchant": "Walmart",
                "confidence": 0.88
            }
        ]

        return {
            "transactions": sample_transactions[offset:offset+limit],
            "total": len(sample_transactions),
            "limit": limit,
            "offset": offset
        }

    def categorize_transaction(self, transaction_data: Dict) -> Dict:
        """Mock categorization"""
        # Simple rule-based categorization for demo
        description = transaction_data.get("description", "").lower()

        if any(word in description for word in ["coffee", "restaurant", "food"]):
            return {"category": "Food & Dining", "confidence": 0.95}
        elif any(word in description for word in ["grocery", "supermarket"]):
            return {"category": "Groceries", "confidence": 0.90}
        elif any(word in description for word in ["gas", "fuel", "uber"]):
            return {"category": "Transportation", "confidence": 0.85}
        else:
            return {"category": "Other", "confidence": 0.60}

    def get_spending_analytics(self, period: str = "monthly", filters: Optional[Dict] = None) -> Dict:
        """Mock analytics"""
        return {
            "analytics": {
                "total_spending": 2450.75,
                "average_transaction": 65.50,
                "transaction_count": 37,
                "top_category": "Food & Dining",
                "spending_trend": "increasing",
                "period": period
            }
        }

    def get_suggestions(self, suggestion_type: str = "all") -> Dict:
        """Mock suggestions"""
        suggestions = [
            {
                "type": "savings",
                "title": "Reduce Coffee Spending",
                "description": "You spent $180 on coffee this month. Consider making coffee at home to save $100/month.",
                "potential_savings": 100.0,
                "difficulty": "Easy"
            },
            {
                "type": "budget",
                "title": "Set Dining Budget",
                "description": "Your dining expenses are 35% of your budget. Consider setting a monthly limit of $300.",
                "recommended_amount": 300.0,
                "difficulty": "Medium"
            }
        ]

        return {"suggestions": suggestions}

    def run_fraud_detection(self, transactions: List[Dict]) -> Dict:
        """Mock fraud detection"""
        return {
            "results": {
                "fraud_score": 0.15,
                "suspicious_transactions": 2,
                "risk_level": "Low",
                "anomalies_detected": [
                    {
                        "transaction_id": "123",
                        "reason": "Unusual amount",
                        "risk_score": 0.75
                    }
                ]
            }
        }

    def health_check(self) -> Dict:
        """Mock health check"""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }

# Singleton instance for easy import
api_client = APIClient()
mock_api_client = MockAPIClient()

# Utility functions
def get_client(use_mock: bool = False) -> APIClient:
    """Get API client instance"""
    return mock_api_client if use_mock else api_client

def test_connection(client: APIClient = None) -> Tuple[bool, str]:
    """Test API connection"""
    if client is None:
        client = api_client

    try:
        result = client.health_check()
        if result.get("healthy", False) or result.get("status") == "healthy":
            return True, "API connection successful"
        else:
            return False, result.get("error", "Unknown error")
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def handle_api_error(result: Dict) -> Tuple[bool, str]:
    """Handle API response and extract error information"""
    if "error" in result:
        return False, result["error"]

    if result.get("status") == "failed":
        return False, result.get("message", "Operation failed")

    return True, "Success"
