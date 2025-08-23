"""
Chart Components - Reusable chart components for the Streamlit application
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def spending_pie_chart(df, category_col='category', amount_col='amount_abs', title="Spending by Category"):
    """Create a pie chart showing spending distribution by category"""
    if df.empty:
        st.warning("No data available for chart")
        return
    
    category_spending = df.groupby(category_col)[amount_col].sum().sort_values(ascending=False)
    
    fig = px.pie(
        values=category_spending.values,
        names=category_spending.index,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=True, legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01))
    
    return fig

def monthly_trend_chart(df, date_col='date', amount_col='amount', title="Monthly Spending Trend"):
    """Create a line chart showing monthly spending trends"""
    if df.empty:
        st.warning("No data available for chart")
        return
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Separate income and expenses
    expenses_df = df[df[amount_col] < 0].copy()
    income_df = df[df[amount_col] >= 0].copy()
    
    expenses_df['amount_abs'] = abs(expenses_df[amount_col])
    income_df['amount_abs'] = income_df[amount_col]
    
    # Group by month
    monthly_expenses = expenses_df.groupby(expenses_df[date_col].dt.to_period('M'))['amount_abs'].sum()
    monthly_income = income_df.groupby(income_df[date_col].dt.to_period('M'))['amount_abs'].sum()
    
    fig = go.Figure()
    
    # Add expenses line
    fig.add_trace(go.Scatter(
        x=monthly_expenses.index.astype(str),
        y=monthly_expenses.values,
        mode='lines+markers',
        name='Expenses',
        line=dict(color='red', width=3),
        marker=dict(size=8)
    ))
    
    # Add income line if available
    if not monthly_income.empty:
        fig.add_trace(go.Scatter(
            x=monthly_income.index.astype(str),
            y=monthly_income.values,
            mode='lines+markers',
            name='Income',
            line=dict(color='green', width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        hovermode='x unified',
        showlegend=True
    )
    
    return fig

def top_merchants_chart(df, merchant_col='merchant', amount_col='amount_abs', top_n=10, title="Top Merchants by Spending"):
    """Create a horizontal bar chart showing top merchants"""
    if df.empty:
        st.warning("No data available for chart")
        return
    
    merchant_spending = df.groupby(merchant_col)[amount_col].sum().sort_values(ascending=False).head(top_n)
    
    fig = px.bar(
        x=merchant_spending.values,
        y=merchant_spending.index,
        orientation='h',
        title=title,
        labels={'x': 'Amount ($)', 'y': 'Merchant'},
        color=merchant_spending.values,
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False,
        coloraxis_showscale=False
    )
    
    return fig

def spending_heatmap(df, date_col='date', category_col='category', amount_col='amount_abs', title="Spending Heatmap"):
    """Create a heatmap showing spending patterns by category and time"""
    if df.empty:
        st.warning("No data available for chart")
        return
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df['month'] = df[date_col].dt.to_period('M')
    
    # Create pivot table
    heatmap_data = df.groupby(['month', category_col])[amount_col].sum().unstack(fill_value=0)
    
    fig = px.imshow(
        heatmap_data.T,
        title=title,
        labels=dict(x="Month", y="Category", color="Amount"),
        aspect="auto",
        color_continuous_scale="Reds"
    )
    
    return fig

def budget_comparison_chart(current_spending, recommended_spending, title="Budget vs Actual"):
    """Create a comparison chart between current and recommended spending"""
    categories = list(current_spending.keys())
    current_values = list(current_spending.values())
    recommended_values = list(recommended_spending.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Current Spending',
        x=categories,
        y=current_values,
        marker_color='lightcoral'
    ))
    
    fig.add_trace(go.Bar(
        name='Recommended Budget',
        x=categories,
        y=recommended_values,
        marker_color='lightblue'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Category",
        yaxis_title="Amount ($)",
        barmode='group',
        xaxis_tickangle=-45
    )
    
    return fig

def cash_flow_chart(df, date_col='date', amount_col='amount', title="Cash Flow Analysis"):
    """Create a cash flow chart showing income vs expenses over time"""
    if df.empty:
        st.warning("No data available for chart")
        return
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Group by date and sum amounts
    daily_flow = df.groupby(df[date_col].dt.date)[amount_col].sum()
    
    # Calculate cumulative cash flow
    cumulative_flow = daily_flow.cumsum()
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Daily Cash Flow', 'Cumulative Cash Flow'),
        vertical_spacing=0.1
    )
    
    # Daily cash flow
    colors = ['green' if x >= 0 else 'red' for x in daily_flow.values]
    fig.add_trace(
        go.Bar(x=daily_flow.index, y=daily_flow.values, marker_color=colors, name='Daily Flow'),
        row=1, col=1
    )
    
    # Cumulative cash flow
    fig.add_trace(
        go.Scatter(
            x=cumulative_flow.index, 
            y=cumulative_flow.values, 
            mode='lines+markers',
            line=dict(color='blue', width=2),
            name='Cumulative Flow'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=title,
        showlegend=False,
        height=600
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
    fig.update_yaxes(title_text="Cumulative Amount ($)", row=2, col=1)
    
    return fig

def transaction_distribution_chart(df, amount_col='amount_abs', bins=30, title="Transaction Amount Distribution"):
    """Create a histogram showing transaction amount distribution"""
    if df.empty:
        st.warning("No data available for chart")
        return
    
    fig = px.histogram(
        df,
        x=amount_col,
        title=title,
        nbins=bins,
        labels={'x': 'Amount ($)', 'y': 'Frequency'}
    )
    
    fig.update_traces(marker_color='lightblue', marker_line_color='black', marker_line_width=1)
    fig.update_layout(bargap=0.1)
    
    return fig

def spending_by_day_chart(df, date_col='date', amount_col='amount_abs', title="Spending by Day of Week"):
    """Create a bar chart showing spending patterns by day of the week"""
    if df.empty:
        st.warning("No data available for chart")
        return
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df['day_of_week'] = df[date_col].dt.day_name()
    
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_spending = df.groupby('day_of_week')[amount_col].sum().reindex(day_order, fill_value=0)
    
    fig = px.bar(
        x=daily_spending.index,
        y=daily_spending.values,
        title=title,
        labels={'x': 'Day of Week', 'y': 'Amount ($)'},
        color=daily_spending.values,
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    
    return fig

def forecasting_chart(historical_data, forecast_data, title="Spending Forecast"):
    """Create a chart showing historical data and forecast"""
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data.values,
        mode='lines',
        name='Historical',
        line=dict(color='blue', width=2)
    ))
    
    # Forecast data
    fig.add_trace(go.Scatter(
        x=forecast_data.index,
        y=forecast_data.values,
        mode='lines',
        name='Forecast',
        line=dict(color='red', dash='dash', width=2)
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        hovermode='x unified'
    )
    
    return fig

def metric_cards(metrics_dict, cols=4):
    """Display a set of metric cards in columns"""
    if not metrics_dict:
        return
    
    metrics_list = list(metrics_dict.items())
    rows = len(metrics_list) // cols + (1 if len(metrics_list) % cols > 0 else 0)
    
    for row in range(rows):
        columns = st.columns(cols)
        for col_idx in range(cols):
            metric_idx = row * cols + col_idx
            if metric_idx < len(metrics_list):
                key, value = metrics_list[metric_idx]
                with columns[col_idx]:
                    if isinstance(value, dict):
                        st.metric(
                            key, 
                            value.get('value', 'N/A'),
                            delta=value.get('delta'),
                            delta_color=value.get('delta_color', 'normal')
                        )
                    else:
                        st.metric(key, value)

def progress_chart(current_value, target_value, title="Progress"):
    """Create a progress indicator chart"""
    progress = min(current_value / target_value, 1.0) if target_value > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = current_value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': target_value},
        gauge = {
            'axis': {'range': [None, target_value * 1.2]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, target_value * 0.5], 'color': "lightgray"},
                {'range': [target_value * 0.5, target_value], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': target_value
            }
        }
    ))
    
    fig.update_layout(height=300)
    
    return fig

def create_comparison_table(data_dict, title="Comparison Table"):
    """Create a styled comparison table"""
    if not data_dict:
        return
    
    st.subheader(title)
    df = pd.DataFrame(data_dict)
    
    # Style the dataframe
    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: lightgreen' if v else '' for v in is_max]
    
    def highlight_min(s):
        is_min = s == s.min()
        return ['background-color: lightcoral' if v else '' for v in is_min]
    
    # Apply styling if numeric data
    if df.select_dtypes(include=[np.number]).columns.any():
        styled_df = df.style.apply(highlight_max, subset=df.select_dtypes(include=[np.number]).columns)
    else:
        styled_df = df
    
    st.dataframe(styled_df, use_container_width=True)

def anomaly_detection_chart(df, date_col='date', amount_col='amount_abs', threshold=2):
    """Create a chart highlighting anomalies in the data"""
    if df.empty:
        st.warning("No data available for chart")
        return
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Calculate z-scores
    mean_val = df[amount_col].mean()
    std_val = df[amount_col].std()
    df['z_score'] = np.abs((df[amount_col] - mean_val) / std_val)
    df['is_anomaly'] = df['z_score'] > threshold
    
    fig = px.scatter(
        df,
        x=date_col,
        y=amount_col,
        color='is_anomaly',
        title="Anomaly Detection in Transactions",
        labels={amount_col: 'Amount ($)', date_col: 'Date'},
        color_discrete_map={True: 'red', False: 'blue'},
        hover_data=['z_score']
    )
    
    fig.update_traces(marker=dict(size=8))
    
    return fig
