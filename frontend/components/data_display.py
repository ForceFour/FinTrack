"""
Data Display Components - Reusable data display components for the Streamlit application
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

def transaction_table(df, columns=None, max_rows=100, title="Transactions"):
    """Display a formatted transaction table with optional filtering"""
    if df.empty:
        st.info("No transactions to display")
        return
    
    st.subheader(title)
    
    # Default columns if not specified
    if columns is None:
        columns = ['date', 'amount', 'description', 'category', 'merchant']
    
    # Filter columns that exist in the dataframe
    available_columns = [col for col in columns if col in df.columns]
    display_df = df[available_columns].copy()
    
    # Format columns for better display
    if 'date' in display_df.columns:
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
    
    if 'amount' in display_df.columns:
        display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:.2f}")
    
    # Limit rows
    if len(display_df) > max_rows:
        st.warning(f"Showing first {max_rows} rows of {len(display_df)} total transactions")
        display_df = display_df.head(max_rows)
    
    # Display with styling
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    return display_df

def summary_stats_card(df, title="Summary Statistics"):
    """Display summary statistics in a card format"""
    if df.empty:
        st.warning("No data available for summary")
        return
    
    st.subheader(title)
    
    # Calculate statistics
    stats = {}
    
    if 'amount' in df.columns:
        expenses = df[df['amount'] < 0]['amount']
        income = df[df['amount'] > 0]['amount']
        
        stats.update({
            'Total Transactions': len(df),
            'Total Expenses': f"${abs(expenses.sum()):,.2f}" if not expenses.empty else "$0.00",
            'Total Income': f"${income.sum():,.2f}" if not income.empty else "$0.00",
            'Average Expense': f"${abs(expenses.mean()):,.2f}" if not expenses.empty else "$0.00",
            'Largest Expense': f"${abs(expenses.min()):,.2f}" if not expenses.empty else "$0.00"
        })
    
    if 'category' in df.columns:
        stats['Unique Categories'] = df['category'].nunique()
    
    if 'merchant' in df.columns:
        stats['Unique Merchants'] = df['merchant'].nunique()
    
    if 'date' in df.columns:
        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        date_range = df_copy['date'].max() - df_copy['date'].min()
        stats['Date Range'] = f"{date_range.days} days"
    
    # Display stats in columns
    cols = st.columns(len(stats))
    for i, (key, value) in enumerate(stats.items()):
        with cols[i % len(cols)]:
            st.metric(key, value)

def category_breakdown_table(df, amount_col='amount', category_col='category'):
    """Display a breakdown of spending by category"""
    if df.empty or category_col not in df.columns or amount_col not in df.columns:
        st.warning("Cannot create category breakdown - missing data")
        return
    
    # Filter to expenses only
    expenses_df = df[df[amount_col] < 0].copy()
    if expenses_df.empty:
        st.info("No expense transactions found")
        return
    
    expenses_df['amount_abs'] = abs(expenses_df[amount_col])
    
    # Calculate category statistics
    category_stats = expenses_df.groupby(category_col).agg({
        'amount_abs': ['sum', 'mean', 'count', 'min', 'max']
    }).round(2)
    
    category_stats.columns = ['Total Spent', 'Average', 'Count', 'Minimum', 'Maximum']
    category_stats = category_stats.sort_values('Total Spent', ascending=False)
    
    # Add percentage
    total_spending = category_stats['Total Spent'].sum()
    category_stats['Percentage'] = (category_stats['Total Spent'] / total_spending * 100).round(1)
    
    # Format currency columns
    currency_cols = ['Total Spent', 'Average', 'Minimum', 'Maximum']
    for col in currency_cols:
        category_stats[col] = category_stats[col].apply(lambda x: f"${x:,.2f}")
    
    category_stats['Percentage'] = category_stats['Percentage'].apply(lambda x: f"{x}%")
    
    st.subheader("📊 Category Breakdown")
    st.dataframe(category_stats, use_container_width=True)
    
    return category_stats

def merchant_analysis_table(df, amount_col='amount', merchant_col='merchant', top_n=20):
    """Display merchant analysis table"""
    if df.empty or merchant_col not in df.columns or amount_col not in df.columns:
        st.warning("Cannot create merchant analysis - missing data")
        return
    
    # Filter to expenses only
    expenses_df = df[df[amount_col] < 0].copy()
    if expenses_df.empty:
        st.info("No expense transactions found")
        return
    
    expenses_df['amount_abs'] = abs(expenses_df[amount_col])
    
    # Calculate merchant statistics
    merchant_stats = expenses_df.groupby(merchant_col).agg({
        'amount_abs': ['sum', 'mean', 'count'],
        'date': ['min', 'max'] if 'date' in df.columns else ['count', 'count']
    }).round(2)
    
    if 'date' in df.columns:
        merchant_stats.columns = ['Total Spent', 'Average', 'Visits', 'First Visit', 'Last Visit']
    else:
        merchant_stats.columns = ['Total Spent', 'Average', 'Visits', 'First', 'Last']
        merchant_stats = merchant_stats.drop(['First', 'Last'], axis=1)
    
    merchant_stats = merchant_stats.sort_values('Total Spent', ascending=False).head(top_n)
    
    # Format currency columns
    merchant_stats['Total Spent'] = merchant_stats['Total Spent'].apply(lambda x: f"${x:,.2f}")
    merchant_stats['Average'] = merchant_stats['Average'].apply(lambda x: f"${x:.2f}")
    
    # Format date columns if they exist
    if 'First Visit' in merchant_stats.columns:
        merchant_stats['First Visit'] = pd.to_datetime(merchant_stats['First Visit']).dt.strftime('%Y-%m-%d')
        merchant_stats['Last Visit'] = pd.to_datetime(merchant_stats['Last Visit']).dt.strftime('%Y-%m-%d')
    
    st.subheader(f"🏪 Top {top_n} Merchants")
    st.dataframe(merchant_stats, use_container_width=True)
    
    return merchant_stats

def alert_banner(message, alert_type="info", icon=None):
    """Display an alert banner with custom styling"""
    icons = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    }
    
    display_icon = icon or icons.get(alert_type, 'ℹ️')
    
    if alert_type == "success":
        st.success(f"{display_icon} {message}")
    elif alert_type == "warning":
        st.warning(f"{display_icon} {message}")
    elif alert_type == "error":
        st.error(f"{display_icon} {message}")
    else:
        st.info(f"{display_icon} {message}")

def progress_indicator(current, target, label="Progress", format_func=None):
    """Display a progress indicator with current/target values"""
    if target <= 0:
        st.error("Target must be greater than 0")
        return
    
    progress = min(current / target, 1.0)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.progress(progress)
        st.caption(f"{label}: {progress:.1%} complete")
    
    with col2:
        if format_func:
            st.metric("Current", format_func(current))
        else:
            st.metric("Current", f"{current:,.2f}")
    
    with col3:
        if format_func:
            st.metric("Target", format_func(target))
        else:
            st.metric("Target", f"{target:,.2f}")

def data_quality_indicator(df, required_columns=None):
    """Display data quality metrics"""
    if df.empty:
        st.error("❌ No data available")
        return
    
    st.subheader("📊 Data Quality")
    
    quality_metrics = {
        'Total Records': len(df),
        'Complete Records': len(df.dropna()),
        'Completeness': f"{(len(df.dropna()) / len(df) * 100):.1f}%"
    }
    
    # Check required columns
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        quality_metrics['Missing Required Columns'] = len(missing_columns)
        
        if missing_columns:
            st.warning(f"⚠️ Missing required columns: {', '.join(missing_columns)}")
    
    # Check for duplicates
    duplicates = df.duplicated().sum()
    quality_metrics['Duplicate Records'] = duplicates
    
    # Display metrics
    cols = st.columns(len(quality_metrics))
    for i, (key, value) in enumerate(quality_metrics.items()):
        with cols[i]:
            if key == 'Duplicate Records' and value > 0:
                st.metric(key, value, delta=value, delta_color="inverse")
            else:
                st.metric(key, value)

def expandable_transaction_details(df, transaction_id_col='id', max_details=50):
    """Display expandable transaction details"""
    if df.empty:
        st.info("No transactions to display")
        return
    
    st.subheader("🔍 Transaction Details")
    
    # Limit the number of expandable items
    display_df = df.head(max_details)
    
    for idx, row in display_df.iterrows():
        # Create a summary for the expander
        if 'date' in row:
            date_str = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
        else:
            date_str = "Unknown Date"
        
        if 'amount' in row:
            amount_str = f"${abs(row['amount']):.2f}"
        else:
            amount_str = "Unknown Amount"
        
        if 'description' in row:
            desc_str = str(row['description'])[:50] + "..." if len(str(row['description'])) > 50 else str(row['description'])
        else:
            desc_str = "No Description"
        
        summary = f"{date_str} - {amount_str} - {desc_str}"
        
        with st.expander(summary):
            # Display all available fields
            for col, value in row.items():
                if pd.notna(value):
                    st.write(f"**{col.title()}:** {value}")

def financial_health_score(df, savings_rate=0.1, debt_ratio=0.3):
    """Calculate and display a financial health score"""
    if df.empty:
        st.warning("Cannot calculate financial health score - no data")
        return
    
    score_components = {}
    total_score = 0
    max_score = 0
    
    # Income vs Expenses (30 points)
    if 'amount' in df.columns:
        total_income = df[df['amount'] > 0]['amount'].sum()
        total_expenses = abs(df[df['amount'] < 0]['amount'].sum())
        
        if total_income > 0:
            expense_ratio = total_expenses / total_income
            if expense_ratio < 0.8:
                expense_score = 30
            elif expense_ratio < 1.0:
                expense_score = 20
            else:
                expense_score = 0
            
            score_components['Expense Management'] = expense_score
            total_score += expense_score
        
        max_score += 30
    
    # Transaction Diversity (20 points)
    if 'category' in df.columns:
        num_categories = df['category'].nunique()
        if num_categories >= 5:
            diversity_score = 20
        elif num_categories >= 3:
            diversity_score = 15
        else:
            diversity_score = 10
        
        score_components['Spending Diversity'] = diversity_score
        total_score += diversity_score
        max_score += 20
    
    # Regular Transactions (20 points)
    if 'date' in df.columns and len(df) > 1:
        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'])
        date_range = (df_copy['date'].max() - df_copy['date'].min()).days
        
        if date_range > 0:
            transactions_per_day = len(df) / date_range
            if transactions_per_day > 0.5:
                regularity_score = 20
            elif transactions_per_day > 0.2:
                regularity_score = 15
            else:
                regularity_score = 10
            
            score_components['Transaction Regularity'] = regularity_score
            total_score += regularity_score
        
        max_score += 20
    
    # Data Completeness (30 points)
    completeness = len(df.dropna()) / len(df)
    completeness_score = int(30 * completeness)
    score_components['Data Completeness'] = completeness_score
    total_score += completeness_score
    max_score += 30
    
    # Calculate final score as percentage
    if max_score > 0:
        final_score = (total_score / max_score) * 100
    else:
        final_score = 0
    
    # Display score
    st.subheader("💯 Financial Health Score")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Score display
        if final_score >= 80:
            score_color = "🟢"
            score_label = "Excellent"
        elif final_score >= 60:
            score_color = "🟡"
            score_label = "Good"
        elif final_score >= 40:
            score_color = "🟠"
            score_label = "Fair"
        else:
            score_color = "🔴"
            score_label = "Needs Improvement"
        
        st.metric("Overall Score", f"{final_score:.0f}/100")
        st.write(f"{score_color} **{score_label}**")
    
    with col2:
        # Component breakdown
        st.write("**Score Breakdown:**")
        for component, score in score_components.items():
            st.write(f"• {component}: {score} points")
    
    return final_score, score_components

def export_data_options(df, filename_prefix="data"):
    """Provide export options for data"""
    if df.empty:
        st.warning("No data to export")
        return
    
    st.subheader("📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV export
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # JSON export
        json_data = df.to_json(orient='records', date_format='iso')
        st.download_button(
            label="📋 Download JSON",
            data=json_data,
            file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    with col3:
        # Summary export
        summary_data = {
            'export_date': datetime.now().isoformat(),
            'record_count': len(df),
            'columns': list(df.columns),
            'summary_stats': df.describe().to_dict() if not df.select_dtypes(include=[np.number]).empty else {}
        }
        
        st.download_button(
            label="📊 Download Summary",
            data=json.dumps(summary_data, indent=2, default=str),
            file_name=f"{filename_prefix}_summary_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

def filter_widget(df, columns=None):
    """Create filter widgets for dataframe columns"""
    if df.empty:
        return df
    
    if columns is None:
        columns = df.columns.tolist()
    
    st.subheader("🔍 Data Filters")
    
    filtered_df = df.copy()
    
    with st.expander("Filter Options", expanded=False):
        for col in columns:
            if col in df.columns:
                if df[col].dtype == 'object':
                    # Categorical filter
                    unique_values = df[col].dropna().unique()
                    if len(unique_values) <= 20:  # Only show multiselect for reasonable number of options
                        selected_values = st.multiselect(
                            f"Filter by {col}",
                            options=unique_values,
                            default=unique_values
                        )
                        filtered_df = filtered_df[filtered_df[col].isin(selected_values)]
                
                elif pd.api.types.is_numeric_dtype(df[col]):
                    # Numeric filter
                    min_val, max_val = float(df[col].min()), float(df[col].max())
                    if min_val != max_val:
                        range_values = st.slider(
                            f"Filter by {col}",
                            min_value=min_val,
                            max_value=max_val,
                            value=(min_val, max_val)
                        )
                        filtered_df = filtered_df[
                            (filtered_df[col] >= range_values[0]) & 
                            (filtered_df[col] <= range_values[1])
                        ]
                
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    # Date filter
                    min_date = df[col].min().date()
                    max_date = df[col].max().date()
                    
                    date_range = st.date_input(
                        f"Filter by {col}",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    if len(date_range) == 2:
                        filtered_df = filtered_df[
                            (filtered_df[col].dt.date >= date_range[0]) & 
                            (filtered_df[col].dt.date <= date_range[1])
                        ]
    
    return filtered_df
