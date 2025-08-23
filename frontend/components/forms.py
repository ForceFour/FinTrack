"""
Form Components - Reusable form components for the Streamlit application
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import json

def transaction_entry_form(key_suffix="", submit_label="Add Transaction"):
    """Create a form for manual transaction entry"""
    st.subheader("✏️ Manual Transaction Entry")
    
    with st.form(f"transaction_form_{key_suffix}"):
        col1, col2 = st.columns(2)
        
        with col1:
            entry_date = st.date_input(
                "Date",
                value=date.today(),
                key=f"date_{key_suffix}"
            )
            
            amount = st.number_input(
                "Amount",
                step=0.01,
                format="%.2f",
                help="Use negative values for expenses, positive for income",
                key=f"amount_{key_suffix}"
            )
            
            description = st.text_input(
                "Description",
                placeholder="Enter transaction description",
                key=f"description_{key_suffix}"
            )
        
        with col2:
            category_options = [
                'Food & Dining', 'Groceries', 'Transportation', 'Entertainment',
                'Shopping', 'Utilities', 'Healthcare', 'Income', 'Transfer', 'Other'
            ]
            
            category = st.selectbox(
                "Category",
                options=category_options,
                key=f"category_{key_suffix}"
            )
            
            merchant = st.text_input(
                "Merchant/Payee",
                placeholder="Enter merchant or payee name",
                key=f"merchant_{key_suffix}"
            )
            
            payment_method_options = [
                'Credit Card', 'Debit Card', 'Cash', 'Bank Transfer', 
                'Digital Wallet', 'Check', 'Other'
            ]
            
            payment_method = st.selectbox(
                "Payment Method",
                options=payment_method_options,
                key=f"payment_method_{key_suffix}"
            )
        
        # Additional fields
        notes = st.text_area(
            "Notes (Optional)",
            placeholder="Add any additional notes about this transaction",
            key=f"notes_{key_suffix}"
        )
        
        submitted = st.form_submit_button(submit_label, type="primary")
        
        if submitted:
            if description.strip():
                transaction_data = {
                    'date': entry_date.strftime('%Y-%m-%d'),
                    'amount': amount,
                    'description': description.strip(),
                    'category': category,
                    'merchant': merchant.strip() if merchant.strip() else 'Unknown',
                    'payment_method': payment_method,
                    'notes': notes.strip() if notes.strip() else None,
                    'created_at': datetime.now().isoformat()
                }
                
                return transaction_data
            else:
                st.error("❌ Description is required!")
                return None
    
    return None

def budget_setup_form(existing_budget=None, key_suffix=""):
    """Create a form for setting up budget categories"""
    st.subheader("💰 Budget Setup")
    
    # Default budget categories with suggested amounts
    default_categories = {
        'Food & Dining': 400,
        'Groceries': 300,
        'Transportation': 200,
        'Entertainment': 150,
        'Shopping': 200,
        'Utilities': 250,
        'Healthcare': 100,
        'Savings': 500,
        'Other': 100
    }
    
    if existing_budget:
        default_categories.update(existing_budget)
    
    with st.form(f"budget_form_{key_suffix}"):
        st.markdown("#### 📊 Monthly Budget by Category")
        
        budget_data = {}
        
        # Create budget input for each category
        col1, col2 = st.columns(2)
        categories = list(default_categories.keys())
        
        for i, (category, default_amount) in enumerate(default_categories.items()):
            with col1 if i % 2 == 0 else col2:
                budget_data[category] = st.number_input(
                    f"{category}",
                    min_value=0.0,
                    value=float(default_amount),
                    step=10.0,
                    key=f"budget_{category}_{key_suffix}"
                )
        
        # Total budget calculation
        total_budget = sum(budget_data.values())
        st.markdown(f"**Total Monthly Budget: ${total_budget:,.2f}**")
        
        # Budget period
        budget_period = st.selectbox(
            "Budget Period",
            options=["Monthly", "Weekly", "Bi-weekly", "Quarterly"],
            key=f"budget_period_{key_suffix}"
        )
        
        # Additional settings
        st.markdown("#### ⚙️ Budget Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            alert_threshold = st.slider(
                "Alert Threshold (%)",
                min_value=50,
                max_value=100,
                value=80,
                help="Get alerts when spending reaches this percentage of budget",
                key=f"alert_threshold_{key_suffix}"
            )
        
        with col2:
            rollover_unused = st.checkbox(
                "Rollover unused budget",
                value=True,
                help="Allow unused budget to roll over to next period",
                key=f"rollover_{key_suffix}"
            )
        
        submitted = st.form_submit_button("💾 Save Budget", type="primary")
        
        if submitted:
            budget_config = {
                'categories': budget_data,
                'total_budget': total_budget,
                'period': budget_period,
                'alert_threshold': alert_threshold,
                'rollover_unused': rollover_unused,
                'created_at': datetime.now().isoformat()
            }
            
            return budget_config
    
    return None

def category_rules_form(key_suffix=""):
    """Create a form for setting up categorization rules"""
    st.subheader("🤖 Auto-Categorization Rules")
    
    with st.form(f"category_rules_form_{key_suffix}"):
        st.markdown("#### 🏷️ Create New Rule")
        
        rule_type = st.selectbox(
            "Rule Type",
            options=["Keyword Match", "Amount Range", "Merchant Pattern", "Description Pattern"],
            key=f"rule_type_{key_suffix}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if rule_type == "Keyword Match":
                keywords = st.text_area(
                    "Keywords (one per line)",
                    placeholder="restaurant\ncoffee\nfood",
                    key=f"keywords_{key_suffix}"
                )
                
                case_sensitive = st.checkbox(
                    "Case sensitive",
                    key=f"case_sensitive_{key_suffix}"
                )
                
            elif rule_type == "Amount Range":
                min_amount = st.number_input(
                    "Minimum Amount",
                    min_value=0.0,
                    step=1.0,
                    key=f"min_amount_{key_suffix}"
                )
                
                max_amount = st.number_input(
                    "Maximum Amount",
                    min_value=0.0,
                    step=1.0,
                    key=f"max_amount_{key_suffix}"
                )
                
            elif rule_type in ["Merchant Pattern", "Description Pattern"]:
                pattern = st.text_input(
                    f"{rule_type.split()[0]} Pattern",
                    placeholder="Enter pattern or regex",
                    key=f"pattern_{key_suffix}"
                )
                
                use_regex = st.checkbox(
                    "Use regular expressions",
                    key=f"use_regex_{key_suffix}"
                )
        
        with col2:
            category_options = [
                'Food & Dining', 'Groceries', 'Transportation', 'Entertainment',
                'Shopping', 'Utilities', 'Healthcare', 'Income', 'Transfer', 'Other'
            ]
            
            target_category = st.selectbox(
                "Assign to Category",
                options=category_options,
                key=f"target_category_{key_suffix}"
            )
            
            confidence_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.1,
                max_value=1.0,
                value=0.8,
                step=0.1,
                key=f"confidence_{key_suffix}"
            )
            
            rule_priority = st.selectbox(
                "Rule Priority",
                options=["High", "Medium", "Low"],
                index=1,
                key=f"priority_{key_suffix}"
            )
        
        rule_description = st.text_area(
            "Rule Description (Optional)",
            placeholder="Describe what this rule does",
            key=f"rule_description_{key_suffix}"
        )
        
        submitted = st.form_submit_button("➕ Add Rule", type="primary")
        
        if submitted:
            rule_data = {
                'type': rule_type,
                'target_category': target_category,
                'confidence_threshold': confidence_threshold,
                'priority': rule_priority,
                'description': rule_description,
                'created_at': datetime.now().isoformat()
            }
            
            # Add type-specific data
            if rule_type == "Keyword Match":
                rule_data['keywords'] = [kw.strip() for kw in keywords.split('\n') if kw.strip()]
                rule_data['case_sensitive'] = case_sensitive
                
            elif rule_type == "Amount Range":
                rule_data['min_amount'] = min_amount
                rule_data['max_amount'] = max_amount
                
            elif rule_type in ["Merchant Pattern", "Description Pattern"]:
                rule_data['pattern'] = pattern
                rule_data['use_regex'] = use_regex
            
            return rule_data
    
    return None

def settings_form(current_settings=None, key_suffix=""):
    """Create a form for application settings"""
    st.subheader("⚙️ Application Settings")
    
    default_settings = {
        'currency': 'USD',
        'date_format': 'YYYY-MM-DD',
        'number_format': 'US',
        'timezone': 'UTC',
        'auto_categorize': True,
        'fraud_detection': True,
        'email_notifications': True,
        'data_retention_days': 2555,  # 7 years
        'session_timeout': 30
    }
    
    if current_settings:
        default_settings.update(current_settings)
    
    with st.form(f"settings_form_{key_suffix}"):
        st.markdown("#### 🌐 General Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            currency = st.selectbox(
                "Currency",
                options=['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY'],
                index=['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY'].index(default_settings['currency']),
                key=f"currency_{key_suffix}"
            )
            
            date_format = st.selectbox(
                "Date Format",
                options=['YYYY-MM-DD', 'MM/DD/YYYY', 'DD/MM/YYYY'],
                index=['YYYY-MM-DD', 'MM/DD/YYYY', 'DD/MM/YYYY'].index(default_settings['date_format']),
                key=f"date_format_{key_suffix}"
            )
            
            number_format = st.selectbox(
                "Number Format",
                options=['US', 'European'],
                index=['US', 'European'].index(default_settings['number_format']),
                key=f"number_format_{key_suffix}"
            )
        
        with col2:
            timezone = st.selectbox(
                "Timezone",
                options=['UTC', 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific', 'Europe/London'],
                index=['UTC', 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific', 'Europe/London'].index(default_settings['timezone']),
                key=f"timezone_{key_suffix}"
            )
            
            session_timeout = st.number_input(
                "Session Timeout (minutes)",
                min_value=5,
                max_value=480,
                value=default_settings['session_timeout'],
                key=f"session_timeout_{key_suffix}"
            )
        
        st.markdown("#### 🤖 AI & Automation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_categorize = st.checkbox(
                "Auto-categorize transactions",
                value=default_settings['auto_categorize'],
                key=f"auto_categorize_{key_suffix}"
            )
            
            fraud_detection = st.checkbox(
                "Enable fraud detection",
                value=default_settings['fraud_detection'],
                key=f"fraud_detection_{key_suffix}"
            )
        
        with col2:
            email_notifications = st.checkbox(
                "Email notifications",
                value=default_settings['email_notifications'],
                key=f"email_notifications_{key_suffix}"
            )
        
        st.markdown("#### 🗂️ Data Management")
        
        data_retention_days = st.number_input(
            "Data Retention (days)",
            min_value=30,
            max_value=3650,
            value=default_settings['data_retention_days'],
            help="How long to keep transaction data",
            key=f"data_retention_{key_suffix}"
        )
        
        submitted = st.form_submit_button("💾 Save Settings", type="primary")
        
        if submitted:
            settings_data = {
                'currency': currency,
                'date_format': date_format,
                'number_format': number_format,
                'timezone': timezone,
                'auto_categorize': auto_categorize,
                'fraud_detection': fraud_detection,
                'email_notifications': email_notifications,
                'data_retention_days': data_retention_days,
                'session_timeout': session_timeout,
                'updated_at': datetime.now().isoformat()
            }
            
            return settings_data
    
    return None

def file_upload_form(accepted_types=None, max_file_size=10, key_suffix=""):
    """Create a file upload form with validation"""
    if accepted_types is None:
        accepted_types = ['csv', 'xlsx', 'xls', 'json']
    
    st.subheader("📁 File Upload")
    
    with st.form(f"upload_form_{key_suffix}"):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=accepted_types,
            help=f"Supported formats: {', '.join(accepted_types)}. Max size: {max_file_size}MB",
            key=f"file_upload_{key_suffix}"
        )
        
        if uploaded_file:
            # File information
            file_info = {
                'name': uploaded_file.name,
                'size': uploaded_file.size,
                'type': uploaded_file.type
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**File Information:**")
                st.write(f"• Name: {file_info['name']}")
                st.write(f"• Size: {file_info['size'] / 1024:.2f} KB")
                st.write(f"• Type: {file_info['type']}")
            
            with col2:
                # Processing options
                st.markdown("**Processing Options:**")
                
                auto_categorize = st.checkbox(
                    "Auto-categorize transactions",
                    value=True,
                    key=f"auto_cat_upload_{key_suffix}"
                )
                
                detect_duplicates = st.checkbox(
                    "Detect duplicate transactions",
                    value=True,
                    key=f"detect_dups_{key_suffix}"
                )
                
                validate_data = st.checkbox(
                    "Validate data quality",
                    value=True,
                    key=f"validate_{key_suffix}"
                )
        
        submitted = st.form_submit_button("🚀 Process File", type="primary")
        
        if submitted and uploaded_file:
            processing_options = {
                'auto_categorize': auto_categorize,
                'detect_duplicates': detect_duplicates,
                'validate_data': validate_data
            }
            
            return uploaded_file, processing_options
        elif submitted and not uploaded_file:
            st.error("❌ Please select a file to upload!")
    
    return None, None

def goal_setup_form(existing_goals=None, key_suffix=""):
    """Create a form for setting up financial goals"""
    st.subheader("🎯 Financial Goals Setup")
    
    with st.form(f"goal_form_{key_suffix}"):
        col1, col2 = st.columns(2)
        
        with col1:
            goal_name = st.text_input(
                "Goal Name",
                placeholder="e.g., Emergency Fund, Vacation, New Car",
                key=f"goal_name_{key_suffix}"
            )
            
            goal_type = st.selectbox(
                "Goal Type",
                options=["Savings", "Debt Payoff", "Investment", "Purchase", "Other"],
                key=f"goal_type_{key_suffix}"
            )
            
            target_amount = st.number_input(
                "Target Amount ($)",
                min_value=0.0,
                step=100.0,
                key=f"target_amount_{key_suffix}"
            )
        
        with col2:
            target_date = st.date_input(
                "Target Date",
                min_value=date.today(),
                key=f"target_date_{key_suffix}"
            )
            
            priority = st.selectbox(
                "Priority",
                options=["High", "Medium", "Low"],
                index=1,
                key=f"priority_{key_suffix}"
            )
            
            current_amount = st.number_input(
                "Current Amount ($)",
                min_value=0.0,
                step=10.0,
                key=f"current_amount_{key_suffix}"
            )
        
        description = st.text_area(
            "Description (Optional)",
            placeholder="Describe your goal and why it's important to you",
            key=f"goal_description_{key_suffix}"
        )
        
        # Calculate monthly savings needed
        if target_amount > current_amount and target_date > date.today():
            remaining_amount = target_amount - current_amount
            days_remaining = (target_date - date.today()).days
            months_remaining = max(1, days_remaining / 30.44)  # Average days per month
            monthly_needed = remaining_amount / months_remaining
            
            st.info(f"💡 You need to save approximately **${monthly_needed:.2f} per month** to reach this goal.")
        
        submitted = st.form_submit_button("🎯 Create Goal", type="primary")
        
        if submitted:
            if goal_name.strip() and target_amount > 0:
                goal_data = {
                    'name': goal_name.strip(),
                    'type': goal_type,
                    'target_amount': target_amount,
                    'current_amount': current_amount,
                    'target_date': target_date.isoformat(),
                    'priority': priority,
                    'description': description.strip() if description.strip() else None,
                    'created_at': datetime.now().isoformat(),
                    'status': 'active'
                }
                
                return goal_data
            else:
                st.error("❌ Goal name and target amount are required!")
    
    return None

def feedback_form(key_suffix=""):
    """Create a feedback form"""
    st.subheader("💬 Feedback")
    
    with st.form(f"feedback_form_{key_suffix}"):
        feedback_type = st.selectbox(
            "Feedback Type",
            options=["Bug Report", "Feature Request", "General Feedback", "Support Request"],
            key=f"feedback_type_{key_suffix}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            rating = st.slider(
                "Overall Rating",
                min_value=1,
                max_value=5,
                value=3,
                key=f"rating_{key_suffix}"
            )
        
        with col2:
            contact_email = st.text_input(
                "Email (Optional)",
                placeholder="your.email@example.com",
                key=f"email_{key_suffix}"
            )
        
        subject = st.text_input(
            "Subject",
            placeholder="Brief description of your feedback",
            key=f"subject_{key_suffix}"
        )
        
        message = st.text_area(
            "Message",
            placeholder="Please provide detailed feedback...",
            height=150,
            key=f"message_{key_suffix}"
        )
        
        submitted = st.form_submit_button("📤 Submit Feedback", type="primary")
        
        if submitted:
            if subject.strip() and message.strip():
                feedback_data = {
                    'type': feedback_type,
                    'rating': rating,
                    'subject': subject.strip(),
                    'message': message.strip(),
                    'email': contact_email.strip() if contact_email.strip() else None,
                    'submitted_at': datetime.now().isoformat()
                }
                
                return feedback_data
            else:
                st.error("❌ Subject and message are required!")
    
    return None
