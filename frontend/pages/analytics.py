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

# Use string format for month to avoid Period serialization issues
df['month'] = df['date'].dt.strftime('%Y-%m')
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
        st.metric(
            "Total Expenses",
            format_currency(total_expenses, show_full_on_hover=False),
            delta=f"{expense_count} tx | {total_expenses:,.2f}",
            delta_color="normal"
        )
    
    with col2:
        total_income = filtered_df[filtered_df['is_income']]['amount_abs'].sum()
        income_count = len(filtered_df[filtered_df['is_income']])
        st.metric(
            "Total Income",
            format_currency(total_income, show_full_on_hover=False),
            delta=f"{income_count} tx | {total_income:,.2f}",
            delta_color="normal"
        )
    
    with col3:
        net_flow = total_income - total_expenses
        net_percentage = (net_flow / total_income * 100) if total_income > 0 else 0
        st.metric(
            "Net Cash Flow",
            format_currency(net_flow, show_full_on_hover=False),
            delta=f"{net_percentage:+.1f}% | {net_flow:,.2f}",
            delta_color="normal"
        )
    
    with col4:
        avg_expense = filtered_df[filtered_df['is_expense']]['amount_abs'].mean() if not filtered_df[filtered_df['is_expense']].empty else 0
        avg_income = filtered_df[filtered_df['is_income']]['amount_abs'].mean() if not filtered_df[filtered_df['is_income']].empty else 0
        st.metric(
            "Avg Expense",
            format_currency(avg_expense, show_full_on_hover=False),
            delta=f"{avg_expense:,.2f}",
            delta_color="normal"
        )
        st.metric(
            "Avg Income",
            format_currency(avg_income, show_full_on_hover=False),
            delta=f"{avg_income:,.2f}",
            delta_color="normal"
        )
    
    with col5:
        transaction_count = len(filtered_df)
        expense_ratio = expense_count / transaction_count * 100 if transaction_count > 0 else 0
        st.metric("Total Transactions", f"{transaction_count:,}")
        st.write(f"{expense_ratio:.1f}% Expenses")

    
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
        fig_comparison.update_traces(texttemplate='LKR%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig_comparison, use_container_width=True)
    
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
        
        # Ensure we have data for all months
        full_month_data = pd.Series(index=range(1, 13), data=0.0)  # Initialize with zeros
        full_month_data.update(monthly_avg)  # Update with actual values
        
        # Create proper DataFrame for plotting
        seasonal_df = pd.DataFrame({
            'Month': month_names,
            'Average Spending': full_month_data.values
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
        
        # Ensure we have data for all days of the week
        full_week_data = pd.Series(index=range(7), data=0.0)  # Initialize with zeros
        full_week_data.update(weekly_avg)  # Update with actual values
        
        # Create DataFrame for weekly plot
        weekly_df = pd.DataFrame({
            'Day': weekday_names,
            'Average Spending': full_week_data.values
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
            # Calculate confidence based on data quality and trend stability
            data_points = len(daily_spending)
            trend_variance = daily_spending.std() / daily_spending.mean() if daily_spending.mean() > 0 else 1.0
            
            # Base confidence from data availability (more data = higher confidence)
            data_confidence = min(data_points / 30, 1.0)  # Max confidence with 30+ days
            
            # Adjust for trend stability (lower variance = higher confidence)
            stability_confidence = max(0.5, 1.0 - min(trend_variance, 0.5))
            
            # Combined confidence score
            confidence = (data_confidence + stability_confidence) / 2
            confidence = max(0.4, min(0.95, confidence))  # Clamp between 40% and 95%
            
            st.metric("Forecast Confidence", f"{confidence:.1%}")

# AI Insights Section
if show_ai_insights:
    st.subheader("🤖 AI-Generated Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Key Findings")
        
        # Import insights generator
        from components.insights_generator import generate_insights
        
        # Generate dynamic insights based on analysis type
        insights = generate_insights(df, analysis_type, filtered_df)
        
        # Display insights with appropriate severity indicators
        for insight in insights:
            if insight["severity"] == "warning":
                st.warning(insight["message"])
            elif insight["severity"] == "error":
                st.error(insight["message"])
            elif insight["severity"] == "success":
                st.success(insight["message"])
            else:
                st.info(insight["message"])  # Single info call to avoid duplication
    
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
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#2c3e50')
            )
            subheading_style = ParagraphStyle(
                'CustomSubheading',
                parent=styles['Heading3'],
                fontSize=14,
                spaceAfter=8,
                textColor=colors.HexColor('#34495e')
            )

            # Title
            story.append(Paragraph("FinTrack Analytics Report", title_style))
            story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles["Italic"]))
            story.append(Spacer(1, 20))

            # Report metadata
            story.append(Paragraph(f"Analysis Type: {analysis_type}", heading_style))
            if len(date_range) == 2:
                story.append(Paragraph(f"Date Range: {date_range[0]} to {date_range[1]}", styles["Normal"]))
            story.append(Paragraph(f"Amount Range: LKR {amount_range[0]:,.2f} to LKR {amount_range[1]:,.2f}", styles["Normal"]))
            story.append(Paragraph(f"Categories: {', '.join(selected_categories)}", styles["Normal"]))
            story.append(Spacer(1, 20))

            # Common metrics for all reports
            total_expenses = filtered_df[filtered_df['is_expense']]['amount_abs'].sum() if not filtered_df[filtered_df['is_expense']].empty else 0
            total_income = filtered_df[~filtered_df['is_expense']]['amount_abs'].sum() if not filtered_df[~filtered_df['is_expense']].empty else 0
            transaction_count = len(filtered_df)
            
            # Analysis type specific content
            if analysis_type == "Overview":
                # Overview specific content
                story.append(Paragraph("Financial Overview Summary", heading_style))
                
                avg_expense = filtered_df[filtered_df['is_expense']]['amount_abs'].mean() if not filtered_df[filtered_df['is_expense']].empty else 0
                top_category = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].sum().idxmax() if not filtered_df[filtered_df['is_expense']].empty else "N/A"
                top_merchant = filtered_df[filtered_df['is_expense']].groupby('merchant')['amount_abs'].sum().idxmax() if not filtered_df[filtered_df['is_expense']].empty else "N/A"
                net_flow = total_income - total_expenses
                savings_rate = (net_flow / total_income * 100) if total_income > 0 else 0

                overview_data = [
                    ["Metric", "Value"],
                    ["Total Transactions", f"{transaction_count:,}"],
                    ["Total Income", f"LKR {total_income:,.2f}"],
                    ["Total Expenses", f"LKR {total_expenses:,.2f}"],
                    ["Net Cash Flow", f"LKR {net_flow:,.2f}"],
                    ["Savings Rate", f"{savings_rate:.1f}%"],
                    ["Average Expense", f"LKR {avg_expense:,.2f}"],
                    ["Top Spending Category", top_category],
                    ["Top Merchant", top_merchant]
                ]
                
            elif analysis_type == "Spending Patterns":
                # Spending Patterns specific content
                story.append(Paragraph("Spending Pattern Analysis", heading_style))
                
                # Day of week analysis
                dow_spending = filtered_df[filtered_df['is_expense']].groupby('day_of_week')['amount_abs'].sum()
                dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                dow_spending = dow_spending.reindex(dow_order, fill_value=0)
                
                highest_spending_day = dow_spending.idxmax() if not dow_spending.empty else "N/A"
                lowest_spending_day = dow_spending.idxmin() if not dow_spending.empty else "N/A"
                
                # Category distribution
                category_spending = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].sum().sort_values(ascending=False)
                top_3_categories = category_spending.head(3)
                
                patterns_data = [
                    ["Pattern Metric", "Value"],
                    ["Total Transactions Analyzed", f"{transaction_count:,}"],
                    ["Highest Spending Day", f"{highest_spending_day} (LKR {dow_spending.max():,.2f})"],
                    ["Lowest Spending Day", f"{lowest_spending_day} (LKR {dow_spending.min():,.2f})"],
                    ["Top Category", f"{top_3_categories.index[0]} (LKR {top_3_categories.iloc[0]:,.2f})"],
                    ["Weekend vs Weekday Ratio", f"{(dow_spending[['Saturday', 'Sunday']].sum() / dow_spending[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']].sum() * 100):.1f}%"],
                ]
                
                # Add day-of-week breakdown
                story.append(Paragraph("Daily Spending Breakdown", subheading_style))
                dow_data = [["Day", "Total Spending", "Avg per Transaction"]]
                for day in dow_order:
                    day_total = dow_spending.get(day, 0)
                    day_count = len(filtered_df[(filtered_df['is_expense']) & (filtered_df['day_of_week'] == day)])
                    day_avg = day_total / day_count if day_count > 0 else 0
                    dow_data.append([day, f"LKR {day_total:,.2f}", f"LKR {day_avg:,.2f}"])
                
                overview_data = patterns_data
                
            elif analysis_type == "Trend Analysis":
                # Trend Analysis specific content
                story.append(Paragraph("Financial Trend Analysis", heading_style))
                
                # Calculate daily trends
                daily_spending = filtered_df[filtered_df['is_expense']].groupby('date')['amount_abs'].sum()
                if not daily_spending.empty:
                    daily_spending = daily_spending.sort_index()
                    trend_direction = "Increasing" if daily_spending.iloc[-1] > daily_spending.iloc[0] else "Decreasing"
                    trend_change = ((daily_spending.iloc[-1] - daily_spending.iloc[0]) / daily_spending.iloc[0] * 100) if daily_spending.iloc[0] > 0 else 0
                    avg_daily = daily_spending.mean()
                    volatility = daily_spending.std() / avg_daily * 100 if avg_daily > 0 else 0
                else:
                    trend_direction = "Stable"
                    trend_change = 0
                    avg_daily = 0
                    volatility = 0
                
                # Monthly patterns
                monthly_avg = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.month)['amount_abs'].mean()
                highest_month = monthly_avg.idxmax() if not monthly_avg.empty else "N/A"
                lowest_month = monthly_avg.idxmin() if not monthly_avg.empty else "N/A"
                month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
                             7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
                
                trends_data = [
                    ["Trend Metric", "Value"],
                    ["Overall Trend Direction", trend_direction],
                    ["Period Change", f"{trend_change:+.1f}%"],
                    ["Average Daily Spending", f"LKR {avg_daily:,.2f}"],
                    ["Spending Volatility", f"{volatility:.1f}%"],
                    ["Highest Spending Month", f"{month_names.get(highest_month, 'N/A')}"],
                    ["Lowest Spending Month", f"{month_names.get(lowest_month, 'N/A')}"],
                    ["Analysis Period (Days)", f"{(date_range[1] - date_range[0]).days if len(date_range) == 2 else 'Full Period'}"]
                ]
                
                overview_data = trends_data
                
            elif analysis_type == "Merchant Analysis":
                # Merchant Analysis specific content
                story.append(Paragraph("Merchant Spending Analysis", heading_style))
                
                # Merchant summary calculations
                merchant_summary = filtered_df[filtered_df['is_expense']].groupby('merchant').agg({
                    'amount_abs': ['sum', 'mean', 'count'],
                    'date': ['min', 'max']
                })
                merchant_summary.columns = ['total_spent', 'avg_transaction', 'transaction_count', 'first_visit', 'last_visit']
                merchant_summary = merchant_summary.sort_values('total_spent', ascending=False)
                
                top_merchant = merchant_summary.index[0] if not merchant_summary.empty else "N/A"
                merchant_count = len(merchant_summary)
                avg_merchant_spending = merchant_summary['total_spent'].mean() if not merchant_summary.empty else 0
                
                merchant_data = [
                    ["Merchant Metric", "Value"],
                    ["Total Unique Merchants", f"{merchant_count:,}"],
                    ["Top Spending Merchant", f"{top_merchant}"],
                    ["Top Merchant Amount", f"LKR {merchant_summary['total_spent'].iloc[0]:,.2f}" if not merchant_summary.empty else "LKR 0.00"],
                    ["Average per Merchant", f"LKR {avg_merchant_spending:,.2f}"],
                    ["Most Frequent Merchant", f"{merchant_summary.sort_values('transaction_count', ascending=False).index[0]}" if not merchant_summary.empty else "N/A"],
                    ["Merchant Diversity", f"{merchant_count} unique merchants"]
                ]
                
                # Add top 10 merchants table
                story.append(Paragraph("Top 10 Merchants by Spending", subheading_style))
                top_merchants_data = [["Rank", "Merchant", "Total Spent", "Avg Transaction", "Visit Count"]]
                for i, (merchant, data) in enumerate(merchant_summary.head(10).iterrows(), 1):
                    top_merchants_data.append([
                        str(i),
                        str(merchant)[:25] + "..." if len(str(merchant)) > 25 else str(merchant),
                        f"LKR {data['total_spent']:,.2f}",
                        f"LKR {data['avg_transaction']:,.2f}",
                        f"{data['transaction_count']:,}"
                    ])
                
                overview_data = merchant_data
                
            elif analysis_type == "Predictive Analytics":
                # Predictive Analytics specific content
                story.append(Paragraph("Predictive Financial Analysis", heading_style))
                
                # Calculate forecast data
                daily_spending = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.date)['amount_abs'].sum()
                if not daily_spending.empty:
                    recent_trend = daily_spending.tail(30).mean()
                    historical_avg = daily_spending.mean()
                    trend_change = ((recent_trend - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0
                    
                    # Forecast calculations
                    forecast_30_days = recent_trend * 30
                    current_monthly = daily_spending.tail(30).sum() if len(daily_spending) >= 30 else daily_spending.sum()
                    predicted_change = ((forecast_30_days - current_monthly) / current_monthly * 100) if current_monthly > 0 else 0
                    
                    # Calculate confidence based on data quality and trend stability
                    data_points = len(daily_spending)
                    trend_variance = daily_spending.std() / daily_spending.mean() if daily_spending.mean() > 0 else 1.0
                    data_confidence = min(data_points / 30, 1.0)
                    stability_confidence = max(0.5, 1.0 - min(trend_variance, 0.5))
                    forecast_confidence = (data_confidence + stability_confidence) / 2
                    forecast_confidence = max(0.4, min(0.95, forecast_confidence))
                else:
                    recent_trend = 0
                    forecast_30_days = 0
                    predicted_change = 0
                    forecast_confidence = 0.5
                    trend_change = 0
                
                # Calculate forecast methodology description based on actual data
                methodology_line1 = "Linear trend projection"
                methodology_line2 = "confidence weighted"
                if len(daily_spending) < 10:
                    methodology_line1 = "Simple averaging"
                    methodology_line2 = "limited data available"
                elif trend_variance > 0.5:
                    methodology_line1 = "Robust trend projection"
                    methodology_line2 = "variance adjusted"
                
                predictive_data = [
                    ["Predictive Metric", "Value"],
                    ["Historical Daily Average", f"LKR {daily_spending.mean() if not daily_spending.empty else 0:,.2f}"],
                    ["Recent Trend (30 days)", f"LKR {recent_trend:,.2f}/day"],
                    ["Trend Direction", f"{'Increasing' if trend_change > 0 else 'Decreasing' if trend_change < 0 else 'Stable'}"],
                    ["30-Day Forecast", f"LKR {forecast_30_days:,.2f}"],
                    ["Predicted Monthly Change", f"{predicted_change:+.1f}%"],
                    ["Forecast Confidence", f"{forecast_confidence:.1%}"],
                    ["Data Points Used", f"{len(daily_spending) if not daily_spending.empty else 0} days"]
                ]
                
                overview_data = predictive_data
            
            else:
                # Default overview for other analysis types
                story.append(Paragraph("General Analytics Summary", heading_style))
                
                avg_expense = filtered_df[filtered_df['is_expense']]['amount_abs'].mean() if not filtered_df[filtered_df['is_expense']].empty else 0
                top_category = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].sum().idxmax() if not filtered_df[filtered_df['is_expense']].empty else "N/A"
                
                overview_data = [
                    ["Metric", "Value"],
                    ["Transactions", f"{transaction_count:,}"],
                    ["Total Income", f"LKR {total_income:,.2f}"],
                    ["Total Expenses", f"LKR {total_expenses:,.2f}"],
                    ["Net Cash Flow", f"LKR {total_income - total_expenses:,.2f}"],
                    ["Average Expense", f"LKR {avg_expense:,.2f}"],
                    ["Top Spending Category", top_category]
                ]

            # Create main metrics table
            table = Table(overview_data, colWidths=[4*inch, 3*inch])
            table_style = TableStyle([
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
            ])
            
            table.setStyle(table_style)
            
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Add analysis-specific detailed sections
            if analysis_type == "Spending Patterns" and 'dow_data' in locals():
                story.append(Paragraph("Daily Spending Breakdown", subheading_style))
                dow_table = Table(dow_data, colWidths=[2*inch, 2.5*inch, 2.5*inch])
                dow_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(dow_table)
                story.append(Spacer(1, 15))
                
            elif analysis_type == "Merchant Analysis" and 'top_merchants_data' in locals():
                story.append(Paragraph("Top 10 Merchants Detail", subheading_style))
                merchants_table = Table(top_merchants_data, colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
                merchants_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(merchants_table)
                story.append(Spacer(1, 15))

            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph("Generated by FinTrack Analytics System", styles["Normal"]))
            story.append(Paragraph(f"Report ID: {datetime.now().strftime('%Y%m%d_%H%M%S')}", styles["Italic"]))

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