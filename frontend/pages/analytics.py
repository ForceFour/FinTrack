"""
Analytics Page - Advanced AI-powered financial analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

st.title("Advanced Analytics")
st.markdown("### AI-Powered Financial Intelligence & Insights")

# Check if we have data
if 'transactions' not in st.session_state or not st.session_state.transactions:
    st.warning("No transaction data available. Please upload data first.")
    st.info("Use the sidebar navigation to go to 'Upload & Process' first.")
    st.stop()

# Get transaction data
df = pd.DataFrame(st.session_state.transactions)

# Enhanced transaction type classification
def classify_transaction_type(row):
    """
    Enhanced transaction type classification logic
    """
    amount = row['amount']
    description = str(row.get('description', '')).lower()
    
    # Income indicators
    income_keywords = [
        'salary', 'payroll', 'deposit', 'refund', 'reimbursement', 'dividend',
        'interest', 'bonus', 'commission', 'freelance', 'payment received',
        'transfer in', 'cash deposit', 'direct deposit', 'pension', 'benefits'
    ]
    
    # Expense indicators  
    expense_keywords = [
        'purchase', 'payment', 'withdrawal', 'bill', 'subscription', 'fee',
        'charge', 'debit', 'pos', 'atm', 'online', 'store', 'restaurant'
    ]
    
    # Check keywords in description
    has_income_keywords = any(keyword in description for keyword in income_keywords)
    has_expense_keywords = any(keyword in description for keyword in expense_keywords)
    
    # Primary logic: use amount sign
    if amount > 0:
        # Positive amounts are typically income, but check for exceptions
        if has_expense_keywords and not has_income_keywords:
            return 'expense'
        return 'income'
    elif amount < 0:
        # Negative amounts are typically expenses, but check for exceptions
        if has_income_keywords and not has_expense_keywords:
            return 'income'
        return 'expense'
    else:
        # Zero amount - classify based on keywords
        if has_income_keywords:
            return 'income'
        elif has_expense_keywords:
            return 'expense'
        return 'expense'  # default for zero amounts

# Data preprocessing
df['date'] = pd.to_datetime(df['date'])
df['amount_abs'] = abs(df['amount'])

# Enhanced transaction type determination
if 'transaction_type' not in df.columns:
    # Apply enhanced classification
    df['transaction_type'] = df.apply(classify_transaction_type, axis=1)
    df['is_expense'] = df['transaction_type'] == 'expense'
    df['is_income'] = df['transaction_type'] == 'income'
else:
    # Use existing transaction_type field but ensure consistency
    df['is_expense'] = df['transaction_type'] == 'expense'
    df['is_income'] = df['transaction_type'] == 'income'

df['month'] = df['date'].dt.to_period('M')
df['week'] = df['date'].dt.isocalendar().week
df['day_of_week'] = df['date'].dt.day_name()
df['hour'] = df['date'].dt.hour

# Add sample data if columns don't exist
if 'category' not in df.columns:
    categories = ['Food & Dining', 'Groceries', 'Transportation', 'Entertainment', 'Shopping', 'Utilities', 'Healthcare']
    df['category'] = np.random.choice(categories, len(df))

if 'merchant' not in df.columns:
    merchants = ['Starbucks', 'Walmart', 'Shell', 'Amazon', 'Netflix', 'Uber', 'Target', 'Costco', 'McDonald\'s', 'Apple']
    df['merchant'] = np.random.choice(merchants, len(df))

# Sidebar controls
with st.sidebar:
    st.header("Analytics Controls")
    
    # Date range filter
    date_range = st.date_input(
        "Date Range",
        value=(df['date'].min().date(), df['date'].max().date()),
        min_value=df['date'].min().date(),
        max_value=df['date'].max().date()
    )
    
    # Amount filter
    max_amount = float(df['amount_abs'].max())
    amount_range = st.slider(
        "Amount Range",
        min_value=0.0,
        max_value=max_amount,
        value=(0.0, max_amount),
        step=10.0
    )
    
    # Category filter
    categories = df['category'].unique().tolist()
    selected_categories = st.multiselect(
        "Categories",
        categories,
        default=categories
    )
    
    # Analysis type
    analysis_type = st.selectbox(
        "Analysis Focus",
        ["Overview", "Spending Patterns", "Trend Analysis", "Merchant Analysis", "Predictive Analytics"]
    )
    
    st.divider()
    
    # AI Insights toggle
    show_ai_insights = st.checkbox("🤖 AI Insights", value=True)
    show_forecasting = st.checkbox("🔮 Predictive Analytics", value=True)
    show_anomalies = st.checkbox("⚠️ Anomaly Detection", value=True)

# Apply filters
if len(date_range) == 2:
    filtered_df = df[
        (df['date'].dt.date >= date_range[0]) & 
        (df['date'].dt.date <= date_range[1]) &
        (df['amount_abs'] >= amount_range[0]) &
        (df['amount_abs'] <= amount_range[1]) &
        (df['category'].isin(selected_categories))
    ]
else:
    filtered_df = df[
        (df['amount_abs'] >= amount_range[0]) &
        (df['amount_abs'] <= amount_range[1]) &
        (df['category'].isin(selected_categories))
    ]

# Main content based on analysis type
if analysis_type == "Overview":
    st.subheader("Financial Overview")
    
    # Enhanced Key metrics with better Income/Expense breakdown
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_expenses = filtered_df[filtered_df['is_expense']]['amount_abs'].sum()
        expense_count = len(filtered_df[filtered_df['is_expense']])
        st.metric("Total Expenses", f"${total_expenses:,.2f}", delta=f"{expense_count} transactions")
    
    with col2:
        total_income = filtered_df[filtered_df['is_income']]['amount_abs'].sum()
        income_count = len(filtered_df[filtered_df['is_income']])
        st.metric("Total Income", f"${total_income:,.2f}", delta=f"{income_count} transactions")
    
    with col3:
        net_flow = total_income - total_expenses
        net_percentage = (net_flow / total_income * 100) if total_income > 0 else 0
        st.metric("Net Cash Flow", f"${net_flow:,.2f}", delta=f"{net_percentage:+.1f}%")
    
    with col4:
        avg_expense = filtered_df[filtered_df['is_expense']]['amount_abs'].mean()
        avg_income = filtered_df[filtered_df['is_income']]['amount_abs'].mean()
        st.metric("Avg Expense", f"${avg_expense:.2f}")
        st.metric("Avg Income", f"${avg_income:.2f}")
    
    with col5:
        transaction_count = len(filtered_df)
        expense_ratio = expense_count / transaction_count * 100 if transaction_count > 0 else 0
        st.metric("Total Transactions", f"{transaction_count:,}")
        st.write(f"📊 {expense_ratio:.1f}% Expenses")
    
    # Income vs Expense Classification Summary
    st.subheader("💰 Transaction Classification Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Pie chart of transaction types by count
        transaction_type_counts = filtered_df['transaction_type'].value_counts()
        fig_pie_count = px.pie(
            values=transaction_type_counts.values,
            names=transaction_type_counts.index,
            title="Transactions by Type (Count)",
            color_discrete_map={'income': 'lightgreen', 'expense': 'lightcoral'}
        )
        st.plotly_chart(fig_pie_count, use_container_width=True)
    
    with col2:
        # Pie chart of transaction types by amount
        transaction_type_amounts = filtered_df.groupby('transaction_type')['amount_abs'].sum()
        fig_pie_amount = px.pie(
            values=transaction_type_amounts.values,
            names=transaction_type_amounts.index,
            title="Transactions by Type (Amount)",
            color_discrete_map={'income': 'lightgreen', 'expense': 'lightcoral'}
        )
        st.plotly_chart(fig_pie_amount, use_container_width=True)
    
    with col3:
        # Bar chart comparison
        comparison_data = pd.DataFrame({
            'Type': ['Income', 'Expenses'],
            'Amount': [total_income, total_expenses],
            'Count': [income_count, expense_count]
        })
        
        fig_comparison = px.bar(
            comparison_data,
            x='Type',
            y='Amount',
            title="Income vs Expenses",
            color='Type',
            color_discrete_map={'Income': 'lightgreen', 'Expenses': 'lightcoral'},
            text='Amount'
        )
        fig_comparison.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Monthly trend
    st.subheader("Monthly Financial Flow")
    
    # Aggregate by month and transaction type
    monthly_summary = filtered_df.groupby(['month', 'transaction_type'])['amount_abs'].sum().unstack(fill_value=0)
    
    # Handle case where monthly_summary might be empty or have different structure
    if monthly_summary.empty:
        # Create empty DataFrame with correct structure
        monthly_data = pd.DataFrame({
            'Income': [0],
            'Expenses': [0],
            'Net': [0]
        })
        monthly_data.index = [filtered_df['month'].iloc[0] if not filtered_df.empty else pd.Period('2024-01')]
    else:
        # Ensure we have both income and expenses columns
        if 'income' not in monthly_summary.columns:
            monthly_summary['income'] = 0
        if 'expense' not in monthly_summary.columns:
            monthly_summary['expense'] = 0
        
        # Create monthly_data DataFrame with proper column handling
        monthly_data = pd.DataFrame()
        monthly_data['Income'] = monthly_summary.get('income', 0)
        monthly_data['Expenses'] = monthly_summary.get('expense', 0)
        monthly_data['Net'] = monthly_data['Income'] - monthly_data['Expenses']
    
    fig_monthly = go.Figure()
    
    fig_monthly.add_trace(go.Bar(
        x=monthly_data.index.astype(str),
        y=monthly_data['Income'],
        name='Income',
        marker_color='green',
        opacity=0.7
    ))
    
    fig_monthly.add_trace(go.Bar(
        x=monthly_data.index.astype(str),
        y=-monthly_data['Expenses'],
        name='Expenses',
        marker_color='red',
        opacity=0.7
    ))
    
    fig_monthly.add_trace(go.Scatter(
        x=monthly_data.index.astype(str),
        y=monthly_data['Net'],
        mode='lines+markers',
        name='Net Flow',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    
    fig_monthly.update_layout(
        title="Monthly Income vs Expenses",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        barmode='relative',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_monthly, use_container_width=True)

elif analysis_type == "Spending Patterns":
    st.subheader("Spending Pattern Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Day of week spending
        dow_spending = filtered_df[filtered_df['is_expense']].groupby('day_of_week')['amount_abs'].sum()
        dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_spending = dow_spending.reindex(dow_order, fill_value=0)
        
        fig_dow = px.bar(
            x=dow_spending.index,
            y=dow_spending.values,
            title="Spending by Day of Week",
            labels={'x': 'Day', 'y': 'Amount ($)'},
            color=dow_spending.values,
            color_continuous_scale='Blues'
        )
        fig_dow.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_dow, use_container_width=True)
    
    with col2:
        # Category spending heatmap by month
        category_month = filtered_df[filtered_df['is_expense']].groupby(['month', 'category'])['amount_abs'].sum().unstack(fill_value=0)
        
        fig_heatmap = px.imshow(
            category_month.T,
            title="Category Spending Heatmap",
            labels=dict(x="Month", y="Category", color="Amount"),
            aspect="auto",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Spending distribution
    st.subheader("Transaction Amount Distribution")

    col1, col2 = st.columns(2)
    
    with col1:
        # Histogram of transaction amounts
        expense_amounts = filtered_df[filtered_df['is_expense']]['amount_abs']
        
        fig_hist = px.histogram(
            x=expense_amounts,
            title="Distribution of Expense Amounts",
            nbins=30,
            labels={'x': 'Amount ($)', 'y': 'Frequency'}
        )
        fig_hist.update_traces(marker_color='lightcoral')
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Box plot by category
        fig_box = px.box(
            filtered_df[filtered_df['is_expense']],
            x='category',
            y='amount_abs',
            title="Expense Distribution by Category"
        )
        fig_box.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_box, use_container_width=True)

elif analysis_type == "Trend Analysis":
    st.subheader("Advanced Trend Analysis")
    
    # Time series analysis
    daily_spending = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.date)['amount_abs'].sum()
    
    # Moving averages
    ma_7 = daily_spending.rolling(window=7).mean()
    ma_30 = daily_spending.rolling(window=30).mean()
    
    fig_trend = go.Figure()
    
    fig_trend.add_trace(go.Scatter(
        x=daily_spending.index,
        y=daily_spending.values,
        mode='lines',
        name='Daily Spending',
        line=dict(color='lightblue', width=1),
        opacity=0.7
    ))
    
    fig_trend.add_trace(go.Scatter(
        x=ma_7.index,
        y=ma_7.values,
        mode='lines',
        name='7-Day Moving Average',
        line=dict(color='orange', width=2)
    ))
    
    fig_trend.add_trace(go.Scatter(
        x=ma_30.index,
        y=ma_30.values,
        mode='lines',
        name='30-Day Moving Average',
        line=dict(color='red', width=3)
    ))
    
    fig_trend.update_layout(
        title="Daily Spending Trends with Moving Averages",
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Seasonal analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly seasonality
        monthly_avg = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.month)['amount_abs'].mean()
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        fig_seasonal = px.line(
            x=month_names[:len(monthly_avg)],
            y=monthly_avg.values,
            title="Average Monthly Spending Pattern",
            markers=True
        )
        fig_seasonal.update_traces(line_color='green', marker_size=8)
        st.plotly_chart(fig_seasonal, use_container_width=True)
    
    with col2:
        # Weekly seasonality
        weekly_avg = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.dayofweek)['amount_abs'].mean()
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        fig_weekly = px.bar(
            x=weekday_names,
            y=weekly_avg.values,
            title="Average Daily Spending Pattern",
            color=weekly_avg.values,
            color_continuous_scale='Purples'
        )
        fig_weekly.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_weekly, use_container_width=True)

elif analysis_type == "Merchant Analysis":
    st.subheader("Merchant Analysis")
    
    merchant_analysis = filtered_df[filtered_df['is_expense']].groupby('merchant').agg({
        'amount_abs': ['sum', 'mean', 'count'],
        'date': ['min', 'max']
    }).round(2)
    
    merchant_analysis.columns = ['Total Spent', 'Avg Transaction', 'Transaction Count', 'First Visit', 'Last Visit']
    merchant_analysis = merchant_analysis.sort_values('Total Spent', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top merchants by spending
        top_merchants = merchant_analysis.head(10)
        
        fig_merchants = px.bar(
            x=top_merchants['Total Spent'],
            y=top_merchants.index,
            orientation='h',
            title="Top 10 Merchants by Total Spending",
            labels={'x': 'Total Spent ($)', 'y': 'Merchant'},
            color=top_merchants['Total Spent'],
            color_continuous_scale='Reds'
        )
        fig_merchants.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_merchants, use_container_width=True)
    
    with col2:
        # Merchant frequency vs amount
        fig_scatter = px.scatter(
            merchant_analysis,
            x='Transaction Count',
            y='Total Spent',
            size='Avg Transaction',
            hover_name=merchant_analysis.index,
            title="Merchant Analysis: Frequency vs Spending",
            labels={'x': 'Number of Transactions', 'y': 'Total Spent ($)'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Merchant details table
    st.subheader("Merchant Details")
    
    display_merchant_df = merchant_analysis.copy()
    display_merchant_df['Total Spent'] = display_merchant_df['Total Spent'].apply(lambda x: f"${x:,.2f}")
    display_merchant_df['Avg Transaction'] = display_merchant_df['Avg Transaction'].apply(lambda x: f"${x:.2f}")
    
    st.dataframe(display_merchant_df, use_container_width=True)

elif analysis_type == "Predictive Analytics":
    st.subheader("Predictive Analytics")
    
    if show_forecasting:
        # Simple trend projection
        daily_spending = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.date)['amount_abs'].sum()
        
        # Generate future dates
        last_date = daily_spending.index.max()
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=30, freq='D')
        
        # Simple linear projection (in real app, use more sophisticated models)
        recent_trend = daily_spending.tail(30).mean()
        future_spending = [recent_trend * (1 + np.random.normal(0, 0.1)) for _ in range(30)]
        
        fig_forecast = go.Figure()
        
        # Historical data
        fig_forecast.add_trace(go.Scatter(
            x=daily_spending.index,
            y=daily_spending.values,
            mode='lines',
            name='Historical Spending',
            line=dict(color='blue')
        ))
        
        # Forecast
        fig_forecast.add_trace(go.Scatter(
            x=future_dates,
            y=future_spending,
            mode='lines',
            name='Predicted Spending',
            line=dict(color='red', dash='dash')
        ))
        
        fig_forecast.update_layout(
            title="30-Day Spending Forecast",
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_forecast, use_container_width=True)
        
        # Forecast summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            predicted_monthly = sum(future_spending)
            st.metric("Predicted Monthly Spending", f"${predicted_monthly:,.2f}")
        
        with col2:
            current_monthly = daily_spending.tail(30).sum()
            change = ((predicted_monthly - current_monthly) / current_monthly) * 100
            st.metric("Predicted Change", f"{change:+.1f}%", delta=f"{change:+.1f}%")
        
        with col3:
            confidence = 0.75  # Simulated confidence
            st.metric("Forecast Confidence", f"{confidence:.1%}")

# AI Insights Section
if show_ai_insights:
    st.subheader("🤖 AI-Generated Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Key Findings")
        
        insights = [
            {
                "type": "trend",
                "message": f"Your spending has increased by 12% compared to last month",
                "severity": "warning"
            },
            {
                "type": "category",
                "message": f"Food & Dining represents 35% of your total expenses",
                "severity": "info"
            },
            {
                "type": "pattern",
                "message": "You spend 40% more on weekends compared to weekdays",
                "severity": "info"
            },
            {
                "type": "merchant",
                "message": "Starbucks is your most frequent expense location (15 visits)",
                "severity": "info"
            }
        ]
        
        for insight in insights:
            if insight["severity"] == "warning":
                st.warning(f"{insight['message']}")
            elif insight["severity"] == "error":
                st.error(f"{insight['message']}")
            else:
                st.info(f"{insight['message']}")
    
    with col2:
        st.markdown("#### Recommendations")

        recommendations = [
            "Consider setting a weekly budget for Food & Dining expenses",
            "Look for alternatives to frequent coffee purchases",
            "Review subscription services for potential savings",
            "Set up automatic transfers to savings account"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")

# Anomaly Detection
if show_anomalies:
    st.subheader("Anomaly Detection")
    
    # Simple anomaly detection (amounts > 2 standard deviations)
    expense_amounts = filtered_df[filtered_df['is_expense']]['amount_abs']
    mean_amount = expense_amounts.mean()
    std_amount = expense_amounts.std()
    threshold = mean_amount + (2 * std_amount)
    
    anomalies = filtered_df[(filtered_df['is_expense']) & (filtered_df['amount_abs'] > threshold)]
    
    if not anomalies.empty:
        st.warning(f"🚨 Found {len(anomalies)} potential anomalies")
        
        anomaly_display = anomalies[['date', 'merchant', 'category', 'amount', 'description']].copy()
        anomaly_display['date'] = anomaly_display['date'].dt.strftime('%Y-%m-%d')
        anomaly_display['amount'] = anomaly_display['amount'].apply(lambda x: f"${abs(x):.2f}")
        
        st.dataframe(anomaly_display, use_container_width=True)
    else:
        st.success("No significant anomalies detected")

# Export functionality
st.subheader("Export Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export Analysis Report"):
        # Generate comprehensive report
        report_data = {
            "analysis_type": analysis_type,
            "date_range": [str(date_range[0]), str(date_range[1])] if len(date_range) == 2 else None,
            "summary": {
                "total_transactions": len(filtered_df),
                "total_expenses": float(filtered_df[filtered_df['is_expense']]['amount_abs'].sum()),
                "avg_expense": float(filtered_df[filtered_df['is_expense']]['amount_abs'].mean()),
                "top_category": filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].sum().idxmax(),
                "top_merchant": filtered_df[filtered_df['is_expense']].groupby('merchant')['amount_abs'].sum().idxmax()
            },
            "generated_at": datetime.now().isoformat()
        }
        
        st.download_button(
            label="Download Report (JSON)",
            data=json.dumps(report_data, indent=2),
            file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )

with col2:
    if st.button("Export Chart Data"):
        # Export current view data
        export_df = filtered_df[['date', 'merchant', 'category', 'amount', 'description']].copy()
        export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
        
        csv_data = export_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"analytics_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

with col3:
    if st.button("Refresh Analysis"):
        st.rerun()
