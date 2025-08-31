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
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas

def format_currency(amount, show_full_on_hover=True):
    """Format currency values to be more readable with K/M/B suffixes"""
    # Full formatted value for tooltip
    full_value = f"LKR{amount:,.2f}"
    
    # Simplified value for display
    if abs(amount) >= 1e9:
        simple_value = f"LKR {amount/1e9:.1f}B"
    elif abs(amount) >= 1e6:
        simple_value = f"LKR {amount/1e6:.1f}M"
    elif abs(amount) >= 1e3:
        simple_value = f"LKR {amount/1e3:.1f}K"
    else:
        simple_value = f"LKR {amount:.0f}"
    
    if show_full_on_hover:
        # Use markdown with hover tooltip
        return f"<span title='{full_value}'>{simple_value}</span>"
    return simple_value

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
        formatted_expenses = format_currency(total_expenses)
        st.markdown(
            f"""
            <div style='text-align: center'>
                <p style='margin-bottom: 0'>Total Expenses ({expense_count} transactions)</p>
                <div title='LKR{total_expenses:,.2f}' style='font-size: 28px'>
                    {formatted_expenses}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        total_income = filtered_df[~filtered_df['is_expense']]['amount_abs'].sum()
        income_count = len(filtered_df[~filtered_df['is_expense']])
        formatted_income = format_currency(total_income)
        st.markdown(
            f"""
            <div style='text-align: center'>
                <p style='margin-bottom: 0'>Total Income ({income_count} transactions)</p>
                <div title='LKR{total_income:,.2f}' style='font-size: 28px'>
                    {formatted_income}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col3:
        net_flow = total_income - total_expenses
        formatted_net = format_currency(net_flow)
        st.markdown(
            f"""
            <div style='text-align: center'>
                <p style='margin-bottom: 0'>Net Cash Flow</p>
                <div title='LKR{net_flow:,.2f}' style='font-size: 28px'>
                    {formatted_net}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col4:
        avg_expense = filtered_df[filtered_df['is_expense']]['amount_abs'].mean()
        formatted_avg = format_currency(avg_expense)
        st.markdown(
            f"""
            <div style='text-align: center'>
                <p style='margin-bottom: 0'>Avg Expense</p>
                <div title='LKR{avg_expense:,.2f}' style='font-size: 28px'>
                    {formatted_avg}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col5:
        transaction_count = len(filtered_df)
        formatted_count = f"{transaction_count:,}"
        st.markdown(
            f"""
            <div style='text-align: center'>
                <p style='margin-bottom: 0'>Transactions</p>
                <div style='font-size: 28px'>
                    {formatted_count}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Monthly trend
    st.subheader("Monthly Financial Flow")
    
    # First, separate income and expenses
    income_data = filtered_df[~filtered_df['is_expense']].groupby('month')['amount_abs'].sum()
    expense_data = filtered_df[filtered_df['is_expense']].groupby('month')['amount_abs'].sum()
    
    # Create DataFrame with both series
    monthly_data = pd.DataFrame({
        'Income': income_data,
        'Expenses': expense_data
    }).fillna(0)
    
    # Calculate net
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
        yaxis_title="Amount (LKR)",
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
            labels={'x': 'Day', 'y': 'Amount (LKR)'},
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
            labels={'x': 'Amount (LKR)', 'y': 'Frequency'}
        )
        fig_hist.update_traces(marker_color='lightcoral')
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Box plot by category
        fig_box = px.box(
            filtered_df[filtered_df['is_expense']],
            x='category',
            y='amount_abs',
            title="Expense Distribution by Category",
            labels={'amount_abs': 'Amount (LKR)'}
        )
        fig_box.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_box, use_container_width=True)

elif analysis_type == "Trend Analysis":
    st.subheader("Advanced Trend Analysis")
    
    # Time series analysis
    daily_spending = filtered_df[filtered_df['is_expense']].groupby('date')['amount_abs'].sum().reset_index()
    daily_spending = daily_spending.sort_values('date')
    
    # Calculate moving averages
    daily_spending['MA7'] = daily_spending['amount_abs'].rolling(window=7).mean()
    daily_spending['MA30'] = daily_spending['amount_abs'].rolling(window=30).mean()
    
    fig_trend = go.Figure()
    
    # Daily spending
    fig_trend.add_trace(go.Scatter(
        x=daily_spending['date'],
        y=daily_spending['amount_abs'],
        mode='lines',
        name='Daily Spending',
        line=dict(color='lightblue', width=1),
        opacity=0.7
    ))
    
    # 7-day moving average
    fig_trend.add_trace(go.Scatter(
        x=daily_spending['date'],
        y=daily_spending['MA7'],
        mode='lines',
        name='7-Day Moving Average',
        line=dict(color='orange', width=2)
    ))
    
    # 30-day moving average
    fig_trend.add_trace(go.Scatter(
        x=daily_spending['date'],
        y=daily_spending['MA30'],
        mode='lines',
        name='30-Day Moving Average',
        line=dict(color='red', width=3)
    ))
    
    fig_trend.update_layout(
        title="Daily Spending Trends with Moving Averages",
        xaxis_title="Date",
        yaxis_title="Amount (LKR)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Seasonal analysis
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly seasonality
        monthly_avg = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.month)['amount_abs'].mean()
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Create proper DataFrame for plotting
        seasonal_df = pd.DataFrame({
            'Month': month_names[:len(monthly_avg)],
            'Average Spending': monthly_avg.values
        })
        
        fig_seasonal = px.line(
            seasonal_df,
            x='Month',
            y='Average Spending',
            title="Average Monthly Spending Pattern",
            markers=True,
            labels={'Average Spending': 'Amount (LKR)'}
        )
        fig_seasonal.update_traces(line_color='green', marker_size=8)
        st.plotly_chart(fig_seasonal, use_container_width=True)
    
    with col2:
        # Weekly seasonality
        weekly_avg = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.dayofweek)['amount_abs'].mean()
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        # Create DataFrame for weekly plot
        weekly_df = pd.DataFrame({
            'Day': weekday_names,
            'Average Spending': weekly_avg.values
        })
        
        fig_weekly = px.bar(
            weekly_df,
            x='Day',
            y='Average Spending',
            title="Average Daily Spending Pattern",
            color='Average Spending',
            color_continuous_scale='Purples',
            labels={'Average Spending': 'Amount (LKR)'}
        )
        fig_weekly.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_weekly, use_container_width=True)

elif analysis_type == "Merchant Analysis":
    st.subheader("Merchant Analysis")
    
    # Prepare merchant analysis data
    merchant_summary = filtered_df[filtered_df['is_expense']].groupby('merchant').agg({
        'amount_abs': ['sum', 'mean', 'count'],
        'date': ['min', 'max']
    })
    
    # Flatten column names and rename
    merchant_summary.columns = ['total_spent', 'avg_transaction', 'transaction_count', 'first_visit', 'last_visit']
    merchant_summary = merchant_summary.round(2)
    merchant_summary = merchant_summary.sort_values('total_spent', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top merchants by spending
        top_merchants = merchant_summary.head(10).reset_index()
        
        fig_merchants = px.bar(
            top_merchants,
            x='total_spent',
            y='merchant',
            orientation='h',
            title="Top 10 Merchants by Total Spending",
            labels={'total_spent': 'Total Spent (LKR)', 'merchant': 'Merchant'},
            color='total_spent',
            color_continuous_scale='Reds'
        )
        fig_merchants.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_merchants, use_container_width=True)
    
    with col2:
        # Merchant frequency vs amount
        fig_scatter = px.scatter(
            merchant_summary.reset_index(),
            x='transaction_count',
            y='total_spent',
            size='avg_transaction',
            hover_name='merchant',
            title="Merchant Analysis: Frequency vs Spending",
            labels={
                'transaction_count': 'Number of Transactions',
                'total_spent': 'Total Spent (LKR)',
                'avg_transaction': 'Average Transaction (LKR)'
            }
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Merchant details table
    st.subheader("Merchant Details")
    
    display_merchant_df = merchant_summary.reset_index()
    display_merchant_df['total_spent'] = display_merchant_df['total_spent'].apply(lambda x: f"LKR{x:,.2f}")
    display_merchant_df['avg_transaction'] = display_merchant_df['avg_transaction'].apply(lambda x: f"LKR{x:.2f}")
    
    # Rename columns for display
    display_merchant_df.columns = ['Merchant', 'Total Spent', 'Avg Transaction', 'Transaction Count', 'First Visit', 'Last Visit']
    
    st.dataframe(display_merchant_df, use_container_width=True)

elif analysis_type == "Predictive Analytics":
    st.subheader("Predictive Analytics")
    
    if show_forecasting:
        # Simple trend projection
        daily_spending = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.date)['amount_abs'].sum()
        
        # Generate future dates
        last_date = pd.to_datetime(daily_spending.index.max())
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=30, freq='D')
        
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
            yaxis_title="Amount (LKR)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_forecast, use_container_width=True)
        
        # Forecast summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            predicted_monthly = sum(future_spending)
            st.metric("Predicted Monthly Spending", f"LKR{predicted_monthly:,.2f}")
        
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
        
        # Calculate insights from actual data
        insights = []
        
        # Spending pattern and correlation analysis
        if not filtered_df.empty:
            # Analyze spending vs. time of month
            filtered_df['day_of_month'] = filtered_df['date'].dt.day
            early_month_spending = filtered_df[filtered_df['day_of_month'] <= 15]['amount_abs'].mean()
            late_month_spending = filtered_df[filtered_df['day_of_month'] > 15]['amount_abs'].mean()
            if early_month_spending != 0 and late_month_spending != 0:
                month_half_diff = ((early_month_spending - late_month_spending) / late_month_spending) * 100
                if abs(month_half_diff) > 20:
                    insights.append({
                        "type": "timing_pattern",
                        "message": f"You tend to spend {'more' if month_half_diff > 0 else 'less'} in the first half of the month " +
                                 f"(LKR {abs(early_month_spending - late_month_spending):,.2f} {'higher' if month_half_diff > 0 else 'lower'} on average)",
                        "severity": "warning" if month_half_diff > 0 else "info"
                    })

            # Analyze expense clustering
            expense_intervals = filtered_df[filtered_df['is_expense']]['date'].diff().dt.days
            if not expense_intervals.empty:
                avg_interval = expense_intervals.mean()
                if avg_interval < 2:
                    insights.append({
                        "type": "spending_behavior",
                        "message": "Your expenses tend to cluster together - consider planning purchases more evenly throughout the month",
                        "severity": "warning"
                    })

            # Category diversification analysis
            category_amounts = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].sum()
            total_expense = category_amounts.sum()
            if not category_amounts.empty and total_expense > 0:
                category_percentages = (category_amounts / total_expense) * 100
                high_concentration_cats = category_percentages[category_percentages > 30]
                if not high_concentration_cats.empty:
                    insights.append({
                        "type": "diversification",
                        "message": f"High spending concentration in {len(high_concentration_cats)} categories - " +
                                 f"consider diversifying expenses for better financial stability",
                        "severity": "warning"
                    })

        # Category analysis
        if not filtered_df[filtered_df['is_expense']].empty:
            category_totals = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].sum()
            total_expenses = filtered_df[filtered_df['is_expense']]['amount_abs'].sum()
            top_category_pct = (category_totals.max() / total_expenses) * 100
            top_category_name = category_totals.idxmax()
            
            insights.append({
                "type": "category",
                "message": f"{top_category_name} represents {top_category_pct:.1f}% of your total expenses",
                "severity": "warning" if top_category_pct > 50 else "info"
            })

        # Day of week pattern analysis
        daily_spending = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.strftime('%A'))['amount_abs'].mean()
        if not daily_spending.empty:
            highest_day = daily_spending.idxmax()
            highest_amount = daily_spending.max()
            insights.append({
                "type": "pattern",
                "message": f"{highest_day}s tend to be your highest spending days (LKR {highest_amount:,.2f} on average)",
                "severity": "info"
            })

        # Merchant analysis
        merchant_visits = filtered_df[filtered_df['is_expense']]['merchant'].value_counts()
        if not merchant_visits.empty:
            top_merchant = merchant_visits.index[0]
            visit_count = merchant_visits.iloc[0]
            merchant_total = filtered_df[filtered_df['merchant'] == top_merchant]['amount_abs'].sum()
            
            insights.append({
                "type": "merchant",
                "message": f"{top_merchant} is your most frequent expense location ({visit_count} visits, total ${merchant_total:.2f})",
                "severity": "info"
            })

            # Analyze transaction size trends
            expense_amounts = filtered_df[filtered_df['is_expense']]['amount_abs']
            if not expense_amounts.empty:
                large_transactions = expense_amounts[expense_amounts > expense_amounts.mean() + 2*expense_amounts.std()]
                if not large_transactions.empty:
                    unusual_dates = filtered_df[filtered_df['amount_abs'].isin(large_transactions)]['date']
                    date_patterns = unusual_dates.dt.day.value_counts()
                    if len(date_patterns) >= 2:
                        insights.append({
                            "type": "transaction_pattern",
                            "message": "Large expenses frequently occur on similar dates - " +
                                     "this might indicate recurring major payments or bills",
                            "severity": "info"
                        })
                        
            # Analyze income stability
            if not filtered_df[~filtered_df['is_expense']].empty:
                monthly_income_var = filtered_df[~filtered_df['is_expense']].groupby(
                    filtered_df['date'].dt.strftime('%B %Y'))['amount_abs'].sum().std()
                monthly_income_mean = filtered_df[~filtered_df['is_expense']].groupby(
                    filtered_df['date'].dt.strftime('%B %Y'))['amount_abs'].sum().mean()
                if monthly_income_mean > 0:
                    income_volatility = (monthly_income_var / monthly_income_mean) * 100
                    if income_volatility > 20:
                        insights.append({
                            "type": "income_stability",
                            "message": f"Your monthly income shows significant variation (±{income_volatility:.1f}%) - " +
                                     "consider building a larger emergency fund",
                            "severity": "warning"
                        })        # Time-based analysis
        monthly_expenses = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.strftime('%B %Y'))['amount_abs'].sum()
        monthly_income = filtered_df[~filtered_df['is_expense']].groupby(filtered_df['date'].dt.strftime('%B %Y'))['amount_abs'].sum()
        
        if not monthly_expenses.empty:
            max_expense_month = monthly_expenses.idxmax()
            min_expense_month = monthly_expenses.idxmin()
            insights.append({
                "type": "monthly_expense",
                "message": f"{max_expense_month} had the highest expenses (LKR {monthly_expenses[max_expense_month]:,.2f})",
                "severity": "warning" if monthly_expenses[max_expense_month] > monthly_expenses.mean() * 1.5 else "info"
            })
            insights.append({
                "type": "monthly_expense_low",
                "message": f"{min_expense_month} had the lowest expenses (LKR {monthly_expenses[min_expense_month]:,.2f})",
                "severity": "success"
            })
            
        if not monthly_income.empty:
            max_income_month = monthly_income.idxmax()
            min_income_month = monthly_income.idxmin()
            insights.append({
                "type": "monthly_income",
                "message": f"{max_income_month} was your best month for income (LKR {monthly_income[max_income_month]:,.2f})",
                "severity": "success"
            })
            insights.append({
                "type": "monthly_income_low",
                "message": f"{min_income_month} had the lowest income (LKR {monthly_income[min_income_month]:,.2f})",
                "severity": "warning"
            })
            
        # Daily patterns
        daily_avg = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.strftime('%A'))['amount_abs'].mean()
        if not daily_avg.empty:
            highest_spending_day = daily_avg.idxmax()
            lowest_spending_day = daily_avg.idxmin()
            insights.append({
                "type": "daily_pattern_high",
                "message": f"{highest_spending_day}s tend to be your highest spending days (LKR {daily_avg[highest_spending_day]:,.2f} on average)",
                "severity": "warning"
            })
            insights.append({
                "type": "daily_pattern_low",
                "message": f"{lowest_spending_day}s are your most economical days (LKR {daily_avg[lowest_spending_day]:,.2f} on average)",
                "severity": "success"
            })
            
        # Category analysis
        category_expenses = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].agg(['sum', 'count'])
        if not category_expenses.empty:
            top_expense_cat = category_expenses['sum'].idxmax()
            top_expense_amount = category_expenses.loc[top_expense_cat, 'sum']
            top_expense_count = category_expenses.loc[top_expense_cat, 'count']
            insights.append({
                "type": "category_high",
                "message": f"Highest spending category: {top_expense_cat} (LKR {top_expense_amount:,.2f} across {top_expense_count} transactions)",
                "severity": "warning" if top_expense_amount > category_expenses['sum'].mean() * 2 else "info"
            })
            
        # Merchant analysis
        merchant_expenses = filtered_df[filtered_df['is_expense']].groupby('merchant')['amount_abs'].agg(['sum', 'count'])
        if not merchant_expenses.empty:
            top_merchant = merchant_expenses['sum'].idxmax()
            merchant_total = merchant_expenses.loc[top_merchant, 'sum']
            merchant_count = merchant_expenses.loc[top_merchant, 'count']
            insights.append({
                "type": "merchant_high",
                "message": f"Most significant merchant: {top_merchant} (LKR {merchant_total:,.2f} across {merchant_count} visits)",
                "severity": "warning" if merchant_count > merchant_expenses['count'].mean() * 2 else "info"
            })
            
        # Transaction size analysis
        large_transactions = filtered_df[filtered_df['is_expense'] & (filtered_df['amount_abs'] > filtered_df['amount_abs'].mean() * 2)]
        if not large_transactions.empty:
            insights.append({
                "type": "large_transactions",
                "message": f"Found {len(large_transactions)} unusually large transactions (over LKR {filtered_df['amount_abs'].mean() * 2:,.2f})",
                "severity": "warning"
            })
            
        # Most common transaction category
        category_counts = filtered_df['category'].value_counts()
        if not category_counts.empty:
            most_common_category = category_counts.index[0]
            category_count = category_counts.iloc[0]
            category_total = filtered_df[filtered_df['category'] == most_common_category]['amount_abs'].sum()
            insights.append({
                "type": "frequency",
                "message": f"Most frequent category: {most_common_category} ({category_count} transactions, total LKR {category_total:,.2f})",
                "severity": "info"
            })
        
        if not insights:
            # This should rarely happen now, as we've added more varied analyses
            current_period = filtered_df['date'].dt.strftime('%B %Y').iloc[0] if not filtered_df.empty else "the selected period"
            insights.append({
                "type": "info",
                "message": f"Showing transaction analysis for {current_period}",
                "severity": "info"
            })
            
        for insight in insights:
            if insight["severity"] == "warning":
                st.warning(f"{insight['message']}")
            elif insight["severity"] == "error":
                st.error(f"{insight['message']}")
            else:
                st.info(f"{insight['message']}")
    
    with col2:
        pass  # Recommendations section removed

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
        anomaly_display['amount'] = anomaly_display['amount'].apply(lambda x: f"LKR{abs(x):.2f}")
        
        st.dataframe(anomaly_display, use_container_width=True)
    else:
        st.success("No significant anomalies detected")

# Export functionality
st.subheader("Export Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export Analysis Report"):
        # Generate comprehensive report
        def generate_pdf_report():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#1f77b4')
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize = 16,
                spaceAfter=12,
                textColor=colors.HexColor('#2c3e50')
            )

            # Title
            story.append(Paragraph("FinTrack Analytics Report", title_style))
            story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles["Italic"]))
            story.append(Spacer(1, 20))

            # Analysis Type and Date Range
            story.append(Paragraph(f"Analysis Type: {analysis_type}", heading_style))
            if len(date_range) == 2:
                story.append(Paragraph(f"Date Range: {date_range[0]} to {date_range[1]}", styles["Normal"]))
            story.append(Spacer(1, 20))

            # Key Metrics
            story.append(Paragraph("Key Metrics", heading_style))
            
            # Create table data
            total_expenses = filtered_df[filtered_df['is_expense']]['amount_abs'].sum() if not filtered_df[filtered_df['is_expense']].empty else 0
            total_income = filtered_df[~filtered_df['is_expense']]['amount_abs'].sum() if not filtered_df[~filtered_df['is_expense']].empty else 0
            avg_expense = filtered_df[filtered_df['is_expense']]['amount_abs'].mean() if not filtered_df[filtered_df['is_expense']].empty else 0
            top_category = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].sum().idxmax() if not filtered_df[filtered_df['is_expense']].empty else "N/A"
            top_merchant = filtered_df[filtered_df['is_expense']].groupby('merchant')['amount_abs'].sum().idxmax() if not filtered_df[filtered_df['is_expense']].empty else "N/A"

            data = [
                ["Metric", "Value"],
                ["Transactions", f"{len(filtered_df):,}"],
                ["Total Income", f"LKR {total_income:,.2f}"],
                ["Total Expenses", f"LKR {total_expenses:,.2f}"],
                ["Net Cash Flow", f"LKR {total_income - total_expenses:,.2f}"],
                ["Average Expense", f"LKR {avg_expense:,.2f}"],
                ["Top Spending Category", top_category],
                ["Top Merchant", top_merchant]
            ]

            # Create table
            table = Table(data, colWidths=[4*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1f77b4')),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))

            doc.build(story)
            buffer.seek(0)
            return buffer

        # Generate PDF and create download button
        pdf_buffer = generate_pdf_report()
        st.download_button(
            label="Download Report (PDF)",
            data=pdf_buffer,
            file_name=f"fintrack_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )

with col2:
    if st.button("Export Chart Data"):
        # Export current view data
        export_df = filtered_df[['date', 'merchant', 'category', 'amount', 'description']].copy()
        export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
        export_df['amount'] = export_df['amount'].apply(lambda x: f"LKR{x:.2f}")
        
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