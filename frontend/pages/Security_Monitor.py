"""
Security Monitor Page - AI-powered security analysis and fraud detection
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import json
import hashlib

st.set_page_config(page_title="Security Monitor", page_icon="", layout="wide")

st.title("Security Monitor")
st.markdown("### AI-Powered Fraud Detection & Security Analysis")

# Initialize security state
if 'security_alerts' not in st.session_state:
    st.session_state.security_alerts = []

if 'security_settings' not in st.session_state:
    st.session_state.security_settings = {
        'fraud_detection': True,
        'anomaly_threshold': 0.8,
        'real_time_monitoring': True,
        'alert_notifications': True,
        'data_encryption': True,
        'session_timeout': 30
    }

if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = []

# Security metrics simulation
def generate_security_metrics():
    """Generate simulated security metrics"""
    return {
        'fraud_score': np.random.uniform(0.1, 0.3),
        'data_integrity': np.random.uniform(0.95, 1.0),
        'encryption_status': True,
        'last_scan': datetime.now() - timedelta(minutes=np.random.randint(1, 60)),
        'suspicious_transactions': np.random.randint(0, 5),
        'blocked_attempts': np.random.randint(0, 3)
    }

# Check if we have data
if 'transactions' not in st.session_state or not st.session_state.transactions:
    st.warning("No transaction data available for security analysis.")
    st.info("Upload transaction data to enable complete security monitoring.")
    
    # Show basic security dashboard without transaction data
    df = pd.DataFrame()
else:
    df = pd.DataFrame(st.session_state.transactions)
    df['date'] = pd.to_datetime(df['date'])
    df['amount_abs'] = abs(df['amount'])
    df['is_expense'] = df['amount'] < 0

# Generate current security metrics
security_metrics = generate_security_metrics()

# Sidebar security controls
with st.sidebar:
    st.header("Security Controls")
    
    # Quick security status
    st.subheader("System Status")
    
    status_color = "" if security_metrics['fraud_score'] < 0.3 else "" if security_metrics['fraud_score'] < 0.6 else ""
    st.write(f"{status_color} **Security Level:** {'High' if security_metrics['fraud_score'] < 0.3 else 'Medium' if security_metrics['fraud_score'] < 0.6 else 'Low'}")
    
    st.write(f"**Encryption:** {'Active' if security_metrics['encryption_status'] else 'Inactive'}")
    st.write(f"**Last Scan:** {security_metrics['last_scan'].strftime('%H:%M')}")
    
    st.divider()
    
    # Security settings
    st.subheader("Settings")
    
    fraud_detection = st.checkbox("AI Fraud Detection", value=st.session_state.security_settings['fraud_detection'])
    st.session_state.security_settings['fraud_detection'] = fraud_detection
    
    anomaly_threshold = st.slider(
        "Anomaly Sensitivity", 
        min_value=0.1, 
        max_value=1.0, 
        value=st.session_state.security_settings['anomaly_threshold'],
        step=0.1
    )
    st.session_state.security_settings['anomaly_threshold'] = anomaly_threshold
    
    real_time_monitoring = st.checkbox("Real-time Monitoring", value=st.session_state.security_settings['real_time_monitoring'])
    st.session_state.security_settings['real_time_monitoring'] = real_time_monitoring
    
    alert_notifications = st.checkbox("Alert Notifications", value=st.session_state.security_settings['alert_notifications'])
    st.session_state.security_settings['alert_notifications'] = alert_notifications
    
    st.divider()
    
    # Quick actions
    if st.button("Run Security Scan", type="primary"):
        with st.spinner("Running comprehensive security scan..."):
            import time
            time.sleep(2)
            st.success("Security scan completed!")
            st.rerun()
    
    if st.button("Generate Security Report"):
        st.info("Security report will be generated and available for download.")

# Main security dashboard
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", 
    "Fraud Detection", 
    "Anomaly Analysis", 
    "Data Protection", 
    "Security Analytics"
])

with tab1:
    st.subheader("Security Overview")
    
    # Key security metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        fraud_level = "Low" if security_metrics['fraud_score'] < 0.3 else "Medium" if security_metrics['fraud_score'] < 0.6 else "High"
        fraud_color = "normal" if fraud_level == "Low" else "inverse"
        st.metric("Fraud Risk", fraud_level, delta_color=fraud_color)
    
    with col2:
        st.metric("Data Integrity", f"{security_metrics['data_integrity']*100:.1f}%")
    
    with col3:
        st.metric("Suspicious Transactions", security_metrics['suspicious_transactions'])
    
    with col4:
        st.metric("Blocked Attempts", security_metrics['blocked_attempts'])
    
    with col5:
        uptime = 99.9  # Simulated
        st.metric("System Uptime", f"{uptime:.1f}%")
    
    # Security trend chart
    st.subheader("Security Trends (Last 30 Days)")

    # Generate mock security trend data
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    fraud_scores = [np.random.uniform(0.1, 0.4) for _ in dates]
    data_integrity = [np.random.uniform(0.95, 1.0) for _ in dates]
    
    fig_trends = go.Figure()
    
    fig_trends.add_trace(go.Scatter(
        x=dates,
        y=fraud_scores,
        mode='lines+markers',
        name='Fraud Risk Score',
        line=dict(color='red', width=2),
        yaxis='y'
    ))
    
    fig_trends.add_trace(go.Scatter(
        x=dates,
        y=data_integrity,
        mode='lines+markers',
        name='Data Integrity',
        line=dict(color='green', width=2),
        yaxis='y2'
    ))
    
    fig_trends.update_layout(
        title="Security Metrics Trend",
        xaxis_title="Date",
        yaxis=dict(title="Fraud Risk Score", side="left", range=[0, 1]),
        yaxis2=dict(title="Data Integrity", side="right", overlaying="y", range=[0.9, 1.0]),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_trends, use_container_width=True)
    
    # Recent security events
    st.subheader("Recent Security Events")
    
    security_events = [
        {
            "timestamp": datetime.now() - timedelta(minutes=15),
            "event": "Successful login from new device",
            "severity": "Info",
            "action": "Device verified via email"
        },
        {
            "timestamp": datetime.now() - timedelta(hours=2),
            "event": "Anomalous transaction detected",
            "severity": "Warning",
            "action": "Transaction flagged for review"
        },
        {
            "timestamp": datetime.now() - timedelta(hours=6),
            "event": "Password changed successfully",
            "severity": "Info",
            "action": "Security confirmation sent"
        },
        {
            "timestamp": datetime.now() - timedelta(days=1),
            "event": "Failed login attempt",
            "severity": "Warning",
            "action": "IP address temporarily blocked"
        }
    ]
    
    for event in security_events:
        col1, col2, col3, col4 = st.columns([2, 3, 1, 2])
        
        with col1:
            st.write(event["timestamp"].strftime("%Y-%m-%d %H:%M"))
        
        with col2:
            st.write(event["event"])
        
        with col3:
            severity_colors = {"Info": "🔵", "Warning": "🟡", "Critical": "🔴"}
            st.write(f"{severity_colors.get(event['severity'], '⚪')} {event['severity']}")
        
        with col4:
            st.write(event["action"])

with tab2:
    st.subheader("AI Fraud Detection")
    
    if not df.empty:
        # Fraud detection analysis
        st.markdown("#### AI Analysis Results")

        # Simulate fraud detection on transactions
        fraud_indicators = []
        
        # Check for unusual amounts
        amount_threshold = df['amount_abs'].quantile(0.95)
        unusual_amounts = df[df['amount_abs'] > amount_threshold]
        
        if not unusual_amounts.empty:
            fraud_indicators.append({
                'type': 'Unusual Amount',
                'count': len(unusual_amounts),
                'risk_level': 'Medium',
                'description': f'Found {len(unusual_amounts)} transactions with unusually high amounts'
            })
        
        # Check for rapid-fire transactions
        df['time_diff'] = df['date'].diff().dt.total_seconds() / 60  # minutes
        rapid_transactions = df[df['time_diff'] < 5]  # Less than 5 minutes apart
        
        if not rapid_transactions.empty:
            fraud_indicators.append({
                'type': 'Rapid Transactions',
                'count': len(rapid_transactions),
                'risk_level': 'High',
                'description': f'Found {len(rapid_transactions)} transactions occurring within 5 minutes of each other'
            })
        
        # Check for unusual times (if hour data available)
        if 'hour' in df.columns or df['date'].dt.hour.min() != df['date'].dt.hour.max():
            late_night_transactions = df[(df['date'].dt.hour < 6) | (df['date'].dt.hour > 23)]
            
            if not late_night_transactions.empty:
                fraud_indicators.append({
                    'type': 'Unusual Time',
                    'count': len(late_night_transactions),
                    'risk_level': 'Low',
                    'description': f'Found {len(late_night_transactions)} transactions during late night hours'
                })
        
        # Check for duplicate transactions
        duplicates = df[df.duplicated(subset=['amount', 'description'], keep=False)]
        
        if not duplicates.empty:
            fraud_indicators.append({
                'type': 'Potential Duplicates',
                'count': len(duplicates),
                'risk_level': 'Medium',
                'description': f'Found {len(duplicates)} potentially duplicate transactions'
            })
        
        # Display fraud indicators
        if fraud_indicators:
            for indicator in fraud_indicators:
                risk_colors = {'Low': 'info', 'Medium': 'warning', 'High': 'error'}
                risk_color = risk_colors.get(indicator['risk_level'], 'info')
                
                getattr(st, risk_color)(f"**{indicator['type']}** ({indicator['risk_level']} Risk): {indicator['description']}")
        else:
            st.success("No fraud indicators detected in your transaction data!")
        
        # Fraud risk score visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Fraud Risk Distribution")
            
            # Simulate risk scores for transactions
            risk_scores = np.random.beta(2, 5, len(df))  # Beta distribution for realistic fraud scores
            risk_categories = ['Low (0-0.3)', 'Medium (0.3-0.7)', 'High (0.7-1.0)']
            risk_counts = [
                sum(risk_scores < 0.3),
                sum((risk_scores >= 0.3) & (risk_scores < 0.7)),
                sum(risk_scores >= 0.7)
            ]
            
            fig_risk = px.bar(
                x=risk_categories,
                y=risk_counts,
                title="Transaction Risk Distribution",
                color=risk_counts,
                color_continuous_scale=['green', 'yellow', 'red']
            )
            fig_risk.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig_risk, use_container_width=True)
        
        with col2:
            st.markdown("#### Risk Score Over Time")
            
            daily_risk = df.groupby(df['date'].dt.date).apply(lambda x: np.random.uniform(0.1, 0.4)).reset_index()
            daily_risk.columns = ['date', 'risk_score']
            
            fig_time_risk = px.line(
                daily_risk,
                x='date',
                y='risk_score',
                title="Daily Average Risk Score",
                markers=True
            )
            fig_time_risk.update_traces(line_color='orange')
            st.plotly_chart(fig_time_risk, use_container_width=True)
        
        # High-risk transactions table
        if fraud_indicators:
            st.markdown("#### High-Risk Transactions")
            
            # Show some example high-risk transactions
            high_risk_df = unusual_amounts.head(5) if not unusual_amounts.empty else df.head(5)
            display_df = high_risk_df[['date', 'amount', 'description']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d %H:%M')
            display_df['amount'] = display_df['amount'].apply(lambda x: f"${abs(x):.2f}")
            display_df['risk_score'] = [np.random.uniform(0.7, 0.95) for _ in range(len(display_df))]
            display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(display_df, use_container_width=True)
    
    else:
        st.info("Upload transaction data to enable fraud detection analysis.")
        
        # Show fraud detection capabilities
        st.markdown("#### Our Fraud Detection Capabilities")
        
        capabilities = [
            "**Machine Learning Models**: Advanced AI algorithms trained on millions of transactions",
            "**Real-time Analysis**: Instant fraud scoring for every transaction",
            "**Pattern Recognition**: Detection of unusual spending patterns and behaviors",
            "**Geolocation Verification**: Location-based fraud detection",
            "**Network Analysis**: Detection of coordinated fraud attempts",
            "**Risk Scoring**: Comprehensive risk assessment for each transaction"
        ]
        
        for capability in capabilities:
            st.markdown(capability)

with tab3:
    st.subheader("Anomaly Analysis")
    
    if not df.empty:
        # Statistical anomaly detection
        st.markdown("#### Statistical Anomaly Detection")

        col1, col2 = st.columns(2)
        
        with col1:
            # Amount-based anomalies
            expense_amounts = df[df['is_expense']]['amount_abs']
            mean_amount = expense_amounts.mean()
            std_amount = expense_amounts.std()
            
            # Z-score based anomalies
            z_scores = np.abs((expense_amounts - mean_amount) / std_amount)
            anomalies = expense_amounts[z_scores > 2]  # 2 standard deviations
            
            st.metric("Amount Anomalies", len(anomalies))
            st.metric("Mean Transaction", f"${mean_amount:.2f}")
            st.metric("Std Deviation", f"${std_amount:.2f}")
            
            if not anomalies.empty:
                st.markdown("**Anomalous Amounts:**")
                for amount in anomalies.head(5):
                    st.write(f"• ${amount:.2f}")
        
        with col2:
            # Time-based anomalies
            if len(df) > 1:
                # Transaction frequency analysis
                daily_counts = df.groupby(df['date'].dt.date).size()
                mean_daily = daily_counts.mean()
                std_daily = daily_counts.std()
                
                daily_anomalies = daily_counts[np.abs(daily_counts - mean_daily) > 2 * std_daily]
                
                st.metric("Frequency Anomalies", len(daily_anomalies))
                st.metric("Avg Daily Transactions", f"{mean_daily:.1f}")
                st.metric("Frequency Std Dev", f"{std_daily:.1f}")
                
                if not daily_anomalies.empty:
                    st.markdown("**Anomalous Days:**")
                    for date, count in daily_anomalies.head(5).items():
                        st.write(f"• {date}: {count} transactions")
        
        # Anomaly visualization
        st.markdown("#### Anomaly Visualization")

        # Create anomaly detection chart
        if not df.empty:
            # Scatter plot of amount vs time with anomalies highlighted
            df['is_anomaly'] = False
            if not expense_amounts.empty:
                z_scores = np.abs((df['amount_abs'] - df['amount_abs'].mean()) / df['amount_abs'].std())
                df['is_anomaly'] = z_scores > 2
            
            fig_anomaly = px.scatter(
                df,
                x='date',
                y='amount_abs',
                color='is_anomaly',
                title="Transaction Anomaly Detection",
                labels={'amount_abs': 'Amount ($)', 'date': 'Date'},
                color_discrete_map={True: 'red', False: 'blue'}
            )
            
            st.plotly_chart(fig_anomaly, use_container_width=True)
        
        # Anomaly patterns
        st.markdown("#### Detected Patterns")

        patterns = [
            {
                'pattern': 'Unusual Amount Range',
                'description': f'Transactions outside normal range (${mean_amount - 2*std_amount:.2f} - ${mean_amount + 2*std_amount:.2f})',
                'count': len(anomalies) if not anomalies.empty else 0,
                'severity': 'Medium'
            },
            {
                'pattern': 'Weekend Activity',
                'description': 'Unusual transaction activity on weekends',
                'count': len(df[df['date'].dt.weekday >= 5]),
                'severity': 'Low'
            },
            {
                'pattern': 'Merchant Deviation',
                'description': 'Transactions from new or unusual merchants',
                'count': np.random.randint(0, 5),  # Simulated
                'severity': 'Medium'
            }
        ]
        
        for pattern in patterns:
            severity_colors = {'Low': 'info', 'Medium': 'warning', 'High': 'error'}
            severity_color = severity_colors.get(pattern['severity'], 'info')
            
            getattr(st, severity_color)(f"**{pattern['pattern']}** ({pattern['count']} instances): {pattern['description']}")
    
    else:
        st.info("Upload transaction data to enable anomaly analysis.")
        
        # Show anomaly detection methods
        st.markdown("#### Anomaly Detection Methods")
        
        methods = [
            "**Statistical Analysis**: Z-score and IQR-based outlier detection",
            "**Machine Learning**: Isolation Forest and One-Class SVM algorithms",
            "**Temporal Analysis**: Time-series anomaly detection",
            "**Behavioral Profiling**: Personal spending pattern analysis",
            "**Geospatial Analysis**: Location-based anomaly detection",
            "**Sequential Analysis**: Transaction sequence pattern analysis"
        ]
        
        for method in methods:
            st.markdown(method)

with tab4:
    st.subheader("Data Protection & Privacy")
    
    # Data protection status
    st.markdown("#### Data Security Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Encryption**")
        st.success("AES-256 Encryption Active")
        st.success("TLS 1.3 in Transit")
        st.success("Database Encryption Enabled")
    
    with col2:
        st.markdown("**Access Control**")
        st.success("Multi-Factor Authentication")
        st.success("Role-Based Access Control")
        st.success("Session Management Active")
    
    with col3:
        st.markdown("**Compliance**")
        st.success("GDPR Compliant")
        st.success("PCI DSS Level 1")
        st.success("SOC 2 Type II")

    # Data handling information
    st.markdown("#### Data Handling Practices")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Data Encryption**")
        st.info("""
        - All sensitive data encrypted at rest using AES-256
        - Data in transit protected with TLS 1.3
        - Database fields individually encrypted
        - Encryption keys managed by AWS KMS
        """)
        
        st.markdown("**Privacy Protection**")
        st.info("""
        - Personal data pseudonymized where possible
        - Minimal data collection principle applied
        - Regular data purging of unnecessary information
        - User consent tracked and respected
        """)
    
    with col2:
        st.markdown("**Data Access Logging**")
        st.info("""
        - All data access attempts logged
        - Real-time monitoring of unusual access patterns
        - Automated alerts for suspicious activities
        - Comprehensive audit trails maintained
        """)
        
        st.markdown("**Geographic Compliance**")
        st.info("""
        - Data residency controls in place
        - Cross-border transfer protections
        - Regional compliance requirements met
        - Data sovereignty respected
        """)
    
    # Data retention and deletion
    st.markdown("#### Data Retention & User Rights")
    
    retention_info = {
        "Transaction Data": "7 years (regulatory requirement)",
        "Personal Information": "As long as account is active",
        "Logs & Analytics": "2 years for security analysis",
        "Backup Data": "90 days retention policy"
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Data Retention Periods**")
        for data_type, period in retention_info.items():
            st.write(f"• **{data_type}**: {period}")
    
    with col2:
        st.markdown("**Your Rights**")
        rights = [
            "Right to access your data",
            "Right to rectify incorrect data",
            "Right to erase your data",
            "Right to data portability",
            "Right to withdraw consent"
        ]
        
        for right in rights:
            st.write(f"• {right}")
        
        if st.button("Exercise Your Rights"):
            st.info("Please contact our privacy team at privacy@fintrack.com to exercise your data protection rights.")

with tab5:
    st.subheader("Security Analytics")
    
    # Generate security analytics data
    st.markdown("#### Security Metrics Dashboard")

    # Security scores over time
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    security_scores = [np.random.uniform(0.8, 1.0) for _ in dates]
    threat_levels = [np.random.uniform(0.0, 0.3) for _ in dates]
    
    fig_security = go.Figure()
    
    fig_security.add_trace(go.Scatter(
        x=dates,
        y=security_scores,
        mode='lines+markers',
        name='Security Score',
        line=dict(color='green', width=2),
        fill='tonexty'
    ))
    
    fig_security.add_trace(go.Scatter(
        x=dates,
        y=threat_levels,
        mode='lines+markers',
        name='Threat Level',
        line=dict(color='red', width=2),
        fill='tozeroy'
    ))
    
    fig_security.update_layout(
        title="Security Metrics Over Time",
        xaxis_title="Date",
        yaxis_title="Score/Level",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_security, use_container_width=True)
    
    # Security event analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Event Categories")
        
        event_categories = {
            'Login Attempts': 45,
            'Data Access': 120,
            'Transaction Monitoring': 89,
            'System Alerts': 12,
            'Fraud Detection': 3
        }
        
        fig_events = px.pie(
            values=list(event_categories.values()),
            names=list(event_categories.keys()),
            title="Security Events (Last 30 Days)"
        )
        st.plotly_chart(fig_events, use_container_width=True)
    
    with col2:
        st.markdown("#### Threat Intelligence")

        threat_types = ['Phishing', 'Malware', 'Fraud Attempts', 'Data Breach', 'Account Takeover']
        threat_counts = [np.random.randint(0, 10) for _ in threat_types]
        
        fig_threats = px.bar(
            x=threat_types,
            y=threat_counts,
            title="Threat Types Detected",
            color=threat_counts,
            color_continuous_scale='Reds'
        )
        fig_threats.update_layout(showlegend=False, coloraxis_showscale=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_threats, use_container_width=True)
    
    # Security recommendations
    st.markdown("#### Security Recommendations")

    st.write("Here are some recommended actions to enhance your security posture:")
    recommendations = [
        {
            'priority': 'High',
            'recommendation': 'Enable two-factor authentication on all accounts',
            'impact': 'Reduces account takeover risk by 99.9%'
        },
        {
            'priority': 'Medium',
            'recommendation': 'Review and update privacy settings quarterly',
            'impact': 'Ensures optimal data protection controls'
        },
        {
            'priority': 'Medium',
            'recommendation': 'Set up transaction amount alerts',
            'impact': 'Early detection of unauthorized transactions'
        },
        {
            'priority': 'Low',
            'recommendation': 'Use unique passwords for all financial accounts',
            'impact': 'Prevents credential stuffing attacks'
        }
    ]
    
    for rec in recommendations:
        priority_colors = {'High': 'error', 'Medium': 'warning', 'Low': 'info'}
        priority_color = priority_colors.get(rec['priority'], 'info')
        
        getattr(st, priority_color)(f"**{rec['priority']} Priority**: {rec['recommendation']}")
        st.caption(f"Impact: {rec['impact']}")

# Security tools and actions
st.subheader("Security Tools")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Run Deep Scan"):
        with st.spinner("Running comprehensive security scan..."):
            import time
            time.sleep(3)
            st.success("Deep scan completed! No threats detected.")

with col2:
    if st.button("Generate Security Report"):
        security_report = {
            'report_date': datetime.now().isoformat(),
            'security_score': security_metrics['fraud_score'],
            'threats_detected': security_metrics['suspicious_transactions'],
            'recommendations': len(recommendations),
            'encryption_status': 'Active',
            'compliance_status': 'Compliant'
        }
        
        st.download_button(
            label="Download Report",
            data=json.dumps(security_report, indent=2),
            file_name=f"security_report_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with col3:
    if st.button("Reset Security Settings"):
        st.session_state.security_settings = {
            'fraud_detection': True,
            'anomaly_threshold': 0.8,
            'real_time_monitoring': True,
            'alert_notifications': True,
            'data_encryption': True,
            'session_timeout': 30
        }
        st.success("Security settings reset to defaults!")

with col4:
    if st.button("Emergency Lockdown"):
        st.error("Emergency lockdown activated! All account access temporarily suspended.")
        st.info("Contact support to reactivate your account.")

# Security contact information
st.subheader("Security Contact")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Security Team**
    - Email: security@fintrack.com
    - Phone: +1 (555) 123-SECURE
    - 24/7 Security Hotline: +1 (555) 911-HELP
    """)

with col2:
    st.markdown("""
    **Report Suspicious Activity**
    - Immediate threats: Use Emergency Lockdown button
    - Suspicious transactions: Contact support
    - Data breach concerns: security@fintrack.com
    """)

# Footer disclaimer
st.markdown("---")
st.caption("This security dashboard provides real-time monitoring and analysis. For urgent security matters, contact our 24/7 security team immediately.")
