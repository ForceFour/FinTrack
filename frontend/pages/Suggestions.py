"""
Suggestions Page - AI-powered financial recommendations and insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="Suggestions", page_icon="💡", layout="wide")

st.title("AI Financial Advisor")
st.markdown("### Personalized Recommendations & Smart Insights")

# Check if we have data
if 'transactions' not in st.session_state or not st.session_state.transactions:
    st.warning("No transaction data available. Please upload data first.")
    st.info("Use the sidebar navigation to go to 'Upload & Process' first.")
    st.stop()

# Get transaction data
df = pd.DataFrame(st.session_state.transactions)
df['date'] = pd.to_datetime(df['date'])
df['amount_abs'] = abs(df['amount'])
df['is_expense'] = df['amount'] < 0

# Add sample data if columns don't exist
if 'category' not in df.columns:
    categories = ['Food & Dining', 'Groceries', 'Transportation', 'Entertainment', 'Shopping', 'Utilities', 'Healthcare']
    df['category'] = np.random.choice(categories, len(df))

if 'merchant' not in df.columns:
    merchants = ['Starbucks', 'Walmart', 'Shell', 'Amazon', 'Netflix', 'Uber', 'Target', 'Costco']
    df['merchant'] = np.random.choice(merchants, len(df))

# Initialize suggestion state
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {
        'savings_goal': 1000,
        'risk_tolerance': 'moderate',
        'financial_goals': ['Emergency Fund', 'Vacation'],
        'budget_preferences': {}
    }

if 'suggestion_history' not in st.session_state:
    st.session_state.suggestion_history = []

# Sidebar for preferences
with st.sidebar:
    st.header("Your Preferences")
    
    # Savings goal
    savings_goal = st.number_input(
        "Monthly Savings Goal ($)",
        min_value=0,
        value=st.session_state.user_preferences['savings_goal'],
        step=50
    )
    st.session_state.user_preferences['savings_goal'] = savings_goal
    
    # Risk tolerance
    risk_tolerance = st.selectbox(
        "Risk Tolerance",
        ['Conservative', 'Moderate', 'Aggressive'],
        index=['Conservative', 'Moderate', 'Aggressive'].index(st.session_state.user_preferences['risk_tolerance'].title())
    )
    st.session_state.user_preferences['risk_tolerance'] = risk_tolerance.lower()
    
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
    
    # Quick actions
    st.markdown("#### Quick Actions")

    if st.button("Refresh Suggestions"):
        st.rerun()

    if st.button("Generate New Analysis"):
        # Trigger new AI analysis
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

    # Calculate spending by category
    expense_df = df[df['is_expense']].copy()
    category_spending = expense_df.groupby('category')['amount_abs'].agg(['sum', 'mean', 'count']).round(2)
    category_spending.columns = ['Total', 'Average', 'Count']
    category_spending = category_spending.sort_values('Total', ascending=False)
    
    # Generate savings suggestions
    savings_opportunities = []
    
    # Food & Dining suggestions
    if 'Food & Dining' in category_spending.index:
        food_spending = category_spending.loc['Food & Dining', 'Total']
        if food_spending > 400:  # Threshold for suggestions
            potential_savings = food_spending * 0.25  # 25% reduction
            savings_opportunities.append({
                'category': 'Food & Dining',
                'current_spending': food_spending,
                'suggested_spending': food_spending - potential_savings,
                'potential_savings': potential_savings,
                'difficulty': 'Medium',
                'suggestions': [
                    'Cook more meals at home',
                    'Use meal planning apps',
                    'Take advantage of happy hour prices',
                    'Use restaurant coupons and deals'
                ]
            })
    
    # Transportation suggestions
    if 'Transportation' in category_spending.index:
        transport_spending = category_spending.loc['Transportation', 'Total']
        if transport_spending > 200:
            potential_savings = transport_spending * 0.20
            savings_opportunities.append({
                'category': 'Transportation',
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
    
    # Entertainment suggestions
    if 'Entertainment' in category_spending.index:
        entertainment_spending = category_spending.loc['Entertainment', 'Total']
        if entertainment_spending > 150:
            potential_savings = entertainment_spending * 0.30
            savings_opportunities.append({
                'category': 'Entertainment',
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
    
    # Display savings opportunities
    total_potential_savings = sum(opp['potential_savings'] for opp in savings_opportunities)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Potential Monthly Savings", f"${total_potential_savings:.2f}")
    
    with col2:
        st.metric("Annual Savings Potential", f"${total_potential_savings * 12:.2f}")
    
    with col3:
        current_total = expense_df['amount_abs'].sum()
        savings_percentage = (total_potential_savings / current_total) * 100
        st.metric("Savings Percentage", f"{savings_percentage:.1f}%")
    
    with col4:
        st.metric("Categories to Optimize", len(savings_opportunities))
    
    # Detailed savings opportunities
    for opp in savings_opportunities:
        with st.expander(f"{opp['category']} - Save ${opp['potential_savings']:.2f}/month"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current vs Suggested Spending:**")
                
                # Create comparison chart
                comparison_data = {
                    'Type': ['Current', 'Suggested'],
                    'Amount': [opp['current_spending'], opp['suggested_spending']]
                }
                
                fig_comparison = px.bar(
                    comparison_data,
                    x='Type',
                    y='Amount',
                    title=f"{opp['category']} Spending Comparison",
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
                
                if st.button(f"Apply to {opp['category']}", key=f"apply_{opp['category']}"):
                    # Save suggestion to history
                    st.session_state.suggestion_history.append({
                        'category': opp['category'],
                        'suggestion': 'Spending reduction plan',
                        'potential_savings': opp['potential_savings'],
                        'applied_date': datetime.now(),
                        'status': 'applied'
                    })
                    st.success(f"Savings plan applied to {opp['category']}!")

with tab2:
    st.subheader("Budget Optimization")

    # Current budget vs recommended
    current_spending = expense_df.groupby('category')['amount_abs'].sum()
    
    # Recommended budget allocation (as percentages)
    recommended_allocation = {
        'Food & Dining': 0.25,
        'Groceries': 0.15,
        'Transportation': 0.15,
        'Entertainment': 0.10,
        'Shopping': 0.10,
        'Utilities': 0.15,
        'Healthcare': 0.05,
        'Other': 0.05
    }
    
    total_spending = current_spending.sum()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Current Budget Distribution")
        
        fig_current = px.pie(
            values=current_spending.values,
            names=current_spending.index,
            title="Current Spending Distribution"
        )
        st.plotly_chart(fig_current, use_container_width=True)
    
    with col2:
        st.markdown("#### Recommended Budget Distribution")

        recommended_amounts = {cat: total_spending * pct for cat, pct in recommended_allocation.items()}
        
        fig_recommended = px.pie(
            values=list(recommended_amounts.values()),
            names=list(recommended_amounts.keys()),
            title="Recommended Spending Distribution"
        )
        st.plotly_chart(fig_recommended, use_container_width=True)
    
    # Budget comparison table
    st.markdown("#### Budget Comparison & Recommendations")

    budget_comparison = []
    for category in current_spending.index:
        current_amount = current_spending[category]
        current_pct = (current_amount / total_spending) * 100
        
        recommended_pct = recommended_allocation.get(category, 0.05) * 100
        recommended_amount = total_spending * (recommended_pct / 100)
        
        difference = current_amount - recommended_amount
        status = "Over Budget" if difference > 0 else "Under Budget" if difference < -10 else "On Track"
        
        budget_comparison.append({
            'Category': category,
            'Current Amount': f"${current_amount:.2f}",
            'Current %': f"{current_pct:.1f}%",
            'Recommended %': f"{recommended_pct:.1f}%",
            'Recommended Amount': f"${recommended_amount:.2f}",
            'Difference': f"${difference:.2f}",
            'Status': status
        })
    
    budget_df = pd.DataFrame(budget_comparison)
    
    # Color code the status
    def color_status(val):
        if val == 'Over Budget':
            return 'background-color: #ffebee'
        elif val == 'Under Budget':
            return 'background-color: #e8f5e8'
        else:
            return 'background-color: #fff3e0'
    
    styled_df = budget_df.style.applymap(color_status, subset=['Status'])
    st.dataframe(styled_df, use_container_width=True)

with tab3:
    st.subheader("Investment Ideas")

    # Calculate available funds for investment
    total_income = df[~df['is_expense']]['amount_abs'].sum() if not df[~df['is_expense']].empty else 5000  # Default if no income data
    total_expenses = expense_df['amount_abs'].sum()
    available_for_investment = max(0, total_income - total_expenses - savings_goal)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Available for Investment", f"${available_for_investment:.2f}")
    
    with col2:
        st.metric("Risk Tolerance", risk_tolerance.title())
    
    with col3:
        recommended_investment_pct = {'conservative': 0.6, 'moderate': 0.8, 'aggressive': 1.0}[risk_tolerance]
        recommended_amount = available_for_investment * recommended_investment_pct
        st.metric("Recommended Investment", f"${recommended_amount:.2f}")
    
    # Investment recommendations based on risk tolerance
    if risk_tolerance == 'conservative':
        investment_suggestions = [
            {
                'type': 'High-Yield Savings Account',
                'allocation': 40,
                'expected_return': 4.5,
                'risk_level': 'Very Low',
                'description': 'Safe option for emergency fund and short-term goals'
            },
            {
                'type': 'Government Bonds',
                'allocation': 30,
                'expected_return': 3.8,
                'risk_level': 'Low',
                'description': 'Stable income with government backing'
            },
            {
                'type': 'Bond Index Funds',
                'allocation': 20,
                'expected_return': 4.2,
                'risk_level': 'Low',
                'description': 'Diversified bond exposure with low fees'
            },
            {
                'type': 'Conservative Balanced Funds',
                'allocation': 10,
                'expected_return': 5.5,
                'risk_level': 'Low-Medium',
                'description': 'Mix of bonds and conservative stocks'
            }
        ]
    elif risk_tolerance == 'moderate':
        investment_suggestions = [
            {
                'type': 'Index Funds (S&P 500)',
                'allocation': 40,
                'expected_return': 8.0,
                'risk_level': 'Medium',
                'description': 'Broad market exposure with reasonable fees'
            },
            {
                'type': 'Bond Index Funds',
                'allocation': 25,
                'expected_return': 4.2,
                'risk_level': 'Low',
                'description': 'Stability and income generation'
            },
            {
                'type': 'International Funds',
                'allocation': 20,
                'expected_return': 7.5,
                'risk_level': 'Medium',
                'description': 'Global diversification'
            },
            {
                'type': 'REIT Funds',
                'allocation': 15,
                'expected_return': 6.8,
                'risk_level': 'Medium',
                'description': 'Real estate exposure for diversification'
            }
        ]
    else:  # aggressive
        investment_suggestions = [
            {
                'type': 'Growth Stock Funds',
                'allocation': 50,
                'expected_return': 10.0,
                'risk_level': 'High',
                'description': 'High growth potential with higher volatility'
            },
            {
                'type': 'Technology Sector ETFs',
                'allocation': 20,
                'expected_return': 12.0,
                'risk_level': 'High',
                'description': 'Exposure to high-growth tech companies'
            },
            {
                'type': 'Emerging Markets',
                'allocation': 15,
                'expected_return': 9.5,
                'risk_level': 'High',
                'description': 'International growth opportunities'
            },
            {
                'type': 'Small-Cap Funds',
                'allocation': 15,
                'expected_return': 11.0,
                'risk_level': 'High',
                'description': 'Small company growth potential'
            }
        ]
    
    # Display investment allocation
    allocation_df = pd.DataFrame(investment_suggestions)
    
    fig_allocation = px.pie(
        allocation_df,
        values='allocation',
        names='type',
        title=f"Recommended Investment Allocation - {risk_tolerance.title()} Risk"
    )
    st.plotly_chart(fig_allocation, use_container_width=True)
    
    # Investment details
    st.markdown("#### 💼 Investment Recommendations")
    
    for inv in investment_suggestions:
        with st.expander(f"{inv['type']} - {inv['allocation']}% allocation"):
            col1, col2 = st.columns(2)
            
            with col1:
                amount = recommended_amount * (inv['allocation'] / 100)
                annual_return = amount * (inv['expected_return'] / 100)
                
                st.metric("Suggested Amount", f"${amount:.2f}")
                st.metric("Expected Annual Return", f"${annual_return:.2f}")
                st.metric("Expected Return Rate", f"{inv['expected_return']:.1f}%")
            
            with col2:
                risk_colors = {
                    'Very Low': 'green',
                    'Low': 'blue',
                    'Low-Medium': 'orange',
                    'Medium': 'orange',
                    'High': 'red'
                }
                risk_color = risk_colors.get(inv['risk_level'], 'gray')
                
                st.markdown(f"**Risk Level:** :{risk_color}[{inv['risk_level']}]")
                st.markdown(f"**Description:** {inv['description']}")
                
                if st.button(f"Learn More", key=f"learn_{inv['type']}"):
                    st.info(f"Research {inv['type']} options from reputable brokers like Vanguard, Fidelity, or Schwab.")

with tab4:
    st.subheader("Risk Analysis")

    # Financial health metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Emergency fund ratio
    monthly_expenses = expense_df['amount_abs'].sum()
    emergency_fund_months = savings_goal / monthly_expenses if monthly_expenses > 0 else 0
    
    with col1:
        color = "normal" if emergency_fund_months >= 3 else "inverse"
        st.metric("Emergency Fund (Months)", f"{emergency_fund_months:.1f}", delta_color=color)
    
    # Spending volatility
    daily_spending = expense_df.groupby(expense_df['date'].dt.date)['amount_abs'].sum()
    spending_volatility = daily_spending.std() / daily_spending.mean() if len(daily_spending) > 1 else 0
    
    with col2:
        volatility_status = "Low" if spending_volatility < 0.5 else "Medium" if spending_volatility < 1.0 else "High"
        st.metric("Spending Volatility", volatility_status)
    
    # Subscription/recurring expense ratio
    recurring_keywords = ['netflix', 'spotify', 'subscription', 'monthly', 'annual']
    recurring_expenses = expense_df[
        expense_df['description'].str.lower().str.contains('|'.join(recurring_keywords), na=False)
    ]['amount_abs'].sum()
    recurring_ratio = (recurring_expenses / monthly_expenses) * 100 if monthly_expenses > 0 else 0
    
    with col3:
        st.metric("Recurring Expenses", f"{recurring_ratio:.1f}%")
    
    # Large transaction frequency
    large_threshold = expense_df['amount_abs'].quantile(0.9)
    large_transactions = len(expense_df[expense_df['amount_abs'] > large_threshold])
    
    with col4:
        st.metric("Large Transactions", large_transactions)
    
    # Risk indicators
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
            'action': 'Implement a 24-hour waiting period for purchases over $100.'
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

    # Display current goals
    st.markdown("#### Your Financial Goals")

    for goal in financial_goals:
        with st.expander(f"{goal}"):
            # Goal-specific recommendations
            if goal == 'Emergency Fund':
                target_amount = monthly_expenses * 6
                current_progress = savings_goal
                months_to_goal = (target_amount - current_progress) / savings_goal if savings_goal > 0 else float('inf')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Target Amount", f"${target_amount:.2f}")
                    st.metric("Current Progress", f"${current_progress:.2f}")
                with col2:
                    st.metric("Months to Goal", f"{months_to_goal:.0f}" if months_to_goal < 100 else "∞")
                    st.metric("Monthly Savings Needed", f"${target_amount / 36:.2f}")  # 3-year timeline
                
                st.progress(min(current_progress / target_amount, 1.0))
                
            elif goal == 'Vacation':
                vacation_cost = 3000  # Estimated
                vacation_months = 12   # Timeline
                monthly_needed = vacation_cost / vacation_months
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Estimated Cost", f"${vacation_cost:.2f}")
                    st.metric("Timeline", f"{vacation_months} months")
                with col2:
                    st.metric("Monthly Savings Needed", f"${monthly_needed:.2f}")
                    st.metric("Current Allocation", f"${savings_goal * 0.3:.2f}")  # 30% of savings
                
                progress = (savings_goal * 0.3 * vacation_months) / vacation_cost
                st.progress(min(progress, 1.0))
                
            elif goal == 'Home Purchase':
                home_price = 300000
                down_payment = home_price * 0.2
                years_to_save = 5
                monthly_needed = down_payment / (years_to_save * 12)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Estimated Home Price", f"${home_price:,.2f}")
                    st.metric("Down Payment (20%)", f"${down_payment:,.2f}")
                with col2:
                    st.metric("Years to Save", f"{years_to_save}")
                    st.metric("Monthly Savings Needed", f"${monthly_needed:.2f}")
                
                if monthly_needed > savings_goal:
                    st.warning(f"You need to save ${monthly_needed - savings_goal:.2f} more per month to reach this goal.")
                else:
                    st.success(f"Your current savings rate can achieve this goal!")
    
    # Goal planning tools
    st.markdown("#### Goal Planning Tools")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Savings Calculator**")
        
        custom_goal_amount = st.number_input("Goal Amount ($)", min_value=100, value=5000, step=100)
        custom_timeline = st.selectbox("Timeline", ["6 months", "1 year", "2 years", "3 years", "5 years"])
        
        timeline_months = {
            "6 months": 6, "1 year": 12, "2 years": 24, 
            "3 years": 36, "5 years": 60
        }[custom_timeline]
        
        required_monthly = custom_goal_amount / timeline_months
        
        st.metric("Required Monthly Savings", f"${required_monthly:.2f}")
        
        if required_monthly <= savings_goal:
            st.success(f"Achievable with current savings rate!")
        else:
            additional_needed = required_monthly - savings_goal
            st.warning(f"Need ${additional_needed:.2f} more per month")

    with col2:
        st.markdown("**Progress Tracker**")
        
        if st.button("Add New Goal"):
            # In a real app, this would open a form
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
    
    progress_pct = (completed_suggestions / total_suggestions) * 100 if total_suggestions > 0 else 0
    
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
        # Create a summary report
        report = f"""
# Financial Advisory Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary
- Potential Monthly Savings: ${total_potential_savings:.2f}
- Investment Recommendation: ${recommended_amount:.2f}
- Risk Tolerance: {risk_tolerance.title()}
- Active Goals: {len(financial_goals)}

## Top Recommendations
{chr(10).join([f"• {opp['category']}: Save ${opp['potential_savings']:.2f}/month" for opp in savings_opportunities[:3]])}

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
            'savings_goal': 1000,
            'risk_tolerance': 'moderate',
            'financial_goals': ['Emergency Fund', 'Vacation'],
            'budget_preferences': {}
        }
        st.session_state.suggestion_history = []
        st.success("Preferences reset!")
        st.rerun()
