"""
Suggestions Page - AI-powered financial recommendations and insights
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import logging

# Add project root to sys.path to resolve src module
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Attempt to import UnifiedClassifierAgent
try:
    from src.agents.unified_classifier_agent import UnifiedClassifierAgent
    classifier_available = True
except ModuleNotFoundError:
    st.error("Module 'unified_classifier_agent' not found. Using fallback categorization. Please ensure the agent is available.")
    classifier_available = False

# Fallback if schemas are not available
try:
    from src.schemas.transaction_schemas import MerchantTransaction, TransactionCategory, PaymentMethod
except ModuleNotFoundError:
    class TransactionCategory:
        ESSENTIALS = 'essentials'
        ENTERTAINMENT = 'entertainment'
        TRANSPORTATION = 'transportation'
        HOUSING = 'housing'
        SAVINGS = 'savings'
        HEALTHCARE = 'healthcare'
        EDUCATION = 'education'
        MISCELLANEOUS = 'miscellaneous'

    class PaymentMethod:
        CREDIT_CARD = 'credit_card'
        DEBIT_CARD = 'debit_card'
        CASH = 'cash'
        OTHER = 'other'

    class MerchantTransaction:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', '')
            self.description_cleaned = kwargs.get('description_cleaned', '')
            self.amount = kwargs.get('amount', 0.0)
            self.merchant_standardized = kwargs.get('merchant_standardized', '')
            date = kwargs.get('date', datetime.now())
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            self.date = date
            self.year = date.year
            self.month = date.month
            self.day = date.day
            self.day_of_week = date.weekday()
            self.payment_method = kwargs.get('payment_method', 'other')
            self.has_discount = kwargs.get('has_discount', False)
            self.discount_percentage = kwargs.get('discount_percentage', 0.0)
            self.transaction_type = kwargs.get('transaction_type', 'expense' if self.amount < 0 else 'income')
            self.metadata = kwargs.get('metadata', {})
            self.merchant_name = self.merchant_standardized
            self.is_merchant_known = bool(self.merchant_standardized)

# Define categories based on TransactionCategory or fallback
categories = (
    [cat.value for cat in TransactionCategory.__members__.values()]
    if classifier_available
    else [getattr(TransactionCategory, attr) for attr in dir(TransactionCategory) if not attr.startswith('__')]
)

st.set_page_config(page_title="Suggestions", page_icon="💡", layout="wide")
st.title("AI Financial Advisor")
st.markdown("### Personalized Recommendations & Smart Insights")

# Current Spending Distribution Section
st.subheader("Current Spending Distribution")
if 'transactions' in st.session_state and st.session_state.transactions:
    try:
        # Use the UnifiedClassifierAgent if available
        if classifier_available:
            from src.schemas.transaction_schemas import MerchantTransaction
            from src.agents.unified_classifier_agent import UnifiedClassifierAgent

            # Initialize the unified classifier agent
            classifier_agent = UnifiedClassifierAgent()

            # Preprocess transactions for classification
            merchant_transactions = []
            for t in st.session_state.transactions:
                if float(t['amount']) < 0:  # Only process expenses
                    # Create MerchantTransaction object with proper date handling
                    date = t.get('date', datetime.now())
                    if isinstance(date, str):
                        try:
                            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        except ValueError:
                            date = datetime.now()

                    merchant_txn = MerchantTransaction(
                        id=str(t.get('id', len(merchant_transactions))),
                        description_cleaned=t.get('description', ''),
                        amount=float(t['amount']),
                        merchant_standardized=t.get('merchant', ''),
                        date=date,
                        year=date.year,
                        month=date.month,
                        day=date.day,
                        day_of_week=date.weekday(),
                        payment_method=t.get('payment_method', 'other'),
                        has_discount=t.get('has_discount', False),
                        discount_percentage=t.get('discount_percentage', 0.0),
                        transaction_type='expense',
                        metadata=t.get('metadata', {})
                    )
                    merchant_transactions.append(merchant_txn)

            if merchant_transactions:
                # Classify transactions using the unified agent
                classification_input = classifier_agent.ClassifierAgentInput(
                    merchant_transactions=merchant_transactions
                )
                classification_output = classifier_agent.process(classification_input)

                # Create DataFrame from classified transactions
                expense_data = []
                for ct in classification_output.classified_transactions:
                    # Find original transaction
                    original_txn = next(t for t in merchant_transactions if t.id == ct.transaction_id)
                    expense_data.append({
                        'amount': abs(float(original_txn.amount)),  # Make amount positive for visualization
                        'description': original_txn.description_cleaned,
                        'merchant': original_txn.merchant_standardized,
                        'category': ct.predicted_category.value if hasattr(ct.predicted_category, 'value') else str(ct.predicted_category),
                        'confidence': ct.classification_confidence
                    })

                expense_df = pd.DataFrame(expense_data)

                # Calculate spending by category
                spending_by_category = expense_df.groupby('category')['amount'].sum().abs()

                # Create pie chart
                fig = px.pie(
                    values=spending_by_category.values,
                    names=spending_by_category.index,
                    title="Current Spending Distribution",
                    hover_data=[spending_by_category.values],
                    labels={'hover_data_0': 'Amount (LKR)'}
                )
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

                # Display category-wise spending table
                st.markdown("#### Category-wise Spending Breakdown")
                spending_df = pd.DataFrame({
                    'Category': spending_by_category.index,
                    'Amount (LKR)': spending_by_category.values,
                    'Percentage': (spending_by_category.values / spending_by_category.sum() * 100)
                })
                spending_df['Amount (LKR)'] = spending_df['Amount (LKR)'].round(2)
                spending_df['Percentage'] = spending_df['Percentage'].round(2)
                st.dataframe(spending_df.sort_values('Amount (LKR)', ascending=False), use_container_width=True)
            else:
                st.info("No expense transactions found in the data.")
        else:
            st.warning("Unified classifier not available. Please check the agent installation.")
    except Exception as e:
        st.error(f"Error processing transactions: {e}")
        st.info("Using fallback categorization...")
else:
    st.warning("No transaction data available. Please upload transactions first.")

# Check if we have data
if 'transactions' not in st.session_state or not st.session_state.transactions:
    st.warning("No transaction data available. Please upload data first.")
    st.info("Use the sidebar navigation to go to 'Upload & Process' first.")
    st.stop()

# Fallback categorization function
def fallback_categorize(description: str, amount: float, merchant: str = '') -> str:
    """Simple rule-based categorization if classifier is unavailable"""
    description = description.lower() if isinstance(description, str) else ''
    merchant = merchant.lower() if isinstance(merchant, str) else ''
    if 'grocery' in description or 'keells' in merchant or 'cargills' in merchant or 'electricity' in description or 'dialog' in merchant:
        return 'essentials'
    elif 'netflix' in description or 'cinema' in description or 'spotify' in merchant:
        return 'entertainment'
    elif 'uber' in description or 'pickme' in merchant or 'gas' in description:
        return 'transportation'
    elif 'rent' in description or 'housing' in merchant:
        return 'housing'
    elif 'savings' in description or 'investment' in merchant:
        return 'savings'
    elif 'hospital' in description or 'nawaloka' in merchant or 'pharmacy' in description:
        return 'healthcare'
    elif 'school' in description or 'university' in merchant or 'books' in description:
        return 'education'
    else:
        return 'miscellaneous'

# Add classify_transaction method to UnifiedClassifierAgent if available
if classifier_available:
    def classify_transaction(self, description: str, amount: float, merchant: str = '') -> Dict[str, str]:
        """Classify a single transaction using the process method"""
        try:
            # Create a MerchantTransaction object with proper date handling
            date = datetime.now()
            txn = MerchantTransaction(
                id="temp_id",
                description_cleaned=description,
                amount=amount,
                merchant_standardized=merchant,
                date=date,
                year=date.year,
                month=date.month,
                day=date.day,
                day_of_week=date.weekday(),
                payment_method='other',
                has_discount=False,
                discount_percentage=0.0,
                transaction_type='expense' if amount < 0 else 'income',
                metadata={}
            )
            # Process as a single transaction
            input_data = self.ClassifierAgentInput(merchant_transactions=[txn])
            output = self.process(input_data)
            if output.classified_transactions:
                category = output.classified_transactions[0].predicted_category
                category_value = category.value if hasattr(category, 'value') else str(category)
                return {'category': category_value}
            else:
                return {'category': 'miscellaneous'}
        except Exception as e:
            logging.error(f"Classification failed: {e}")
            return {'category': 'miscellaneous'}

    import types
    UnifiedClassifierAgent.classify_transaction = types.MethodType(classify_transaction, UnifiedClassifierAgent)

# Initialize UnifiedClassifierAgent if available
classifier = UnifiedClassifierAgent() if classifier_available else None

# Get and categorize transaction data
df = pd.DataFrame(st.session_state.transactions)
df['date'] = pd.to_datetime(df['date'])
df['amount_abs'] = abs(df['amount'])
df['is_expense'] = df['amount'] < 0

# Categorize transactions
if 'category' not in df.columns or df['category'].isna().any():
    if classifier_available:
        try:
            df['category'] = df.apply(
                lambda row: classifier.classify_transaction(
                    description=row.get('description', ''),
                    amount=row['amount'],
                    merchant=row.get('merchant', '')
                )['category'],
                axis=1
            )
        except Exception as e:
            st.warning(f"Classifier failed: {e}. Using fallback categorization.")
            df['category'] = df.apply(
                lambda row: fallback_categorize(
                    description=row.get('description', ''),
                    amount=row['amount'],
                    merchant=row.get('merchant', '')
                ),
                axis=1
            )
    else:
        df['category'] = df.apply(
            lambda row: fallback_categorize(
                description=row.get('description', ''),
                amount=row['amount'],
                merchant=row.get('merchant', '')
            ),
            axis=1
        )

# Initialize session state for preferences
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {
        'savings_goal': 1000,
        'risk_tolerance': 'moderate',
        'financial_goals': ['Emergency Fund', 'Vacation'],
        'budget_preferences': {
            'total_monthly_budget': 5000,
            'categories': {cat: 1.0 / len(categories) for cat in categories}
        }
    }
if 'suggestion_history' not in st.session_state:
    st.session_state.suggestion_history = []

# Sidebar for preferences
with st.sidebar:
    st.header("Your Preferences")

    # Annual Savings Goal
    annual_savings_goal = st.number_input(
        "Annual Savings Goal (LKR)",
        min_value=0,
        value=st.session_state.user_preferences.get('annual_savings_goal', 12000),
        step=1000
    )
    monthly_savings_goal = annual_savings_goal / 12
    st.session_state.user_preferences['annual_savings_goal'] = annual_savings_goal
    st.session_state.user_preferences['savings_goal'] = monthly_savings_goal

    # Total Monthly Budget
    total_monthly_budget = st.number_input(
        "Total Monthly Budget (LKR)",
        min_value=0,
        value=st.session_state.user_preferences['budget_preferences'].get('total_monthly_budget', 5000),
        step=100
    )
    st.session_state.user_preferences['budget_preferences']['total_monthly_budget'] = total_monthly_budget
    st.session_state.user_preferences['budget_preferences']['categories'] = {cat: 1.0 / len(categories) for cat in categories}

    # Risk tolerance
    current_risk = st.session_state.user_preferences['risk_tolerance']
    risk_options = ['Conservative', 'Moderate', 'Aggressive']
    try:
        current_index = risk_options.index(current_risk.title() if current_risk else 'Moderate')
    except (ValueError, AttributeError):
        current_index = 1
    risk_tolerance = st.selectbox(
        "Risk Tolerance",
        risk_options,
        index=current_index
    )
    st.session_state.user_preferences['risk_tolerance'] = risk_tolerance.lower() if risk_tolerance else 'moderate'

    # Financial goals
    available_goals = [
        'Emergency Fund', 'Vacation', 'Home Purchase', 'Car Purchase',
        'Debt Payoff', 'Retirement', 'Education', 'Investment'
    ]
    financial_goals = st.multiselect(
        "Financial Goals",
        available_goals,
        default=st.session_state.user_preferences['financial_goals']
    )
    st.session_state.user_preferences['financial_goals'] = financial_goals

    st.divider()
    st.markdown("#### Quick Actions")
    if st.button("Refresh Suggestions"):
        st.rerun()
    if st.button("Generate New Analysis"):
        st.session_state.last_analysis = datetime.now()
        st.success("Analysis updated!")

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Savings Opportunities",
    "Budget Optimization",
    "Investment Ideas",
    "Risk Analysis",
    "Goal Planning"
])

with tab1:
    st.subheader("Savings Opportunities")
    expense_df = df[df['is_expense']].copy()
    category_spending_df = expense_df.groupby('category')['amount_abs'].agg(['sum', 'mean', 'count']).round(2)
    category_spending_df.columns = ['Total', 'Average', 'Count']
    category_spending = category_spending_df.sort_values('Total', ascending=False)

    savings_opportunities = []
    if 'essentials' in category_spending.index:
        essentials_spending = category_spending.loc['essentials', 'Total']
        if essentials_spending > 400:
            potential_savings = essentials_spending * 0.25
            savings_opportunities.append({
                'category': 'essentials',
                'current_spending': essentials_spending,
                'suggested_spending': essentials_spending - potential_savings,
                'potential_savings': potential_savings,
                'difficulty': 'Medium',
                'suggestions': [
                    'Reduce utility usage',
                    'Shop for essentials with discounts',
                    'Plan bulk grocery purchases',
                    'Negotiate bills'
                ]
            })
    if 'transportation' in category_spending.index:
        transport_spending = category_spending.loc['transportation', 'Total']
        if transport_spending > 200:
            potential_savings = transport_spending * 0.20
            savings_opportunities.append({
                'category': 'transportation',
                'current_spending': transport_spending,
                'suggested_spending': transport_spending - potential_savings,
                'potential_savings': potential_savings,
                'difficulty': 'Easy',
                'suggestions': [
                    'Use public transportation more often',
                    'Carpool with colleagues',
                    'Combine errands into single trips',
                    'Consider bike riding for short distances'
                ]
            })
    if 'entertainment' in category_spending.index:
        entertainment_spending = category_spending.loc['entertainment', 'Total']
        if entertainment_spending > 150:
            potential_savings = entertainment_spending * 0.30
            savings_opportunities.append({
                'category': 'entertainment',
                'current_spending': entertainment_spending,
                'suggested_spending': entertainment_spending - potential_savings,
                'potential_savings': potential_savings,
                'difficulty': 'Hard',
                'suggestions': [
                    'Look for free community events',
                    'Share streaming service subscriptions',
                    'Take advantage of library resources',
                    'Host movie nights at home'
                ]
            })

    total_potential_savings = sum(opp['potential_savings'] for opp in savings_opportunities)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Your Monthly Savings Target", f"LKR {monthly_savings_goal:.2f}")
    with col2:
        st.metric("Potential Monthly Savings", f"LKR {total_potential_savings:.2f}")
    with col3:
        potential_annual_savings = total_potential_savings * 12
        progress_to_goal = (potential_annual_savings / annual_savings_goal) * 100 if annual_savings_goal > 0 else 0
        st.metric("Annual Savings Potential", f"LKR {potential_annual_savings:.2f}", delta=f"{progress_to_goal:.1f}% of goal")
    with col4:
        current_total = expense_df['amount_abs'].sum()
        savings_percentage = (total_potential_savings / current_total) * 100 if current_total > 0 else 0
        st.metric("Savings Percentage", f"{savings_percentage:.1f}%")
        st.metric("Categories to Optimize", len(savings_opportunities))

    for opp in savings_opportunities:
        with st.expander(f"{opp['category'].replace('_', ' ').title()} - Save LKR {opp['potential_savings']:.2f}/month"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Current vs Suggested Spending:**")
                comparison_data = {
                    'Type': ['Current', 'Suggested'],
                    'Amount': [opp['current_spending'], opp['suggested_spending']]
                }
                fig_comparison = px.bar(
                    comparison_data,
                    x='Type',
                    y='Amount',
                    title=f"{opp['category'].replace('_', ' ').title()} Spending Comparison",
                    color='Type',
                    color_discrete_map={'Current': 'red', 'Suggested': 'green'}
                )
                st.plotly_chart(fig_comparison, use_container_width=True)
                difficulty_color = {'Easy': 'green', 'Medium': 'orange', 'Hard': 'red'}[opp['difficulty']]
                st.markdown(f"**Difficulty:** :{difficulty_color}[{opp['difficulty']}]")
            with col2:
                st.markdown("**Specific Suggestions:**")
                for suggestion in opp['suggestions']:
                    st.write(f"• {suggestion}")
                if st.button(f"Apply to {opp['category'].replace('_', ' ').title()}", key=f"apply_{opp['category']}"):
                    st.session_state.suggestion_history.append({
                        'category': opp['category'],
                        'suggestion': 'Spending reduction plan',
                        'potential_savings': opp['potential_savings'],
                        'applied_date': datetime.now(),
                        'status': 'applied'
                    })
                    st.success(f"Savings plan applied to {opp['category'].replace('_', ' ').title()}!")

with tab2:
    st.subheader("Budget Optimization")
    expense_df = df[df['is_expense']].copy()
    current_spending = expense_df.groupby('category')['amount_abs'].sum()
    total_spending = current_spending.sum() if current_spending.sum() > 0 else 1

    total_budget = st.session_state.user_preferences['budget_preferences']['total_monthly_budget']
    recommended_allocation = st.session_state.user_preferences['budget_preferences']['categories']
    recommended_amounts = {cat: total_budget * pct for cat, pct in recommended_allocation.items()}

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Current Spending Distribution")
        current_distribution = {cat: (amt / total_spending) * 100 for cat, amt in current_spending.items()}
        for cat in categories:
            if cat not in current_distribution:
                current_distribution[cat] = 0
        fig_current_pie = px.pie(
            values=list(current_distribution.values()),
            names=[cat.replace('_', ' ').title() for cat in current_distribution.keys()],
            title="Current Spending Distribution (%)"
        )
        st.plotly_chart(fig_current_pie, use_container_width=True)

    with col2:
        st.markdown("#### Recommended Budget Distribution")
        recommended_distribution = {cat: pct * 100 for cat, pct in recommended_allocation.items()}
        fig_recommended = px.pie(
            values=list(recommended_distribution.values()),
            names=[cat.replace('_', ' ').title() for cat in recommended_distribution.keys()],
            title="Recommended Budget Distribution (%)"
        )
        st.plotly_chart(fig_recommended, use_container_width=True)

    st.markdown("#### Budget Comparison & Recommendations")
    budget_comparison = []
    for category in set(current_spending.index).union(categories):
        current_amount = current_spending.get(category, 0)
        current_pct = (current_amount / total_spending * 100) if total_spending > 0 else 0
        recommended_pct = recommended_allocation.get(category, 1.0 / len(categories)) * 100
        recommended_amount = total_budget * (recommended_pct / 100)
        difference = current_amount - recommended_amount
        status = "Over Budget" if difference > 0 else "Under Budget" if difference < -10 else "On Track"
        budget_comparison.append({
            'Category': category.replace('_', ' ').title(),
            'Current Amount': f"LKR {current_amount:.2f}",
            'Current %': f"{current_pct:.1f}%",
            'Recommended %': f"{recommended_pct:.1f}%",
            'Recommended Amount': f"LKR {recommended_amount:.2f}",
            'Difference': f"LKR {difference:.2f}",
            'Status': status
        })

    budget_df = pd.DataFrame(budget_comparison, columns=[
        'Category', 'Current Amount', 'Current %', 'Recommended %',
        'Recommended Amount', 'Difference', 'Status'
    ])

    def color_budget_status(val):
        if pd.isna(val) or not isinstance(val, str):
            return 'background-color: transparent'
        return {
            'Over Budget': 'background-color: #ffebee',
            'Under Budget': 'background-color: #e8f5e8',
            'On Track': 'background-color: #fff3e0'
        }.get(val, 'background-color: transparent')

    styled_df = budget_df.style.apply(lambda s: [color_budget_status(val) for val in s], subset=['Status'])
    st.dataframe(styled_df, use_container_width=True)

with tab3:
    st.subheader("Investment Ideas")
    total_income = df[~df['is_expense']]['amount_abs'].sum() if not df[~df['is_expense']].empty else 5000
    total_expenses = expense_df['amount_abs'].sum()
    available_for_investment = max(0, total_income - total_expenses - monthly_savings_goal)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Available for Investment", f"LKR {available_for_investment:.2f}")
    with col2:
        current_risk = st.session_state.user_preferences.get('risk_tolerance', 'moderate')
        st.metric("Risk Tolerance", current_risk.title() if current_risk else 'Moderate')
    with col3:
        recommended_investment_pct = {'conservative': 0.6, 'moderate': 0.8, 'aggressive': 1.0}.get(current_risk, 0.8)
        recommended_amount = available_for_investment * recommended_investment_pct
        st.metric("Recommended Investment", f"LKR {recommended_amount:.2f}")

    current_risk = st.session_state.user_preferences.get('risk_tolerance', 'moderate')
    if current_risk == 'conservative':
        investment_suggestions = [
            {'type': 'essentials', 'allocation': 35, 'expected_return': 4.5, 'risk_level': 'Very Low', 'description': 'Essential spending with potential for optimization'},
            {'type': 'savings', 'allocation': 25, 'expected_return': 3.8, 'risk_level': 'Low', 'description': 'Regular savings and emergency fund'},
            {'type': 'housing', 'allocation': 20, 'expected_return': 4.2, 'risk_level': 'Low', 'description': 'Housing and utilities management'},
            {'type': 'healthcare', 'allocation': 10, 'expected_return': 4.0, 'risk_level': 'Low', 'description': 'Healthcare and wellness expenses'},
            {'type': 'transportation', 'allocation': 10, 'expected_return': 3.5, 'risk_level': 'Low', 'description': 'Transportation and commuting'}
        ]
    elif current_risk == 'moderate':
        investment_suggestions = [
            {'type': 'essentials', 'allocation': 30, 'expected_return': 5.0, 'risk_level': 'Medium', 'description': 'Essential spending optimization'},
            {'type': 'entertainment', 'allocation': 15, 'expected_return': 6.0, 'risk_level': 'Medium', 'description': 'Entertainment and leisure activities'},
            {'type': 'education', 'allocation': 20, 'expected_return': 7.0, 'risk_level': 'Medium', 'description': 'Educational investments'},
            {'type': 'savings', 'allocation': 20, 'expected_return': 4.5, 'risk_level': 'Low', 'description': 'Savings and investments'},
            {'type': 'miscellaneous', 'allocation': 15, 'expected_return': 5.5, 'risk_level': 'Medium', 'description': 'Other discretionary spending'}
        ]
    else:
        investment_suggestions = [
            {'type': 'entertainment', 'allocation': 25, 'expected_return': 8.0, 'risk_level': 'High', 'description': 'Entertainment and leisure optimization'},
            {'type': 'education', 'allocation': 25, 'expected_return': 9.0, 'risk_level': 'High', 'description': 'Educational and skill investments'},
            {'type': 'savings', 'allocation': 20, 'expected_return': 7.0, 'risk_level': 'Medium', 'description': 'Aggressive investment strategy'},
            {'type': 'essentials', 'allocation': 15, 'expected_return': 6.0, 'risk_level': 'Medium', 'description': 'Essential spending optimization'},
            {'type': 'miscellaneous', 'allocation': 15, 'expected_return': 8.5, 'risk_level': 'High', 'description': 'Flexible discretionary spending'}
        ]

    allocation_df = pd.DataFrame(investment_suggestions)
    fig_allocation = px.pie(
        allocation_df,
        values='allocation',
        names='type',
        title=f"Recommended Investment Allocation - {current_risk.title() if current_risk else 'Moderate'} Risk"
    )
    st.plotly_chart(fig_allocation, use_container_width=True)

    st.markdown("#### 💼 Investment Recommendations")
    for inv in investment_suggestions:
        with st.expander(f"{inv['type']} - {inv['allocation']}% allocation"):
            col1, col2 = st.columns(2)
            with col1:
                amount = recommended_amount * (inv['allocation'] / 100)
                annual_return = amount * (inv['expected_return'] / 100)
                st.metric("Suggested Amount", f"LKR {amount:.2f}")
                st.metric("Expected Annual Return", f"LKR {annual_return:.2f}")
                st.metric("Expected Return Rate", f"{inv['expected_return']:.1f}%")
            with col2:
                risk_colors = {'Very Low': 'green', 'Low': 'blue', 'Low-Medium': 'orange', 'Medium': 'orange', 'High': 'red'}
                risk_color = risk_colors.get(inv['risk_level'], 'gray')
                st.markdown(f"**Risk Level:** :{risk_color}[{inv['risk_level']}]")
                st.markdown(f"**Description:** {inv['description']}")
                if st.button(f"Learn More", key=f"learn_{inv['type']}"):
                    st.info(f"Research {inv['type']} options from reputable brokers like Vanguard, Fidelity, or Schwab.")

with tab4:
    st.subheader("Risk Analysis")
    col1, col2, col3, col4 = st.columns(4)
    monthly_expenses = expense_df['amount_abs'].sum()
    emergency_fund_months = monthly_savings_goal / monthly_expenses if monthly_expenses > 0 else 0
    with col1:
        color = "normal" if emergency_fund_months >= 3 else "inverse"
        st.metric("Emergency Fund (Months)", f"{emergency_fund_months:.1f}", delta_color=color)

    if len(expense_df) > 0:
        try:
            expense_df_copy = expense_df.copy()
            expense_df_copy['date'] = pd.to_datetime(expense_df_copy['date'])
            daily_spending = expense_df_copy.groupby(expense_df_copy['date'].dt.date)['amount_abs'].sum()
            spending_volatility = daily_spending.std() / daily_spending.mean() if len(daily_spending) > 1 else 0
        except Exception:
            spending_volatility = 0
    else:
        spending_volatility = 0
    with col2:
        volatility_status = "Low" if spending_volatility < 0.5 else "Medium" if spending_volatility < 1.0 else "High"
        st.metric("Spending Volatility", volatility_status)

    recurring_keywords = ['netflix', 'spotify', 'subscription', 'monthly', 'annual', 'dialog', 'mobitel']
    if len(expense_df) > 0 and 'description' in expense_df.columns:
        try:
            description_series = pd.Series(expense_df['description'])
            recurring_mask = description_series.str.lower().str.contains('|'.join(recurring_keywords), na=False)
            recurring_expenses = expense_df[recurring_mask]['amount_abs'].sum()
        except (AttributeError, KeyError):
            recurring_expenses = 0
    else:
        recurring_expenses = 0
    recurring_ratio = (recurring_expenses / monthly_expenses) * 100 if monthly_expenses > 0 else 0
    with col3:
        st.metric("Recurring Expenses", f"{recurring_ratio:.1f}%")

    if len(expense_df) > 0:
        try:
            amount_series = pd.Series(expense_df['amount_abs'])
            large_threshold = amount_series.quantile(0.9)
            large_transactions = len(expense_df[expense_df['amount_abs'] > large_threshold])
        except (AttributeError, KeyError):
            large_transactions = 0
    else:
        large_transactions = 0
    with col4:
        st.metric("Large Transactions", large_transactions)

    st.markdown("#### Risk Indicators")
    risks = []
    if emergency_fund_months < 3:
        risks.append({
            'type': 'Emergency Fund',
            'severity': 'High',
            'message': f'Your emergency fund covers only {emergency_fund_months:.1f} months of expenses. Aim for 3-6 months.',
            'action': 'Increase your monthly savings goal and reduce discretionary spending.'
        })
    if recurring_ratio > 30:
        risks.append({
            'type': 'Subscription Overload',
            'severity': 'Medium',
            'message': f'Recurring expenses make up {recurring_ratio:.1f}% of your budget. This reduces flexibility.',
            'action': 'Review and cancel unused subscriptions. Consider sharing services with family.'
        })
    if spending_volatility > 1.0:
        risks.append({
            'type': 'Irregular Spending',
            'severity': 'Medium',
            'message': 'Your spending patterns are highly variable, making budgeting difficult.',
            'action': 'Create a more structured budget and track daily expenses.'
        })
    if large_transactions > 5:
        risks.append({
            'type': 'Impulse Purchases',
            'severity': 'Low',
            'message': f'You have {large_transactions} large transactions this period.',
            'action': 'Implement a 24-hour waiting period for purchases over LKR 100.'
        })
    if not risks:
        st.success("No significant financial risks detected!")
    else:
        for risk in risks:
            severity_colors = {'High': 'error', 'Medium': 'warning', 'Low': 'info'}
            severity_color = severity_colors[risk['severity']]
            getattr(st, severity_color)(f"**{risk['type']}** ({risk['severity']} Risk): {risk['message']}")
            st.info(f"**Action:** {risk['action']}")

with tab5:
    st.subheader("Goal Planning")
    st.markdown("#### Your Financial Goals")
    for goal in financial_goals:
        with st.expander(f"{goal}"):
            if goal == 'Emergency Fund':
                target_amount = monthly_expenses * 6
                current_progress = monthly_savings_goal
                months_to_goal = (target_amount - current_progress) / monthly_savings_goal if monthly_savings_goal > 0 else float('inf')
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Target Amount", f"LKR {target_amount:.2f}")
                    st.metric("Current Progress", f"LKR {current_progress:.2f}")
                with col2:
                    st.metric("Months to Goal", f"{months_to_goal:.0f}" if months_to_goal < 100 else "∞")
                    st.metric("Monthly Savings Needed", f"LKR {target_amount / 36:.2f}")
                st.progress(min(current_progress / target_amount, 1.0))
            elif goal == 'Vacation':
                vacation_cost = 3000
                vacation_months = 12
                monthly_needed = vacation_cost / vacation_months
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Estimated Cost", f"LKR {vacation_cost:.2f}")
                    st.metric("Timeline", f"{vacation_months} months")
                with col2:
                    st.metric("Monthly Savings Needed", f"LKR {monthly_needed:.2f}")
                    st.metric("Current Allocation", f"LKR {monthly_savings_goal * 0.3:.2f}")
                progress = (monthly_savings_goal * 0.3 * vacation_months) / vacation_cost
                st.progress(min(progress, 1.0))
            elif goal == 'Home Purchase':
                home_price = 300000
                down_payment = home_price * 0.2
                years_to_save = 5
                monthly_needed = down_payment / (years_to_save * 12)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Estimated Home Price", f"LKR {home_price:,.2f}")
                    st.metric("Down Payment (20%)", f"LKR {down_payment:,.2f}")
                with col2:
                    st.metric("Years to Save", f"{years_to_save}")
                    st.metric("Monthly Savings Needed", f"LKR {monthly_needed:.2f}")
                if monthly_needed > monthly_savings_goal:
                    st.warning(f"You need to save LKR {monthly_needed - monthly_savings_goal:.2f} more per month to reach this goal.")
                else:
                    st.success(f"Your current savings rate can achieve this goal!")

    st.markdown("#### Goal Planning Tools")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Savings Calculator**")
        custom_goal_amount = st.number_input("Goal Amount (LKR)", min_value=100, value=5000, step=100)
        custom_timeline = st.selectbox("Timeline", ["6 months", "1 year", "2 years", "3 years", "5 years"])
        timeline_mapping = {"6 months": 6, "1 year": 12, "2 years": 24, "3 years": 36, "5 years": 60}
        timeline_months = timeline_mapping.get(custom_timeline or "1 year", 12)
        required_monthly = custom_goal_amount / timeline_months
        st.metric("Required Monthly Savings", f"LKR {required_monthly:.2f}")
        if required_monthly <= monthly_savings_goal:
            st.success(f"Achievable with current savings rate!")
        else:
            additional_needed = required_monthly - monthly_savings_goal
            st.warning(f"Need LKR {additional_needed:.2f} more per month")
    with col2:
        st.markdown("**Progress Tracker**")
        if st.button("Add New Goal"):
            st.info("Feature coming soon! You'll be able to add custom financial goals with specific targets and timelines.")
        if st.button("View Goal Dashboard"):
            st.info("Navigate to the main dashboard to see all your goals in one place.")

# Action items and follow-ups
st.subheader("Action Items")
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### This Week")
    weekly_actions = [
        "Review and cancel unused subscriptions",
        "Set up automatic transfer to savings account",
        "Research high-yield savings accounts",
        "Create meal plan to reduce dining expenses"
    ]
    for action in weekly_actions:
        checked = st.checkbox(action, key=f"weekly_{action}")
        if checked:
            st.session_state.suggestion_history.append({
                'action': action,
                'completed_date': datetime.now(),
                'type': 'weekly_action'
            })
with col2:
    st.markdown("#### This Month")
    monthly_actions = [
        "Research investment options based on risk tolerance",
        "Build emergency fund to 3 months of expenses",
        "Negotiate better rates on insurance and utilities",
        "Track spending patterns for budget optimization"
    ]
    for action in monthly_actions:
        checked = st.checkbox(action, key=f"monthly_{action}")
        if checked:
            st.session_state.suggestion_history.append({
                'action': action,
                'completed_date': datetime.now(),
                'type': 'monthly_action'
            })

# Progress tracking
if st.session_state.suggestion_history:
    st.subheader("Progress Tracking")
    completed_suggestions = len([s for s in st.session_state.suggestion_history if s.get('status') == 'applied' or 'completed_date' in s])
    total_suggestions = len(weekly_actions) + len(monthly_actions) + len(savings_opportunities)
    progress_pct = min((completed_suggestions / total_suggestions) * 100, 100) if total_suggestions > 0 else 0
    st.progress(progress_pct / 100)
    st.write(f"Completed {completed_suggestions} out of {total_suggestions} suggestions ({progress_pct:.1f}%)")

# Export suggestions
st.subheader("Export & Share")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Export Action Plan"):
        action_plan = {
            'savings_opportunities': savings_opportunities,
            'investment_recommendations': investment_suggestions,
            'financial_goals': financial_goals,
            'risk_analysis': risks if 'risks' in locals() else [],
            'generated_date': datetime.now().isoformat()
        }
        st.download_button(
            label="Download Plan (JSON)",
            data=json.dumps(action_plan, indent=2, default=str),
            file_name=f"financial_action_plan_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
with col2:
    if st.button("Generate Report"):
        report = f"""
# Financial Advisory Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
## Summary
- Potential Monthly Savings: LKR {total_potential_savings:.2f}
- Investment Recommendation: LKR {recommended_amount:.2f}
- Risk Tolerance: {current_risk.title() if current_risk else 'Moderate'}
- Active Goals: {len(financial_goals)}
## Top Recommendations
{chr(10).join([f"• {opp['category'].replace('_', ' ').title()}: Save LKR {opp['potential_savings']:.2f}/month" for opp in savings_opportunities[:3]])}
## Next Steps
{chr(10).join([f"• {action}" for action in weekly_actions[:3]])}
        """
        st.download_button(
            label="Download Report (TXT)",
            data=report,
            file_name=f"financial_report_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
with col3:
    if st.button("Reset Preferences"):
        st.session_state.user_preferences = {
            'annual_savings_goal': 12000,
            'savings_goal': 1000,
            'risk_tolerance': 'moderate',
            'financial_goals': ['Emergency Fund', 'Vacation'],
            'budget_preferences': {
                'total_monthly_budget': 5000,
                'categories': {cat: 1.0 / len(categories) for cat in categories}
            }
        }
        st.session_state.suggestion_history = []
        st.success("Preferences reset!")
        st.rerun()
