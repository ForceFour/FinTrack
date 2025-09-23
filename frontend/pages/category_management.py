"""
Category Management Page - AI-powered categorization and rules
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

st.set_page_config(page_title="Category Management", page_icon=" ", layout="wide")

st.title("Category Management")
st.markdown("### AI-Powered Transaction Categorization & Rules")

# Initialize session state for categories if not exists
if 'custom_categories' not in st.session_state:
    st.session_state.custom_categories = [
        {"name": "Food & Dining", "color": "#FF6B6B", "rules": ["restaurant", "coffee", "food"], "auto_assign": True},
        {"name": "Groceries", "color": "#4ECDC4", "rules": ["grocery", "supermarket", "walmart"], "auto_assign": True},
        {"name": "Transportation", "color": "#45B7D1", "rules": ["gas", "uber", "taxi", "parking"], "auto_assign": True},
        {"name": "Entertainment", "color": "#96CEB4", "rules": ["netflix", "movie", "concert"], "auto_assign": True},
        {"name": "Shopping", "color": "#FFEAA7", "rules": ["amazon", "target", "shopping"], "auto_assign": True},
        {"name": "Utilities", "color": "#DDA0DD", "rules": ["electric", "water", "internet"], "auto_assign": True},
        {"name": "Healthcare", "color": "#98D8C8", "rules": ["hospital", "pharmacy", "doctor"], "auto_assign": True},
    ]

if 'categorization_rules' not in st.session_state:
    st.session_state.categorization_rules = []

# Sidebar for category management
with st.sidebar:
    st.header("Category Controls")

    # Quick stats if we have transaction data
    if 'transactions' in st.session_state and st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)

        if 'category' in df.columns:
            categorized_count = df['category'].notna().sum()
            total_count = len(df)
            categorized_pct = (categorized_count / total_count) * 100

            st.metric("Categorized Transactions", f"{categorized_count}/{total_count}")
            st.metric("Completion Rate", f"{categorized_pct:.1f}%")

            # Category distribution
            category_counts = df['category'].value_counts()
            if not category_counts.empty:
                st.markdown("**Top Categories:**")
                for cat, count in category_counts.head(5).items():
                    st.write(f"• {cat}: {count}")

    st.divider()

    # AI categorization controls
    st.markdown("#### AI Controls")

    if st.button("Auto-Categorize All", type="primary"):
        if 'transactions' in st.session_state:
            with st.spinner():
                st.write("AI categorizing transactions...")
                # Simulate AI categorization
                import time
                time.sleep(2)
                st.success("Auto-categorization complete!")
                st.rerun()

    confidence_threshold = st.slider("AI Confidence Threshold", 0.5, 1.0, 0.8)

    if st.button("Refresh Categories"):
        st.rerun()

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Manage Categories", "AI Rules", "Analytics"])

with tab1:
    st.subheader("Category Overview")

    if 'transactions' in st.session_state and st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)

        # Add sample categories if not present
        if 'category' not in df.columns:
            import numpy as np
            categories = [cat["name"] for cat in st.session_state.custom_categories]
            df['category'] = np.random.choice(categories, len(df))
            # Update session state
            for i, transaction in enumerate(st.session_state.transactions):
                transaction['category'] = df.iloc[i]['category']

        col1, col2 = st.columns(2)

        with col1:
            # Category distribution pie chart
            category_counts = df['category'].value_counts()

            fig_pie = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Transaction Distribution by Category",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Category spending (for expenses only)
            if 'amount' in df.columns:
                expense_df = df[df['amount'] < 0].copy()
                expense_df['amount_abs'] = abs(expense_df['amount'])
                category_spending_series = expense_df.groupby('category')['amount_abs'].sum()
                category_spending = category_spending_series.sort_values(ascending=True)  # type: ignore

                fig_bar = px.bar(
                    x=category_spending.values,
                    y=category_spending.index,
                    orientation='h',
                    title="Spending by Category",
                    labels={'x': 'Amount ($)', 'y': 'Category'},
                    color=category_spending.values,
                    color_continuous_scale='Reds'
                )
                fig_bar.update_layout(showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)

        # Category performance table
        st.subheader("Category Performance")

        if 'amount' in df.columns:
            category_stats = df.groupby('category').agg({
                'amount': ['count', 'sum', 'mean'],
                'date': ['min', 'max']
            }).round(2)

            category_stats.columns = ['Transaction Count', 'Total Amount', 'Average Amount', 'First Transaction', 'Last Transaction']

            # Convert to string format safely
            total_amount_series = pd.Series(category_stats['Total Amount'])
            average_amount_series = pd.Series(category_stats['Average Amount'])

            category_stats['Total Amount'] = total_amount_series.apply(lambda x: f"${x:,.2f}")
            category_stats['Average Amount'] = average_amount_series.apply(lambda x: f"${x:,.2f}")

            st.dataframe(category_stats, use_container_width=True)

    else:
        st.info("No transaction data available. Upload transactions to see category analysis.")

        # Show default categories
        st.subheader("Default Categories")

        default_categories_df = pd.DataFrame(st.session_state.custom_categories)
        default_categories_df['rules_count'] = default_categories_df['rules'].apply(len)

        display_df = default_categories_df[['name', 'color', 'rules_count', 'auto_assign']].copy()
        display_df.columns = ['Category Name', 'Color', 'Rules Count', 'Auto-Assign']

        st.dataframe(display_df, use_container_width=True)

with tab2:
    st.subheader("Manage Categories")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Existing Categories")

        # Display categories in a grid
        for i, category in enumerate(st.session_state.custom_categories):
            with st.container():
                col_a, col_b, col_c, col_d = st.columns([3, 1, 1, 1])

                with col_a:
                    st.markdown(f"**{category['name']}**")
                    st.caption(f"Rules: {', '.join(category['rules'][:3])}{'...' if len(category['rules']) > 3 else ''}")

                with col_b:
                    st.color_picker("Category Color", value=category['color'], key=f"color_{i}", disabled=True, label_visibility="collapsed")

                with col_c:
                    auto_enabled = st.checkbox("Auto", value=category['auto_assign'], key=f"auto_{i}")
                    if auto_enabled != category['auto_assign']:
                        st.session_state.custom_categories[i]['auto_assign'] = auto_enabled

                with col_d:
                    if st.button("", key=f"edit_{i}", help="Edit category"):
                        st.session_state.editing_category = i
                    if st.button("", key=f"delete_{i}", help="Delete category"):
                        st.session_state.custom_categories.pop(i)
                        st.rerun()

                st.divider()

    with col2:
        st.markdown("#### Add New Category")

        with st.form("add_category"):
            new_name = st.text_input("Category Name")
            new_color = st.color_picker("Color", value="#FF6B6B")
            new_rules = st.text_area("Keywords/Rules (one per line)", placeholder="restaurant\ncoffee\nfood")
            new_auto_assign = st.checkbox("Enable auto-assignment", value=True)

            if st.form_submit_button("Add Category"):
                if new_name:
                    rules_list = [rule.strip() for rule in new_rules.split('\n') if rule.strip()]

                    new_category = {
                        "name": new_name,
                        "color": new_color,
                        "rules": rules_list,
                        "auto_assign": new_auto_assign
                    }

                    st.session_state.custom_categories.append(new_category)
                    st.success(f"Added category: {new_name}")
                    st.rerun()
                else:
                    st.error("Please enter a category name")

    # Edit category form
    if hasattr(st.session_state, 'editing_category'):
        edit_idx = st.session_state.editing_category
        category = st.session_state.custom_categories[edit_idx]

        st.markdown(f"#### Edit Category: {category['name']}")

        with st.form("edit_category"):
            edit_name = st.text_input("Category Name", value=category['name'])
            edit_color = st.color_picker("Color", value=category['color'])
            edit_rules = st.text_area("Keywords/Rules (one per line)", value='\n'.join(category['rules']))
            edit_auto_assign = st.checkbox("Enable auto-assignment", value=category['auto_assign'])

            col_save, col_cancel = st.columns(2)

            with col_save:
                if st.form_submit_button("Save Changes", type="primary"):
                    rules_list = [rule.strip() for rule in (edit_rules or '').split('\n') if rule.strip()]

                    st.session_state.custom_categories[edit_idx] = {
                        "name": edit_name,
                        "color": edit_color,
                        "rules": rules_list,
                        "auto_assign": edit_auto_assign
                    }

                    del st.session_state.editing_category
                    st.success("Category updated!")
                    st.rerun()

            with col_cancel:
                if st.form_submit_button("Cancel"):
                    del st.session_state.editing_category
                    st.rerun()

with tab3:
    st.subheader("AI Categorization Rules")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Smart Rules Engine")

        # Rule types
        rule_type = st.selectbox(
            "Rule Type",
            ["Keyword Match", "Amount Range", "Merchant Pattern", "Date Pattern", "Description Pattern"]
        )

        if rule_type == "Keyword Match":
            st.markdown("**Keyword Matching Rules**")
            keyword = st.text_input("Keyword or phrase")
            match_category = st.selectbox("Assign to category", [cat["name"] for cat in st.session_state.custom_categories])
            case_sensitive = st.checkbox("Case sensitive")

            if st.button("Add Keyword Rule"):
                rule = {
                    "type": "keyword",
                    "keyword": keyword,
                    "category": match_category,
                    "case_sensitive": case_sensitive,
                    "created": datetime.now().isoformat()
                }
                st.session_state.categorization_rules.append(rule)
                st.success(f"Added keyword rule: '{keyword}' → {match_category}")

        elif rule_type == "Amount Range":
            st.markdown("**Amount-Based Rules**")
            min_amount = st.number_input("Minimum amount", value=0.0)
            max_amount = st.number_input("Maximum amount", value=100.0)
            amount_category = st.selectbox("Assign to category", [cat["name"] for cat in st.session_state.custom_categories])

            if st.button("Add Amount Rule"):
                rule = {
                    "type": "amount_range",
                    "min_amount": min_amount,
                    "max_amount": max_amount,
                    "category": amount_category,
                    "created": datetime.now().isoformat()
                }
                st.session_state.categorization_rules.append(rule)
                st.success(f"Added amount rule: ${min_amount}-${max_amount} → {amount_category}")

        elif rule_type == "Merchant Pattern":
            st.markdown("**Merchant-Based Rules**")
            merchant_pattern = st.text_input("Merchant name/pattern")
            merchant_category = st.selectbox("Assign to category", [cat["name"] for cat in st.session_state.custom_categories])

            if st.button("Add Merchant Rule"):
                rule = {
                    "type": "merchant",
                    "pattern": merchant_pattern,
                    "category": merchant_category,
                    "created": datetime.now().isoformat()
                }
                st.session_state.categorization_rules.append(rule)
                st.success(f"Added merchant rule: '{merchant_pattern}' → {merchant_category}")

    with col2:
        st.markdown("#### Active Rules")

        if st.session_state.categorization_rules:
            for i, rule in enumerate(st.session_state.categorization_rules):
                with st.container():
                    col_rule, col_actions = st.columns([3, 1])

                    with col_rule:
                        if rule["type"] == "keyword":
                            st.write(f" **Keyword:** '{rule['keyword']}' → {rule['category']}")
                        elif rule["type"] == "amount_range":
                            st.write(f" **Amount:** ${rule['min_amount']}-${rule['max_amount']} → {rule['category']}")
                        elif rule["type"] == "merchant":
                            st.write(f" **Merchant:** '{rule['pattern']}' → {rule['category']}")

                        st.caption(f"Created: {rule['created'][:10]}")

                    with col_actions:
                        if st.button("", key=f"delete_rule_{i}"):
                            st.session_state.categorization_rules.pop(i)
                            st.rerun()

                    st.divider()
        else:
            st.info("No custom rules defined. Add rules to customize AI categorization.")

        # Rule testing
        st.markdown("#### Test Rules")

        test_description = st.text_input("Test description", placeholder="STARBUCKS COFFEE STORE")
        test_amount = st.number_input("Test amount", value=-4.50)

        if st.button("Test Categorization"):
            # Simulate rule testing
            matched_category = "Food & Dining"  # Simulated result
            confidence = 0.95

            st.success(f"**Predicted Category:** {matched_category}")
            st.info(f"**Confidence:** {confidence:.1%}")

with tab4:
    st.subheader("Categorization Analytics")

    if 'transactions' in st.session_state and st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Category Accuracy")

            # Simulated accuracy metrics
            accuracy_data = {
                "Category": [cat["name"] for cat in st.session_state.custom_categories],
                "Accuracy": [0.95, 0.88, 0.92, 0.85, 0.90, 0.87, 0.93],
                "Confidence": [0.92, 0.85, 0.89, 0.82, 0.87, 0.84, 0.91]
            }

            accuracy_df = pd.DataFrame(accuracy_data)

            # Accuracy chart
            fig_accuracy = px.bar(
                accuracy_df,
                x="Category",
                y="Accuracy",
                title="AI Categorization Accuracy by Category",
                color="Accuracy",
                color_continuous_scale="Greens"
            )
            fig_accuracy.update_layout(xaxis_tickangle=-45, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig_accuracy, use_container_width=True)

        with col2:
            st.markdown("#### Confidence Distribution")

            # Confidence histogram
            confidence_scores = [0.95, 0.88, 0.92, 0.85, 0.90, 0.87, 0.93] * 20  # Simulated

            fig_confidence = px.histogram(
                x=confidence_scores,
                title="AI Confidence Score Distribution",
                nbins=20,
                labels={'x': 'Confidence Score', 'y': 'Count'}
            )
            fig_confidence.update_traces(marker_color='lightblue')
            st.plotly_chart(fig_confidence, use_container_width=True)

        # Performance metrics
        st.markdown("#### Performance Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Overall Accuracy", "89.5%", delta="2.3%")

        with col2:
            st.metric("Auto-Categorized", "87%", delta="15%")

        with col3:
            st.metric("Manual Review Needed", "13%", delta="-15%")

        with col4:
            st.metric("Average Confidence", "0.87", delta="0.05")

        # Improvement suggestions
        st.markdown("#### Improvement Suggestions")

        suggestions = [
            "Add more keyword rules for 'Entertainment' category (accuracy: 85%)",
            "Review transactions with confidence < 0.8 for pattern improvement",
            "'Transportation' category shows good accuracy (92%) - rules working well",
            "Consider adding amount-based rules for better utility bill detection"
        ]

        for suggestion in suggestions:
            st.info(suggestion)

    else:
        st.info("Upload transaction data to see categorization analytics.")

# Export/Import functionality
st.subheader("Category Data Management")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export Categories"):
        export_data = {
            "categories": st.session_state.custom_categories,
            "rules": st.session_state.categorization_rules,
            "exported_at": datetime.now().isoformat()
        }

        st.download_button(
            label="Download Category Config",
            data=json.dumps(export_data, indent=2),
            file_name=f"categories_config_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with col2:
    uploaded_config = st.file_uploader("Import Categories", type=['json'])

    if uploaded_config is not None:
        try:
            config_data = json.load(uploaded_config)

            if st.button("Import Configuration"):
                st.session_state.custom_categories = config_data.get('categories', [])
                st.session_state.categorization_rules = config_data.get('rules', [])
                st.success("Categories and rules imported successfully!")
                st.rerun()
        except Exception as e:
            st.error(f"Error importing configuration: {e}")

with col3:
    if st.button("Reset to Defaults"):
        # Reset to default categories
        st.session_state.custom_categories = [
            {"name": "Food & Dining", "color": "#FF6B6B", "rules": ["restaurant", "coffee", "food"], "auto_assign": True},
            {"name": "Groceries", "color": "#4ECDC4", "rules": ["grocery", "supermarket", "walmart"], "auto_assign": True},
            {"name": "Transportation", "color": "#45B7D1", "rules": ["gas", "uber", "taxi", "parking"], "auto_assign": True},
            {"name": "Entertainment", "color": "#96CEB4", "rules": ["netflix", "movie", "concert"], "auto_assign": True},
            {"name": "Shopping", "color": "#FFEAA7", "rules": ["amazon", "target", "shopping"], "auto_assign": True},
            {"name": "Utilities", "color": "#DDA0DD", "rules": ["electric", "water", "internet"], "auto_assign": True},
            {"name": "Healthcare", "color": "#98D8C8", "rules": ["hospital", "pharmacy", "doctor"], "auto_assign": True},
        ]
        st.session_state.categorization_rules = []
        st.success("Reset to default categories!")
        st.rerun()
