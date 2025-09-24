"""
Login Page - User authentication
"""

import streamlit as st
import requests
from utils.api_client import get_client, handle_api_error

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

def login_user(username: str, password: str):
    """Authenticate user and store token"""
    try:
        api_client = get_client(use_mock=False)

        # Make login request
        login_data = {
            "username": username,
            "password": password
        }

        response = api_client._make_request('POST', '/api/auth/login', json=login_data)
        result = api_client._handle_response(response)

        success, error_msg = handle_api_error(result)
        if success:
            # Store authentication data in session state
            st.session_state.authenticated = True
            st.session_state.access_token = result['access_token']
            st.session_state.user = result['user']
            st.session_state.api_client = api_client

            # Update API client with token
            api_client.session.headers.update({
                'Authorization': f'Bearer {result["access_token"]}'
            })

            return True, "Login successful!"
        else:
            return False, error_msg

    except Exception as e:
        return False, f"Login failed: {str(e)}"

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def logout_user():
    """Logout user and clear session"""
    # Clear session state
    for key in ['authenticated', 'access_token', 'user', 'api_client']:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()

# Main login interface
if not check_authentication():
    st.title("🔐 Login to FinTrack")
    st.markdown("Please login to access transaction management features")

    # Login form
    with st.form("login_form"):
        st.markdown("### Login Credentials")

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            if username and password:
                with st.spinner("Authenticating..."):
                    success, message = login_user(username, password)

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.error("Please enter both username and password")

    # Test credentials info
    st.markdown("---")
    st.info("""
    **Test Credentials:**
    - Username: `testuser`
    - Password: `testpass123`
    """)

    # Registration info (future feature)
    st.markdown("---")
    st.markdown("**Don't have an account?** Registration coming soon!")

else:
    # User is authenticated - show dashboard
    user = st.session_state.get('user', {})

    st.title("✅ Welcome to FinTrack!")
    st.markdown(f"**Logged in as:** {user.get('full_name', 'User')} ({user.get('username', 'N/A')})")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📤 Upload Transactions", type="primary"):
            st.switch_page("pages/upload_transactions.py")

    with col2:
        if st.button("📊 Dashboard"):
            st.switch_page("pages/dashboard.py")

    with col3:
        if st.button("📈 Analytics"):
            st.switch_page("pages/analytics.py")

    with col4:
        if st.button("🚪 Logout"):
            logout_user()

    st.markdown("---")
    st.markdown("### Quick Actions")

    # Quick stats (placeholder)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Transactions", "0", "0")

    with col2:
        st.metric("This Month Spending", "$0.00", "0%")

    with col3:
        st.metric("Categories", "0", "0")

    # Recent activity placeholder
    st.markdown("### Recent Activity")
    st.info("No recent transactions. Upload some data to get started!")
