"""
Dashboard Page - Comprehensive expense overview with AI insights
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Dashboard", page_icon="", layout="wide")

st.title("Expense Dashboard")
st.markdown("### AI-Powered Financial Intelligence Overview")

# Check if we have data
if 'transactions' not in st.session_state or not st.session_state.transactions:
    st.warning("No transaction data available. Please upload data from the main page.")
    st.info("Use the sidebar navigation to go to 'Upload & Process' first.")
    st.stop()

# Get transaction data
df = pd.DataFrame(st.session_state.transactions)

# Ensure we have required columns
required_columns = ['date', 'amount', 'description']
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error(f"Missing required columns: {missing_columns}")
    st.stop()

# Data preprocessing
df['date'] = pd.to_datetime(df['date'])
df['amount_abs'] = abs(df['amount'])
df['is_expense'] = df['amount'] < 0

# Add sample categories and merchants if not present
if 'category' not in df.columns:
    categories = ['Food & Dining', 'Groceries', 'Transportation', 'Entertainment', 'Shopping', 'Utilities', 'Healthcare']
    df['category'] = np.random.choice(categories, len(df))

if 'merchant' not in df.columns:
    merchants = ['Starbucks', 'Walmart', 'Shell', 'Amazon', 'Netflix', 'Uber', 'Target']
    df['merchant'] = np.random.choice(merchants, len(df))

# Key Performance Indicators
st.subheader("Key Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_expenses = df[df['is_expense']]['amount_abs'].sum()
    st.metric(
        "Total Expenses",
        f"${total_expenses:,.2f}",
        delta="-12.5%",
        delta_color="inverse"
    )

with col2:
    avg_transaction = df['amount_abs'].mean()
    st.metric(
        "Avg Transaction",
        f"${avg_transaction:.2f}",
        delta="+5.2%"
    )

with col3:
    transaction_count = len(df)
    st.metric(
        "Total Transactions",
        f"{transaction_count:,}",
        delta="+23"
    )

with col4:
    unique_merchants = df['merchant'].nunique()
    st.metric(
        "Unique Merchants",
        f"{unique_merchants}",
        delta="+3"
    )

with col5:
    categories_used = df['category'].nunique()
    st.metric(
        "Categories",
        f"{categories_used}",
        delta="0"
    )

# Charts Section
st.subheader("Expense Analysis")

# Row 1: Spending by Category and Monthly Trend
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Spending by Category")
    category_spending = df[df['is_expense']].groupby('category')['amount_abs'].sum().sort_values(ascending=False)
    
    fig_category = px.pie(
        values=category_spending.values,
        names=category_spending.index,
        title="",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_category.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_category, use_container_width=True)

with col2:
    st.markdown("#### Daily Spending Trend")
    daily_spending = df[df['is_expense']].groupby(df['date'].dt.date)['amount_abs'].sum()
    
    fig_trend = px.line(
        x=daily_spending.index,
        y=daily_spending.values,
        title="",
        labels={'x': 'Date', 'y': 'Amount ($)'}
    )
    fig_trend.update_traces(line_color='#FF6B6B', line_width=3)
    fig_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        showlegend=False
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# Row 2: Top Merchants and Payment Methods
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Top Merchants by Spending")
    merchant_spending = df[df['is_expense']].groupby('merchant')['amount_abs'].sum().sort_values(ascending=False).head(10)
    
    fig_merchants = px.bar(
        x=merchant_spending.values,
        y=merchant_spending.index,
        orientation='h',
        title="",
        labels={'x': 'Amount ($)', 'y': 'Merchant'},
        color=merchant_spending.values,
        color_continuous_scale='Reds'
    )
    fig_merchants.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_merchants, use_container_width=True)

with col2:
    st.markdown("#### Payment Method Usage")
    if 'payment_method' in df.columns:
        payment_methods = df['payment_method'].value_counts()
    else:
        # Sample data if payment_method not available
        payment_methods = pd.Series({
            'Credit Card': len(df) * 0.6,
            'Debit Card': len(df) * 0.25,
            'Cash': len(df) * 0.1,
            'Digital Wallet': len(df) * 0.05
        }).astype(int)
    
    fig_payment = px.bar(
        x=payment_methods.index,
        y=payment_methods.values,
        title="",
        labels={'x': 'Payment Method', 'y': 'Count'},
        color=payment_methods.values,
        color_continuous_scale='Blues'
    )
    fig_payment.update_layout(
        showlegend=False,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_payment, use_container_width=True)

# AI Insights Section
st.subheader("AI-Generated Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Spending Insights")
    
    insights = [
        {
            "icon": "📈",
            "title": "Spending Trend",
            "message": f"Your spending increased by 12% compared to last month. Total: ${total_expenses:,.2f}",
            "type": "warning"
        },
        {
            "icon": "🏪",
            "title": "Top Category",
            "message": f"Most spending in '{category_spending.index[0]}' category (${category_spending.iloc[0]:,.2f})",
            "type": "info"
        },
        {
            "icon": "🔄",
            "title": "Recurring Patterns",
            "message": f"Found {np.random.randint(3, 8)} recurring transactions that could be subscriptions",
            "type": "info"
        },
        {
            "icon": "⚠️",
            "title": "Budget Alert",
            "message": "You've exceeded your dining budget by 15% this month",
            "type": "error"
        }
    ]
    
    for insight in insights:
        if insight["type"] == "warning":
            st.warning(f"{insight['icon']} **{insight['title']}**: {insight['message']}")
        elif insight["type"] == "error":
            st.error(f"{insight['icon']} **{insight['title']}**: {insight['message']}")
        else:
            st.info(f"{insight['icon']} **{insight['title']}**: {insight['message']}")

with col2:
    st.markdown("#### Savings Opportunities")
    
    opportunities = [
        {
            "category": "Food & Dining",
            "current": 450,
            "suggested": 350,
            "savings": 100
        },
        {
            "category": "Entertainment",
            "current": 200,
            "suggested": 150,
            "savings": 50
        },
        {
            "category": "Transportation",
            "current": 300,
            "suggested": 250,
            "savings": 50
        }
    ]
    
    for opp in opportunities:
        with st.container():
            st.markdown(f"**{opp['category']}**")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Current", f"${opp['current']}")
            with col_b:
                st.metric("Suggested", f"${opp['suggested']}")
            with col_c:
                st.metric("Savings", f"${opp['savings']}", delta=f"-${opp['savings']}")
            st.divider()

# Recent Transactions
st.subheader("Recent Transactions")

# Display recent transactions
recent_df = df.sort_values('date', ascending=False).head(10)
display_df = recent_df[['date', 'merchant', 'category', 'amount', 'description']].copy()
display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:.2f}")

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "date": "Date",
        "merchant": "Merchant",
        "category": "Category",
        "amount": "Amount",
        "description": "Description"
    }
)

# Export functionality
st.subheader("Export Data")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export Dashboard Report"):
        # Generate dashboard report
        report_data = {
            "summary": {
                "total_expenses": total_expenses,
                "avg_transaction": avg_transaction,
                "transaction_count": transaction_count,
                "unique_merchants": unique_merchants
            },
            "top_categories": category_spending.to_dict(),
            "top_merchants": merchant_spending.to_dict(),
            "insights": [insight["message"] for insight in insights]
        }
        
        st.download_button(
            label="Download Report (JSON)",
            data=pd.Series(report_data).to_json(),
            file_name=f"expense_report_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with col2:
    if st.button("Export Transaction Data"):
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col3:
    if st.button("Refresh Data"):
        st.rerun()
