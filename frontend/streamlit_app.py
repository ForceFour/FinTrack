"""
Agentic Expense Tracker - Main Streamlit Application
Multi-agent AI expense tracking system with real-time processing
"""

import streamlit as st
import asyncio
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any
import time

# Configure page
st.set_page_config(
    page_title="Agentic Expense Tracker",
    page_icon="", #REVIEW - add icon
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import API client
try:
    from utils.api_client import ExpenseTrackerAPI
    from components.charts import create_expense_chart, create_agent_status_chart
    from components.data_display import display_transaction_table, display_suggestions
    from components.widgets import agent_status_widget, file_upload_widget
except ImportError:
    st.error("Frontend modules not found. Please ensure the project structure is complete.")
    st.stop()

# Initialize session state
if 'api_client' not in st.session_state:
    st.session_state.api_client = ExpenseTrackerAPI()

if 'agent_status' not in st.session_state:
    st.session_state.agent_status = {
        'ingestion': 'idle',
        'ner_merchant': 'idle',
        'classifier': 'idle',
        'pattern_analyzer': 'idle',
        'suggestion': 'idle',
        'safety_guard': 'idle'
    }

if 'transactions' not in st.session_state:
    st.session_state.transactions = []

if 'processing_log' not in st.session_state:
    st.session_state.processing_log = []

def main():
    """Main application function"""
    
    # Header
    st.title("🤖 Agentic Expense Tracker")
    st.markdown("### Multi-Agent AI Financial Intelligence System")
    
    # Sidebar
    with st.sidebar:
        st.title("🎛️ Control Panel")
        
        # API Status Check
        st.subheader("API Connection")
        if st.button("Test API Connection"):
            with st.spinner("Testing connection..."):
                try:
                    status = st.session_state.api_client.health_check()
                    if status.get('status') == 'healthy':
                        st.success("API Connected")
                    else:
                        st.error("API Unavailable")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")
        
        # Agent Status
        st.subheader("Agent Status")
        agent_status_widget(st.session_state.agent_status)
        
        # Quick Stats
        st.subheader("Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Transactions", len(st.session_state.transactions))
        with col2:
            st.metric("Processing Jobs", len(st.session_state.processing_log))
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Upload & Process", 
        "Dashboard", 
        "Transaction Analysis",
        "Agent Workflow"
    ])
    
    with tab1:
        upload_and_process_tab()
    
    with tab2:
        dashboard_tab()
    
    with tab3:
        analysis_tab()
    
    with tab4:
        workflow_tab()

def upload_and_process_tab():
    """File upload and processing tab"""
    st.header("Upload Transaction Data")
    
    # File upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload Transaction File",
            type=['csv', 'json', 'xlsx'],
            help="Upload your bank statement or transaction export (CSV, JSON, or Excel)",
            accept_multiple_files=False
        )
        
        # Sample format info
        with st.expander("Expected File Format"):
            st.code("""
CSV Format:
date,amount,description,payment_method,account_type
2024-01-15,-45.67,"STARBUCKS STORE #12345 NEW YORK NY","Credit Card","Checking"
2024-01-16,-123.45,"WALMART SUPERCENTER #5678","Debit Card","Checking"

JSON Format:
[
    {
        "date": "2024-01-15",
        "amount": -45.67,
        "description": "STARBUCKS STORE #12345 NEW YORK NY",
        "payment_method": "Credit Card",
        "account_type": "Checking"
    }
]
            """)
    
    with col2:
        # Processing options
        st.subheader("Processing Options")
        
        use_llm = st.checkbox("Use LLM for merchant extraction", value=True)
        enable_ml_classification = st.checkbox("Enable ML classification", value=True)
        security_scan = st.checkbox("Run security scan", value=True)
        generate_suggestions = st.checkbox("Generate suggestions", value=True)
    
    # Process file
    if uploaded_file is not None:
        st.subheader("Process Transactions")
        
        if st.button("Start Agent Processing", type="primary"):
            process_file(uploaded_file, {
                'use_llm': use_llm,
                'enable_ml_classification': enable_ml_classification,
                'security_scan': security_scan,
                'generate_suggestions': generate_suggestions
            })

def process_file(uploaded_file, options: Dict[str, bool]):
    """Process uploaded file through agent pipeline"""
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    agent_progress = st.empty()
    
    try:
        # Read file
        status_text.text("Reading file...")
        progress_bar.progress(10)
        
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.json'):
            data = json.load(uploaded_file)
            df = pd.DataFrame(data)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        
        transactions = df.to_dict('records')
        
        # Start agent processing
        status_text.text("Initializing agents...")
        progress_bar.progress(20)
        
        # Simulate agent workflow (replace with actual API calls)
        agents = ['ingestion', 'ner_merchant', 'classifier', 'pattern_analyzer', 'suggestion', 'safety_guard']
        
        for i, agent in enumerate(agents):
            status_text.text(f"Running {agent.replace('_', ' ').title()} Agent...")
            
            # Update agent status
            st.session_state.agent_status[agent] = 'running'
            
            # Show current agent status
            with agent_progress.container():
                cols = st.columns(6)
                for j, ag in enumerate(agents):
                    with cols[j]:
                        if ag == agent:
                            st.success(f"{ag.replace('_', ' ').title()}")
                        elif j < i:
                            st.success(f"{ag.replace('_', ' ').title()}")
                        else:
                            st.info(f"⏳ {ag.replace('_', ' ').title()}")
            
            # Simulate processing time
            time.sleep(2)
            
            # Update progress
            progress_bar.progress(20 + (i + 1) * (80 / len(agents)))
            
            # Mark as complete
            st.session_state.agent_status[agent] = 'complete'
        
        # Complete processing
        status_text.text("Processing complete!")
        progress_bar.progress(100)
        
        # Store results
        st.session_state.transactions = transactions
        st.session_state.processing_log.append({
            'timestamp': datetime.now(),
            'file': uploaded_file.name,
            'transactions': len(transactions),
            'status': 'completed'
        })
        
        # Show results
        st.success(f"Successfully processed {len(transactions)} transactions!")
        
        # Display sample results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Transactions Processed", len(transactions))
        with col2:
            st.metric("Categories Found", len(set([t.get('category', 'Unknown') for t in transactions])))
        with col3:
            st.metric("Merchants Identified", len(set([t.get('merchant', 'Unknown') for t in transactions])))
        
        # Show processed data preview
        with st.expander("Processed Data Preview"):
            st.dataframe(pd.DataFrame(transactions).head(10))
    
    except Exception as e:
        st.error(f"Processing failed: {str(e)}")
        status_text.text("Processing failed")

    # Conversational Transaction Entry (placed like the old manual entry)
    st.markdown("---")
    st.subheader("Conversational Transaction Entry")
    st.markdown("Enter transaction details by typing them naturally")
    
    # Import and display conversational interface
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

def dashboard_tab():
    """Main dashboard tab"""
    st.header("Expense Dashboard")
    
    if not st.session_state.transactions:
        st.info("Please upload and process transaction data first.")
        return
    
    # Key metrics
    df = pd.DataFrame(st.session_state.transactions)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_expenses = abs(df[df['amount'] < 0]['amount'].sum()) if 'amount' in df.columns else 0
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    
    with col2:
        avg_transaction = abs(df['amount'].mean()) if 'amount' in df.columns else 0
        st.metric("Average Transaction", f"${avg_transaction:.2f}")
    
    with col3:
        transaction_count = len(df)
        st.metric("Total Transactions", transaction_count)
    
    with col4:
        categories = len(df['category'].unique()) if 'category' in df.columns else 0
        st.metric("Categories", categories)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Expenses by Category")
        if 'category' in df.columns and 'amount' in df.columns:
            category_expenses = df.groupby('category')['amount'].sum().abs()
            fig = px.pie(values=category_expenses.values, names=category_expenses.index)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Spending Trend")
        if 'date' in df.columns and 'amount' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            daily_spending = df.groupby(df['date'].dt.date)['amount'].sum().abs()
            fig = px.line(x=daily_spending.index, y=daily_spending.values)
            fig.update_layout(xaxis_title="Date", yaxis_title="Amount ($)")
            st.plotly_chart(fig, use_container_width=True)

def analysis_tab():
    """Transaction analysis tab"""
    st.header("Transaction Analysis")
    
    if not st.session_state.transactions:
        st.info("Please upload and process transaction data first.")
        return
    
    df = pd.DataFrame(st.session_state.transactions)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'category' in df.columns:
            categories = st.multiselect("Filter by Category", df['category'].unique())
            if categories:
                df = df[df['category'].isin(categories)]
    
    with col2:
        if 'merchant' in df.columns:
            merchants = st.multiselect("Filter by Merchant", df['merchant'].unique())
            if merchants:
                df = df[df['merchant'].isin(merchants)]
    
    with col3:
        if 'amount' in df.columns:
            min_amount, max_amount = st.slider(
                "Amount Range",
                float(df['amount'].min()),
                float(df['amount'].max()),
                (float(df['amount'].min()), float(df['amount'].max()))
            )
            df = df[(df['amount'] >= min_amount) & (df['amount'] <= max_amount)]
    
    # Analysis results
    st.subheader("Filtered Transactions")
    st.dataframe(df, use_container_width=True)
    
    # Insights
    st.subheader("AI-Generated Insights")
    
    insights = [
        "You spend most on dining and entertainment on weekends",
        "Your grocery spending has increased 15% this month",
        "Unusual spending pattern detected at electronics stores",
        "Consider setting a budget limit for restaurant expenses"
    ]
    
    for insight in insights:
        st.info(insight)

def workflow_tab():
    """Agent workflow monitoring tab"""
    st.header("Agent Workflow Monitor")
    
    # Real-time agent status
    st.subheader("Agent Status Dashboard")
    
    # Create workflow visualization
    agents = [
        ("Ingestion", "Normalizes raw data"),
        ("NER/Merchant", "Extracts merchants"),
        ("Classifier", "Predicts categories"),
        ("Pattern Analyzer", "Detects patterns"),
        ("Suggestion", "Generates recommendations"),
        ("Safety Guard", "Security & compliance")
    ]
    
    cols = st.columns(3)
    for i, (name, desc) in enumerate(agents):
        with cols[i % 3]:
            agent_key = name.lower().split()[1].replace('/', '_')
            status = st.session_state.agent_status.get(agent_key, 'idle')
            
            if status == 'complete':
                st.success(f"{name}")
            elif status == 'running':
                st.warning(f"{name}")
            else:
                st.info(f"{name}")
            
            st.caption(desc)
    
    # Processing log
    st.subheader("Processing Log")
    
    if st.session_state.processing_log:
        log_df = pd.DataFrame(st.session_state.processing_log)
        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("No processing history available")
    
    # Agent communication
    st.subheader("Agent Communication")
    
    with st.expander("View Agent Messages"):
        st.code("""
[2024-08-23 10:30:15] Ingestion → NER/Merchant: Processed 150 transactions
[2024-08-23 10:30:16] NER/Merchant → Classifier: Identified 45 merchants
[2024-08-23 10:30:18] Classifier → Pattern Analyzer: Classified into 12 categories
[2024-08-23 10:30:20] Pattern Analyzer → Suggestion: Found 8 spending patterns
[2024-08-23 10:30:22] Suggestion → Safety Guard: Generated 5 recommendations
[2024-08-23 10:30:24] Safety Guard → System: No security issues detected
        """)

if __name__ == "__main__":
    main()
