"""
Upload Transactions Page - File upload and AI processing
"""

import streamlit as st
import pandas as pd
import io
import json
from datetime import datetime
import requests
import time
from utils.api_client import get_client, test_connection, handle_api_error

st.set_page_config(page_title="Upload Transactions", page_icon="📤", layout="wide")

# Check authentication
def check_authentication():
    return st.session_state.get('authenticated', False)

if not check_authentication():
    st.title("🔐 Authentication Required")
    st.error("Please login to access this page")
    if st.button("Go to Login", type="primary"):
        st.switch_page("pages/login.py")
    st.stop()

# Get authenticated user info
user = st.session_state.get('user', {})
access_token = st.session_state.get('access_token', '')

st.title("Upload & Process Transactions")
st.markdown(f"### AI-Powered Transaction Processing & Analysis")
st.markdown(f"**Logged in as:** {user.get('full_name', 'User')}")

# Logout button in sidebar
with st.sidebar:
    st.markdown(f"**User:** {user.get('username', 'N/A')}")
    if st.button("🚪 Logout"):
        # Clear session
        for key in ['authenticated', 'access_token', 'user', 'api_client']:
            if key in st.session_state:
                del st.session_state[key]
        st.switch_page("pages/login.py")

# API endpoints (pointing to test API for now)
API_BASE_URL = "http://localhost:8000"

def upload_to_api(file_data, file_type):
    """Upload file to FastAPI backend for processing"""
    try:
        # Test API connection first
        api_client = get_client(use_mock=False)
        is_connected, message = test_connection(api_client)

        if not is_connected:
            st.warning(f"API connection failed: {message}. Using mock processing...")
            api_client = get_client(use_mock=True)

        # Upload transactions
        result = api_client.upload_transactions(file_data, file_type)

        # Handle response
        success, error_msg = handle_api_error(result)
        if success:
            return result
        else:
            st.error(f"Upload failed: {error_msg}")
            return {"status": "error", "message": error_msg}

    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return {"status": "error", "message": str(e)}

def save_transactions_to_db(transactions_data):
    """Save processed transactions to database via API"""
    try:
        api_client = get_client(use_mock=False)

        # Set authentication token
        if access_token:
            api_client.set_auth_token(access_token)

        is_connected, message = test_connection(api_client)

        if not is_connected:
            st.warning(f"API connection failed: {message}. Transactions stored locally only.")
            return {"status": "error", "message": "No API connection"}

        # Convert DataFrame records to API format
        transaction_creates = []
        for record in transactions_data:
            # Ensure date is in proper format
            transaction_date = record.get("date")
            if isinstance(transaction_date, pd.Timestamp):
                transaction_date = transaction_date.isoformat()
            elif isinstance(transaction_date, datetime):
                transaction_date = transaction_date.isoformat()

            transaction_create = {
                "amount": float(record.get("amount", 0)),
                "description": str(record.get("description", "")),
                "date": transaction_date,
                "merchant": record.get("merchant"),
                "category": record.get("category"),
                "subcategory": record.get("subcategory"),
                "transaction_type": "debit" if float(record.get("amount", 0)) < 0 else "credit",
                "status": "completed"
            }
            transaction_creates.append(transaction_create)

        # Use batch creation
        result = api_client.batch_create_transactions(transaction_creates)

        success, error_msg = handle_api_error(result)
        if success:
            return {"status": "success", "saved": len(transaction_creates)}
        else:
            return {"status": "error", "message": error_msg}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_csv_file(uploaded_file):
    """Process uploaded CSV file"""
    try:
        df = pd.read_csv(uploaded_file)

        # Basic validation
        required_columns = ['date', 'amount', 'description']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.info("Required columns: date, amount, description")
            return None, None

        # Data cleaning and standardization
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

        # Remove rows with invalid data
        original_count = len(df)
        df = df.dropna(subset=['date', 'amount'])

        if len(df) < original_count:
            st.warning(f"Removed {original_count - len(df)} rows with invalid data")

        # Convert to records for API
        records = df.to_dict('records')

        return df, records
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None, None

def process_bank_statement(uploaded_file, bank_type):
    """Process bank statement files (PDF, OFX, QIF)"""
    try:
        #FIXME: Integrate with actual bank statement parsing library or API
        # Simulate bank statement processing
        st.info(f"Processing {bank_type} bank statement...")
        time.sleep(3)

        # Simulated extracted transactions
        sample_transactions = [
            {
                "date": "2024-01-15",
                "amount": -45.67,
                "description": "STARBUCKS COFFEE",
                "category": "Food & Dining",
                "merchant": "Starbucks"
            },
            {
                "date": "2024-01-14",
                "amount": -120.00,
                "description": "GROCERY STORE PURCHASE",
                "category": "Groceries",
                "merchant": "Walmart"
            },
            {
                "date": "2024-01-13",
                "amount": -35.50,
                "description": "GAS STATION",
                "category": "Transportation",
                "merchant": "Shell"
            }
        ]

        return pd.DataFrame(sample_transactions)
    except Exception as e:
        st.error(f"Error processing bank statement: {str(e)}")
        return None

# File Upload Section
st.subheader("File Upload")

upload_tab1, upload_tab2, upload_tab3 = st.tabs(["CSV/Excel", "Bank Statements", "Mobile Export"])

with upload_tab1:
    st.markdown("#### Upload CSV or Excel Files")
    st.info("**Supported formats:** CSV, XLSX, XLS")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload transaction data in CSV or Excel format"
    )

    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")

        # File info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.2f} KB",
            "File type": uploaded_file.type
        }

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**File Information:**")
            for key, value in file_details.items():
                st.write(f"• {key}: {value}")

        with col2:
            if st.button("Process File", type="primary"):
                with st.spinner("Processing file and saving to database..."):
                    st.write("Processing file...")

                    if uploaded_file.name.endswith('.csv'):
                        df, records = process_csv_file(uploaded_file)
                    else:
                        # Handle Excel files
                        df_raw = pd.read_excel(uploaded_file)
                        # Apply same validation as CSV
                        required_columns = ['date', 'amount', 'description']
                        missing_columns = [col for col in required_columns if col not in df_raw.columns]

                        if missing_columns:
                            st.error(f"Missing required columns: {', '.join(missing_columns)}")
                            st.info("Required columns: date, amount, description")
                            df, records = None, None
                        else:
                            df_raw['date'] = pd.to_datetime(df_raw['date'], errors='coerce')
                            df_raw['amount'] = pd.to_numeric(df_raw['amount'], errors='coerce')
                            df = df_raw.dropna(subset=['date', 'amount'])
                            records = df.to_dict('records')

                    if df is not None and records is not None:
                        # Store in session state
                        st.session_state.transactions = records

                        # Save to database
                        st.write("Saving to database...")
                        save_result = save_transactions_to_db(records)

                        if save_result["status"] == "success":
                            st.success(f"✅ Successfully processed and saved {len(df)} transactions to database!")
                        else:
                            st.warning(f"⚠️ File processed but database save failed: {save_result['message']}")
                            st.info("Transactions are stored locally in this session")

                        # Preview data
                        st.markdown("**Data Preview:**")
                        st.dataframe(df.head(), use_container_width=True)

                        # Show processing results
                        st.balloons()

with upload_tab2:
    st.markdown("#### Bank Statement Import")
    st.info("**Supported formats:** PDF, OFX, QIF, QFX")

    bank_type = st.selectbox(
        "Select your bank",
        ["Chase", "Bank of America", "Wells Fargo", "Citi", "Capital One", "Other"]
    )

    statement_file = st.file_uploader(
        "Upload bank statement",
        type=['pdf', 'ofx', 'qif', 'qfx'],
        help="Upload official bank statements for automatic extraction"
    )

    if statement_file is not None:
        st.success(f"Statement uploaded: {statement_file.name}")

        if st.button("Extract Transactions", type="primary"):
            with st.spinner():
                st.write("Extracting transactions from statement...")
                df = process_bank_statement(statement_file, bank_type)

                if df is not None:
                    st.session_state.transactions = df.to_dict('records')
                    st.success(f"Extracted {len(df)} transactions from {bank_type} statement!")

                    # Preview extracted data
                    st.markdown("**Extracted Transactions:**")
                    st.dataframe(df, use_container_width=True)

with upload_tab3:
    st.markdown("#### Mobile App Export")
    st.info("**Supported apps:** Mint, YNAB, Personal Capital, Quicken")

    app_type = st.selectbox(
        "Select mobile app",
        ["Mint", "YNAB (You Need A Budget)", "Personal Capital", "Quicken", "PocketGuard", "Other"]
    )

    mobile_file = st.file_uploader(
        "Upload app export file",
        type=['csv', 'json', 'xlsx'],
        help="Upload transaction export from mobile financial apps"
    )

    if mobile_file is not None:
        st.success(f"Export uploaded: {mobile_file.name}")

        if st.button("Import from App", type="primary"):
            with st.spinner():
                st.write(f"Importing from {app_type}...")
                if mobile_file.name.endswith('.json'):
                    data = json.load(mobile_file)
                    df = pd.DataFrame(data)
                else:
                    df = pd.read_csv(mobile_file)

                if df is not None:
                    st.session_state.transactions = df.to_dict('records')
                    st.success(f"Imported {len(df)} transactions from {app_type}!")
                    st.dataframe(df.head(), use_container_width=True)

# AI Processing Options
st.subheader("AI Processing Options")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Auto-Categorization")
    enable_categorization = st.checkbox("Enable AI categorization", value=True)

    if enable_categorization:
        confidence_threshold = st.slider(
            "Confidence threshold",
            min_value=0.5,
            max_value=1.0,
            value=0.8,
            step=0.05,
            help="Minimum confidence level for auto-categorization"
        )

        custom_categories = st.text_area(
            "Custom categories (one per line)",
            placeholder="Business Travel\nHome Office\nClient Entertainment",
            help="Add custom categories for your specific needs"
        )

with col2:
    st.markdown("#### Data Enhancement")

    enable_merchant_lookup = st.checkbox("Merchant enrichment", value=True)
    enable_duplicate_detection = st.checkbox("Duplicate detection", value=True)
    enable_anomaly_detection = st.checkbox("Anomaly detection", value=True)
    enable_pattern_analysis = st.checkbox("Pattern analysis", value=True)

# Processing Status
if 'transactions' in st.session_state and st.session_state.transactions:
    st.subheader("Processing Complete")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Transactions Loaded",
            len(st.session_state.transactions),
            delta=len(st.session_state.transactions)
        )

    with col2:
        categorized = sum(1 for t in st.session_state.transactions if t.get('category'))
        st.metric(
            "Categorized",
            categorized,
            delta=f"{(categorized/len(st.session_state.transactions)*100):.1f}%"
        )

    with col3:
        duplicates_found = 3  # Simulated
        st.metric(
            "Duplicates Found",
            duplicates_found,
            delta=duplicates_found
        )

    with col4:
        anomalies_found = 2  # Simulated
        st.metric(
            "Anomalies Detected",
            anomalies_found,
            delta=anomalies_found,
            delta_color="inverse"
        )

    # Action buttons
    st.markdown("#### Next Steps")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("View Dashboard", type="primary"):
            st.switch_page("pages/Dashboard.py")

    with col2:
        if st.button("Analyze Data"):
            st.switch_page("pages/Analytics.py")

    with col3:
        if st.button("Get Suggestions"):
            st.switch_page("pages/Suggestions.py")

# Conversational Transaction Entry
st.subheader("Conversational Transaction Entry")
st.markdown("Enter transaction details naturally by typing them out")

# Chat input and interface
try:
    from components.conversational_entry import (
        conversational_transaction_entry,
        show_conversation_tips,
        conversation_stats
    )

    # Main conversational interface (input box will be at top)
    conversational_transaction_entry()

    # Show tips below the chat
    show_conversation_tips()

    # Show conversation statistics if there's activity
    conversation_stats()

except ImportError:
    st.error("Conversational entry component not found. Please check the components directory.")

# Data Validation Summary
if 'transactions' in st.session_state and st.session_state.transactions:
    st.subheader("Data Validation Summary")

    df = pd.DataFrame(st.session_state.transactions)

    validation_results = {
        "Total Records": len(df),
        "Complete Records": len(df.dropna()),
        "Missing Dates": df['date'].isna().sum() if 'date' in df.columns else 0,
        "Missing Amounts": df['amount'].isna().sum() if 'amount' in df.columns else 0,
        "Missing Descriptions": df['description'].isna().sum() if 'description' in df.columns else 0,
        "Duplicate Records": df.duplicated().sum(),
        "Date Range": f"{df['date'].min()} to {df['date'].max()}" if 'date' in df.columns else "N/A"
    }

    col1, col2 = st.columns(2)

    with col1:
        for key, value in list(validation_results.items())[:4]:
            st.metric(key, value)

    with col2:
        for key, value in list(validation_results.items())[4:]:
            if key == "Date Range":
                st.info(f"**{key}**: {value}")
            else:
                st.metric(key, value)

else:
    # Show sample data format
    st.subheader("Expected Data Format")

    sample_data = {
        "date": ["2024-01-15", "2024-01-14", "2024-01-13"],
        "amount": [-45.67, -120.00, 2500.00],
        "description": ["STARBUCKS COFFEE", "GROCERY STORE", "SALARY DEPOSIT"],
        "category": ["Food & Dining", "Groceries", "Income"],
        "merchant": ["Starbucks", "Walmart", "Employer"]
    }

    sample_df = pd.DataFrame(sample_data)
    st.dataframe(sample_df, use_container_width=True)

    st.markdown("""
    **Required columns:**
    - `date`: Transaction date (YYYY-MM-DD format)
    - `amount`: Transaction amount (negative for expenses, positive for income)
    - `description`: Transaction description or memo

    **Optional columns:**
    - `category`: Transaction category
    - `merchant`: Merchant or payee name
    - `payment_method`: Payment method used
    """)
