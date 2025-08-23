"""
Widget Components - Custom widgets and interactive components for the Streamlit application
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

def spending_gauge(current_spending, budget, title="Budget Progress", color_scheme="default"):
    """Create a gauge chart showing spending vs budget"""
    if budget <= 0:
        st.error("Budget must be greater than 0")
        return
    
    progress = min(current_spending / budget, 1.2)  # Allow up to 120% to show overspending
    
    # Color schemes
    color_schemes = {
        "default": {"good": "green", "warning": "yellow", "danger": "red"},
        "traffic": {"good": "#00ff00", "warning": "#ffff00", "danger": "#ff0000"},
        "blue": {"good": "#0066cc", "warning": "#ff9900", "danger": "#cc0000"}
    }
    
    colors = color_schemes.get(color_scheme, color_schemes["default"])
    
    # Determine color based on progress
    if progress <= 0.7:
        bar_color = colors["good"]
    elif progress <= 0.9:
        bar_color = colors["warning"]
    else:
        bar_color = colors["danger"]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_spending,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': budget, 'position': "top"},
        gauge={
            'axis': {'range': [None, budget * 1.2]},
            'bar': {'color': bar_color},
            'steps': [
                {'range': [0, budget * 0.7], 'color': "lightgray"},
                {'range': [budget * 0.7, budget * 0.9], 'color': "gray"},
                {'range': [budget * 0.9, budget], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': budget
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Status message
    if progress <= 0.7:
        st.success(f"On track! You've spent {progress:.1%} of your budget.")
    elif progress <= 0.9:
        st.warning(f"Getting close! You've spent {progress:.1%} of your budget.")
    elif progress <= 1.0:
        st.warning(f"Almost at limit! You've spent {progress:.1%} of your budget.")
    else:
        st.error(f"Over budget! You've spent {progress:.1%} of your budget.")

def category_toggle_buttons(categories, selected_categories=None, key_prefix="category"):
    """Create toggle buttons for category selection"""
    if selected_categories is None:
        selected_categories = categories.copy()
    
    st.markdown("#### Select Categories")
    
    # Create columns for buttons
    cols = st.columns(min(len(categories), 4))
    updated_selection = []
    
    for i, category in enumerate(categories):
        with cols[i % len(cols)]:
            is_selected = category in selected_categories
            if st.button(
                f"{'✅' if is_selected else '⬜'} {category}",
                key=f"{key_prefix}_{i}",
                use_container_width=True
            ):
                # Toggle selection
                if is_selected:
                    # Remove from selection
                    updated_selection = [c for c in selected_categories if c != category]
                else:
                    # Add to selection
                    updated_selection = selected_categories + [category]
                
                return updated_selection
    
    return selected_categories

def date_range_picker(default_days=30, key_suffix=""):
    """Create a date range picker with preset options"""
    st.markdown("#### 📅 Date Range")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        preset = st.selectbox(
            "Quick Select",
            options=["Custom", "Last 7 days", "Last 30 days", "Last 90 days", "This month", "Last month", "This year"],
            key=f"date_preset_{key_suffix}"
        )
    
    with col2:
        if preset == "Custom":
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=default_days)
        elif preset == "Last 7 days":
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
        elif preset == "Last 30 days":
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        elif preset == "Last 90 days":
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
        elif preset == "This month":
            end_date = datetime.now().date()
            start_date = end_date.replace(day=1)
        elif preset == "Last month":
            today = datetime.now().date()
            end_date = today.replace(day=1) - timedelta(days=1)
            start_date = end_date.replace(day=1)
        elif preset == "This year":
            end_date = datetime.now().date()
            start_date = end_date.replace(month=1, day=1)
        
        date_range = st.date_input(
            "Select range",
            value=(start_date, end_date),
            key=f"date_range_{key_suffix}"
        )
    
    return date_range

def spending_trend_indicator(current_period, previous_period, metric_name="Spending"):
    """Show spending trend with arrow indicators"""
    if previous_period == 0:
        change_pct = 0
        change_amount = current_period
    else:
        change_pct = ((current_period - previous_period) / previous_period) * 100
        change_amount = current_period - previous_period
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            f"Current {metric_name}",
            f"${current_period:,.2f}"
        )
    
    with col2:
        st.metric(
            f"Previous {metric_name}",
            f"${previous_period:,.2f}"
        )
    
    with col3:
        # Determine trend
        if change_pct > 5:
            trend_icon = "📈"
            trend_color = "error"
        elif change_pct < -5:
            trend_icon = "📉"
            trend_color = "normal"
        else:
            trend_icon = "➡️"
            trend_color = "off"
        
        st.metric(
            "Change",
            f"{change_pct:+.1f}%",
            delta=f"${change_amount:+,.2f}",
            delta_color=trend_color
        )
        
        st.write(f"{trend_icon} Trend")

def interactive_budget_slider(categories_budget, key_suffix=""):
    """Interactive budget allocation slider"""
    st.markdown("#### 💰 Budget Allocation")
    
    total_budget = sum(categories_budget.values())
    updated_budget = {}
    
    # Show total budget input
    new_total = st.number_input(
        "Total Monthly Budget",
        min_value=0.0,
        value=total_budget,
        step=50.0,
        key=f"total_budget_{key_suffix}"
    )
    
    # If total changed, scale all categories proportionally
    if new_total != total_budget and total_budget > 0:
        scale_factor = new_total / total_budget
        categories_budget = {cat: amount * scale_factor for cat, amount in categories_budget.items()}
        total_budget = new_total
    
    st.markdown("**Adjust category budgets:**")
    
    for category, current_amount in categories_budget.items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            max_amount = total_budget * 0.5  # Max 50% of total budget per category
            new_amount = st.slider(
                category,
                min_value=0.0,
                max_value=max_amount,
                value=current_amount,
                step=10.0,
                key=f"budget_slider_{category}_{key_suffix}"
            )
            updated_budget[category] = new_amount
        
        with col2:
            percentage = (new_amount / total_budget * 100) if total_budget > 0 else 0
            st.write(f"{percentage:.1f}%")
    
    # Show allocation summary
    allocated_total = sum(updated_budget.values())
    remaining = total_budget - allocated_total
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Budget", f"${total_budget:,.2f}")
    
    with col2:
        st.metric("Allocated", f"${allocated_total:,.2f}")
    
    with col3:
        color = "normal" if remaining >= 0 else "inverse"
        st.metric("Remaining", f"${remaining:,.2f}", delta_color=color)
    
    if remaining < 0:
        st.error(f"⚠️ Over-allocated by ${abs(remaining):,.2f}")
    elif remaining > total_budget * 0.1:
        st.warning(f"💡 You have ${remaining:,.2f} unallocated")
    
    return updated_budget

def transaction_search_widget(df, key_suffix=""):
    """Advanced search widget for transactions"""
    if df.empty:
        return df
    
    st.markdown("#### 🔍 Search Transactions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Text search
        search_text = st.text_input(
            "Search in descriptions",
            placeholder="Enter keywords...",
            key=f"search_text_{key_suffix}"
        )
        
        # Amount filter
        if 'amount' in df.columns:
            amount_filter = st.selectbox(
                "Amount filter",
                options=["All", "Expenses only", "Income only", "Above $100", "Below $10"],
                key=f"amount_filter_{key_suffix}"
            )
    
    with col2:
        # Category filter
        if 'category' in df.columns:
            categories = ['All'] + sorted(df['category'].dropna().unique().tolist())
            selected_category = st.selectbox(
                "Category",
                options=categories,
                key=f"category_filter_{key_suffix}"
            )
        
        # Date filter
        if 'date' in df.columns:
            date_filter = st.selectbox(
                "Date filter",
                options=["All time", "Last 7 days", "Last 30 days", "This month"],
                key=f"date_filter_{key_suffix}"
            )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Text search
    if search_text and 'description' in df.columns:
        filtered_df = filtered_df[
            filtered_df['description'].str.contains(search_text, case=False, na=False)
        ]
    
    # Amount filter
    if 'amount' in df.columns:
        if amount_filter == "Expenses only":
            filtered_df = filtered_df[filtered_df['amount'] < 0]
        elif amount_filter == "Income only":
            filtered_df = filtered_df[filtered_df['amount'] > 0]
        elif amount_filter == "Above $100":
            filtered_df = filtered_df[abs(filtered_df['amount']) > 100]
        elif amount_filter == "Below $10":
            filtered_df = filtered_df[abs(filtered_df['amount']) < 10]
    
    # Category filter
    if 'category' in df.columns and selected_category != "All":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    # Date filter
    if 'date' in df.columns and date_filter != "All time":
        df_copy = filtered_df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        
        if date_filter == "Last 7 days":
            cutoff_date = datetime.now() - timedelta(days=7)
            filtered_df = df_copy[df_copy['date'] >= cutoff_date]
        elif date_filter == "Last 30 days":
            cutoff_date = datetime.now() - timedelta(days=30)
            filtered_df = df_copy[df_copy['date'] >= cutoff_date]
        elif date_filter == "This month":
            current_month = datetime.now().month
            current_year = datetime.now().year
            filtered_df = df_copy[
                (df_copy['date'].dt.month == current_month) &
                (df_copy['date'].dt.year == current_year)
            ]
    
    # Show results summary
    if len(filtered_df) < len(df):
        st.info(f"🔍 Showing {len(filtered_df)} of {len(df)} transactions")
    
    return filtered_df

def savings_goal_widget(current_amount, target_amount, target_date, goal_name="Savings Goal"):
    """Display a savings goal progress widget"""
    progress = min(current_amount / target_amount, 1.0) if target_amount > 0 else 0
    remaining_amount = max(target_amount - current_amount, 0)
    
    # Calculate time remaining
    days_remaining = (target_date - datetime.now().date()).days if target_date > datetime.now().date() else 0
    
    st.markdown(f"#### 🎯 {goal_name}")
    
    # Progress bar
    st.progress(progress)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current", f"${current_amount:,.2f}")
    
    with col2:
        st.metric("Target", f"${target_amount:,.2f}")
    
    with col3:
        st.metric("Remaining", f"${remaining_amount:,.2f}")
    
    # Time and savings rate info
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"📅 **Target Date:** {target_date.strftime('%B %d, %Y')}")
        st.write(f"⏰ **Days Remaining:** {days_remaining}")
    
    with col2:
        if days_remaining > 0 and remaining_amount > 0:
            daily_savings_needed = remaining_amount / days_remaining
            monthly_savings_needed = daily_savings_needed * 30.44
            st.write(f"💰 **Daily savings needed:** ${daily_savings_needed:.2f}")
            st.write(f"💰 **Monthly savings needed:** ${monthly_savings_needed:.2f}")
        else:
            st.write("🎉 **Goal achieved!**" if progress >= 1.0 else "⏰ **Goal overdue**")

def notification_center(notifications=None):
    """Display a notification center widget"""
    if not notifications:
        notifications = []
    
    st.markdown("#### 🔔 Notifications")
    
    if not notifications:
        st.info("📭 No new notifications")
        return
    
    # Group notifications by type
    notification_types = {}
    for notification in notifications:
        notif_type = notification.get('type', 'info')
        if notif_type not in notification_types:
            notification_types[notif_type] = []
        notification_types[notif_type].append(notification)
    
    # Display notifications by type
    type_icons = {
        'alert': '🚨',
        'warning': '⚠️',
        'info': 'ℹ️',
        'success': '✅'
    }
    
    for notif_type, notifs in notification_types.items():
        with st.expander(f"{type_icons.get(notif_type, '📢')} {notif_type.title()} ({len(notifs)})"):
            for notif in notifs:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"**{notif.get('title', 'Notification')}**")
                    st.write(notif.get('message', ''))
                    st.caption(notif.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M')))
                
                with col2:
                    if st.button("❌", key=f"dismiss_{notif.get('id', hash(notif.get('message', '')))}"):
                        # In a real app, this would dismiss the notification
                        st.success("Dismissed!")

def quick_stats_widget(df):
    """Display quick statistics widget"""
    if df.empty:
        st.warning("No data for statistics")
        return
    
    st.markdown("#### ⚡ Quick Stats")
    
    stats = {}
    
    if 'amount' in df.columns:
        expenses = df[df['amount'] < 0]
        income = df[df['amount'] > 0]
        
        stats.update({
            "Total Transactions": len(df),
            "Total Expenses": f"${abs(expenses['amount'].sum()):,.2f}",
            "Total Income": f"${income['amount'].sum():,.2f}",
            "Average Transaction": f"${df['amount'].abs().mean():,.2f}"
        })
    
    if 'date' in df.columns:
        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        date_range = df_copy['date'].max() - df_copy['date'].min()
        stats["Date Range"] = f"{date_range.days} days"
    
    # Display in grid
    cols = st.columns(len(stats))
    for i, (key, value) in enumerate(stats.items()):
        with cols[i]:
            st.metric(key, value)

def trend_indicator_widget(value, previous_value, label="Metric", format_type="currency"):
    """Display a trend indicator widget"""
    if previous_value == 0:
        change_pct = 0
    else:
        change_pct = ((value - previous_value) / previous_value) * 100
    
    # Format value based on type
    if format_type == "currency":
        formatted_value = f"${value:,.2f}"
        formatted_change = f"${value - previous_value:+,.2f}"
    elif format_type == "percentage":
        formatted_value = f"{value:.1f}%"
        formatted_change = f"{value - previous_value:+.1f}pp"
    else:
        formatted_value = f"{value:,.0f}"
        formatted_change = f"{value - previous_value:+,.0f}"
    
    # Determine trend direction
    if change_pct > 0:
        trend_icon = "📈"
        trend_color = "normal"
    elif change_pct < 0:
        trend_icon = "📉"
        trend_color = "inverse"
    else:
        trend_icon = "➡️"
        trend_color = "off"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.metric(
            label,
            formatted_value,
            delta=formatted_change,
            delta_color=trend_color
        )
    
    with col2:
        st.write(trend_icon)
        st.caption(f"{change_pct:+.1f}%")
