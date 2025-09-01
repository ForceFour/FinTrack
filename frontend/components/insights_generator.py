"""
Insights Generator Component for Analytics Dashboard
"""
from typing import List, Dict, Any
import pandas as pd


def generate_insights(df: pd.DataFrame, analysis_type: str, filtered_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate contextual, unique insights based on the selected analysis type.
    Maximum 5 insights per analysis type, ensuring no duplication.
    """
    insights = []
    # Track used insight types to prevent duplicates
    used_insight_types = set()

    if analysis_type == "Overview":
        # High-level financial summary insights
        if not filtered_df.empty:
            # 1. Net cash flow
            total_expenses = filtered_df[filtered_df['is_expense']]['amount_abs'].sum()
            total_income = filtered_df[filtered_df['is_income']]['amount_abs'].sum()
            net_flow = total_income - total_expenses
            if "net_flow" not in used_insight_types:
                insights.append({
                    "type": "net_flow",
                    "message": f"Net cash flow: LKR {net_flow:,.2f}",
                    "severity": "success" if net_flow > 0 else "warning"
                })
                used_insight_types.add("net_flow")

            # 2. Expense to income ratio
            if total_income > 0 and "expense_ratio" not in used_insight_types:
                expense_ratio = (total_expenses / total_income) * 100
                insights.append({
                    "type": "expense_ratio",
                    "message": f"Expenses are {expense_ratio:.1f}% of income",
                    "severity": "warning" if expense_ratio > 80 else "info"
                })
                used_insight_types.add("expense_ratio")

            # 3. Transaction volume
            transaction_count = len(filtered_df)
            days_span = (filtered_df['date'].max() - filtered_df['date'].min()).days
            avg_daily_tx = transaction_count / days_span if days_span > 0 else transaction_count
            if "transaction_volume" not in used_insight_types:
                insights.append({
                    "type": "transaction_volume",
                    "message": f"Average {avg_daily_tx:.1f} transactions per day",
                    "severity": "info"
                })
                used_insight_types.add("transaction_volume")

            # 4. Income vs expense transaction count
            expense_count = len(filtered_df[filtered_df['is_expense']])
            income_count = len(filtered_df[filtered_df['is_income']])
            if transaction_count > 0 and "transaction_split" not in used_insight_types:
                expense_pct = (expense_count / transaction_count) * 100
                insights.append({
                    "type": "transaction_split",
                    "message": f"{expense_pct:.1f}% of transactions are expenses ({expense_count} expenses, {income_count} income)",
                    "severity": "info"
                })
                used_insight_types.add("transaction_split")

            # 5. Average transaction size comparison
            avg_expense = filtered_df[filtered_df['is_expense']]['amount_abs'].mean() if not filtered_df[filtered_df['is_expense']].empty else 0
            avg_income = filtered_df[filtered_df['is_income']]['amount_abs'].mean() if not filtered_df[filtered_df['is_income']].empty else 0
            if avg_expense > 0 and avg_income > 0 and "avg_transaction_comparison" not in used_insight_types:
                diff_pct = ((avg_expense - avg_income) / avg_income) * 100
                insights.append({
                    "type": "avg_transaction_comparison",
                    "message": f"Average expense (LKR {avg_expense:,.2f}) is {abs(diff_pct):.1f}% {'higher' if diff_pct > 0 else 'lower'} than average income (LKR {avg_income:,.2f})",
                    "severity": "warning" if diff_pct > 50 else "info"
                })
                used_insight_types.add("avg_transaction_comparison")

    elif analysis_type == "Spending Patterns":
        # Category and temporal spending pattern insights
        if not filtered_df[filtered_df['is_expense']].empty:
            # 1. Top spending category
            category_totals = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].sum()
            total_expenses = filtered_df[filtered_df['is_expense']]['amount_abs'].sum()
            top_category = category_totals.nlargest(1).index[0]
            top_pct = (category_totals[top_category] / total_expenses) * 100 if total_expenses > 0 else 0
            if "category_distribution" not in used_insight_types:
                insights.append({
                    "type": "category_distribution",
                    "message": f"Highest spending: {top_category} ({top_pct:.1f}% of total expenses)",
                    "severity": "warning" if top_pct > 40 else "info"
                })
                used_insight_types.add("category_distribution")

            # 2. Most frequent category
            category_counts = filtered_df[filtered_df['is_expense']]['category'].value_counts()
            frequent_category = category_counts.index[0]
            category_count = category_counts.iloc[0]
            category_avg = filtered_df[filtered_df['category'] == frequent_category]['amount_abs'].mean()
            if frequent_category != top_category and "category_frequency" not in used_insight_types:
                insights.append({
                    "type": "category_frequency",
                    "message": f"Most frequent category: {frequent_category} ({category_count} transactions, avg. LKR {category_avg:,.2f})",
                    "severity": "info"
                })
                used_insight_types.add("category_frequency")

            # 3. Highest spending day of week
            daily_avg = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.day_name())['amount_abs'].mean()
            highest_day = daily_avg.idxmax()
            highest_amount = daily_avg[highest_day]
            overall_daily_avg = daily_avg.mean()
            if highest_amount > overall_daily_avg * 1.5 and "day_pattern" not in used_insight_types:
                insights.append({
                    "type": "day_pattern",
                    "message": f"Highest spending on {highest_day}s (LKR {highest_amount:,.2f}, {((highest_amount/overall_daily_avg)-1)*100:.1f}% above average)",
                    "severity": "warning"
                })
                used_insight_types.add("day_pattern")

            # 4. Category concentration
            top_3_categories = category_totals.nlargest(3)
            top_3_pct = (top_3_categories.sum() / total_expenses) * 100 if total_expenses > 0 else 0
            if top_3_pct > 70 and "category_concentration" not in used_insight_types:
                insights.append({
                    "type": "category_concentration",
                    "message": f"Top 3 categories account for {top_3_pct:.1f}% of total spending",
                    "severity": "warning"
                })
                used_insight_types.add("category_concentration")

            # 5. Spending variability
            category_std = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].std()
            most_variable_category = category_std.idxmax()
            if not pd.isna(most_variable_category) and "spending_variability" not in used_insight_types:
                insights.append({
                    "type": "spending_variability",
                    "message": f"{most_variable_category} has the most variable spending (std: LKR {category_std[most_variable_category]:,.2f})",
                    "severity": "info"
                })
                used_insight_types.add("spending_variability")

    elif analysis_type == "Trend Analysis":
        # Time-based trend insights
        if not filtered_df[filtered_df['is_expense']].empty:
            # 1. Monthly spending trend
            monthly_spending = filtered_df[filtered_df['is_expense']].groupby(
                pd.Grouper(key='date', freq='M'))['amount_abs'].sum()
            if len(monthly_spending) > 1 and "spending_trend" not in used_insight_types:
                trend = (monthly_spending.iloc[-1] - monthly_spending.iloc[0]) / monthly_spending.iloc[0] * 100 if monthly_spending.iloc[0] > 0 else 0
                insights.append({
                    "type": "spending_trend",
                    "message": f"Monthly spending has {'increased' if trend > 0 else 'decreased'} by {abs(trend):.1f}% over the period",
                    "severity": "warning" if trend > 0 else "success"
                })
                used_insight_types.add("spending_trend")

            # 2. Month start vs end pattern
            filtered_df['day_of_month'] = filtered_df['date'].dt.day
            early_month = filtered_df[filtered_df['day_of_month'] <= 15]['amount_abs'].mean()
            late_month = filtered_df[filtered_df['day_of_month'] > 15]['amount_abs'].mean()
            if early_month != 0 and late_month != 0 and "monthly_pattern" not in used_insight_types:
                diff_pct = ((early_month - late_month) / late_month) * 100
                if abs(diff_pct) > 30:
                    insights.append({
                        "type": "monthly_pattern",
                        "message": f"Spending is {abs(diff_pct):.1f}% {'higher' if diff_pct > 0 else 'lower'} in the first half of each month",
                        "severity": "warning" if diff_pct > 0 else "info"
                    })
                    used_insight_types.add("monthly_pattern")

            # 3. Seasonal peak month
            monthly_avg = filtered_df[filtered_df['is_expense']].groupby(filtered_df['date'].dt.month)['amount_abs'].mean()
            if not monthly_avg.empty and "seasonal_peak" not in used_insight_types:
                peak_month = monthly_avg.idxmax()
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                peak_month_name = month_names[int(peak_month) - 1]
                peak_value = monthly_avg[peak_month]
                avg_value = monthly_avg.mean()
                if peak_value > avg_value * 1.2:
                    insights.append({
                        "type": "seasonal_peak",
                        "message": f"Highest average spending in {peak_month_name} (LKR {peak_value:,.2f}, {((peak_value/avg_value)-1)*100:.1f}% above average)",
                        "severity": "warning"
                    })
                    used_insight_types.add("seasonal_peak")

            # 4. Category trend analysis
            monthly_category = filtered_df[filtered_df['is_expense']].pivot_table(
                index=pd.Grouper(key='date', freq='M'),
                columns='category',
                values='amount_abs',
                aggfunc='sum'
            ).fillna(0)
            if not monthly_category.empty and len(monthly_category) > 1 and "category_trend" not in used_insight_types:
                significant_changes = []
                for category in monthly_category.columns:
                    first_month = monthly_category[category].iloc[0]
                    last_month = monthly_category[category].iloc[-1]
                    if first_month > 0:
                        change = ((last_month - first_month) / first_month) * 100
                        if abs(change) > 50:
                            significant_changes.append((category, change))
                if significant_changes:
                    category, change = sorted(significant_changes, key=lambda x: abs(x[1]), reverse=True)[0]
                    insights.append({
                        "type": "category_trend",
                        "message": f"{category} spending has {'increased' if change > 0 else 'decreased'} by {abs(change):.1f}%",
                        "severity": "warning" if change > 0 else "success"
                    })
                    used_insight_types.add("category_trend")

            # 5. Transaction frequency trend
            monthly_tx_count = filtered_df[filtered_df['is_expense']].groupby(
                pd.Grouper(key='date', freq='M')).size()
            if len(monthly_tx_count) > 1 and "tx_frequency_trend" not in used_insight_types:
                trend = (monthly_tx_count.iloc[-1] - monthly_tx_count.iloc[0]) / monthly_tx_count.iloc[0] * 100 if monthly_tx_count.iloc[0] > 0 else 0
                insights.append({
                    "type": "tx_frequency_trend",
                    "message": f"Transaction frequency has {'increased' if trend > 0 else 'decreased'} by {abs(trend):.1f}% over the period",
                    "severity": "info"
                })
                used_insight_types.add("tx_frequency_trend")

    elif analysis_type == "Merchant Analysis":
        # Merchant-specific insights
        if not filtered_df[filtered_df['is_expense']].empty:
            # 1. Top merchant by spending
            merchant_totals = filtered_df[filtered_df['is_expense']].groupby('merchant')['amount_abs'].sum()
            top_merchant = merchant_totals.idxmax()
            top_merchant_pct = (merchant_totals.max() / merchant_totals.sum()) * 100 if merchant_totals.sum() > 0 else 0
            if top_merchant_pct > 5 and "merchant_concentration" not in used_insight_types:
                insights.append({
                    "type": "merchant_concentration",
                    "message": f"{top_merchant} accounts for {top_merchant_pct:.1f}% of total spending",
                    "severity": "warning" if top_merchant_pct > 30 else "info"
                })
                used_insight_types.add("merchant_concentration")

            # 2. Most frequent merchant
            merchant_visits = filtered_df[filtered_df['is_expense']]['merchant'].value_counts()
            frequent_merchant = merchant_visits.index[0]
            visit_count = merchant_visits.iloc[0]
            merchant_avg = filtered_df[filtered_df['merchant'] == frequent_merchant]['amount_abs'].mean()
            if visit_count > 10 and frequent_merchant != top_merchant and "merchant_frequency" not in used_insight_types:
                insights.append({
                    "type": "merchant_frequency",
                    "message": f"Most visited: {frequent_merchant} ({visit_count} visits, avg. LKR {merchant_avg:,.2f} per visit)",
                    "severity": "info"
                })
                used_insight_types.add("merchant_frequency")

            # 3. Merchant spending trend
            merchant_monthly = filtered_df[filtered_df['is_expense']].pivot_table(
                index=pd.Grouper(key='date', freq='M'),
                columns='merchant',
                values='amount_abs',
                aggfunc='sum'
            ).fillna(0)
            if not merchant_monthly.empty and len(merchant_monthly) > 1 and "merchant_trend" not in used_insight_types:
                significant_changes = []
                for merchant in merchant_monthly.columns:
                    first_month = merchant_monthly[merchant].iloc[0]
                    last_month = merchant_monthly[merchant].iloc[-1]
                    if first_month > 0 and merchant_totals.get(merchant, 0) > merchant_totals.mean():
                        change = ((last_month - first_month) / first_month) * 100
                        if abs(change) > 50:
                            significant_changes.append((merchant, change))
                if significant_changes:
                    merchant, change = sorted(significant_changes, key=lambda x: abs(x[1]), reverse=True)[0]
                    insights.append({
                        "type": "merchant_trend",
                        "message": f"Spending at {merchant} has {'increased' if change > 0 else 'decreased'} by {abs(change):.1f}%",
                        "severity": "warning" if change > 0 else "success"
                    })
                    used_insight_types.add("merchant_trend")

            # 4. High-value merchant transactions
            high_value_merchants = filtered_df[filtered_df['is_expense']].groupby('merchant')['amount_abs'].max()
            top_high_value_merchant = high_value_merchants.idxmax()
            max_transaction = high_value_merchants.max()
            if max_transaction > filtered_df[filtered_df['is_expense']]['amount_abs'].mean() * 2 and "high_value_merchant" not in used_insight_types:
                insights.append({
                    "type": "high_value_merchant",
                    "message": f"Largest single transaction at {top_high_value_merchant}: LKR {max_transaction:,.2f}",
                    "severity": "warning"
                })
                used_insight_types.add("high_value_merchant")

            # 5. Merchant diversity
            unique_merchants = len(filtered_df[filtered_df['is_expense']]['merchant'].unique())
            total_transactions = len(filtered_df[filtered_df['is_expense']])
            if total_transactions > 0 and "merchant_diversity" not in used_insight_types:
                merchant_diversity = unique_merchants / total_transactions * 100
                insights.append({
                    "type": "merchant_diversity",
                    "message": f"Spending spread across {unique_merchants} unique merchants ({merchant_diversity:.1f}% diversity)",
                    "severity": "info"
                })
                used_insight_types.add("merchant_diversity")

    elif analysis_type == "Predictive Analytics":
        # Future-focused insights
        if not filtered_df[filtered_df['is_expense']].empty:
            # 1. Monthly spending forecast
            monthly_spending = filtered_df[filtered_df['is_expense']].groupby(
                pd.Grouper(key='date', freq='M'))['amount_abs'].sum()
            if len(monthly_spending) > 1 and "spending_forecast" not in used_insight_types:
                avg_spend = monthly_spending.mean()
                std_spend = monthly_spending.std()
                next_month_prediction = avg_spend + (monthly_spending.diff().mean())
                percent_change = ((next_month_prediction - avg_spend) / avg_spend) * 100 if avg_spend > 0 else 0
                insights.append({
                    "type": "spending_forecast",
                    "message": f"Next month's predicted spending: LKR {next_month_prediction:,.2f} ({percent_change:+.1f}% vs average)",
                    "severity": "warning" if next_month_prediction > avg_spend + std_spend else "info"
                })
                used_insight_types.add("spending_forecast")

            # 2. Category growth trend
            category_trends = filtered_df[filtered_df['is_expense']].pivot_table(
                index=pd.Grouper(key='date', freq='M'),
                columns='category',
                values='amount_abs',
                aggfunc='sum'
            ).fillna(0)
            if not category_trends.empty and len(category_trends) > 2 and "category_forecast" not in used_insight_types:
                significant_trends = []
                for category in category_trends.columns:
                    trend = pd.Series(category_trends[category]).diff().mean()
                    category_avg = category_trends[category].mean()
                    if category_avg > 0:
                        trend_pct = (trend / category_avg) * 100
                        if abs(trend_pct) > 20:
                            significant_trends.append((category, trend_pct))
                if significant_trends:
                    category, trend_pct = sorted(significant_trends, key=lambda x: abs(x[1]), reverse=True)[0]
                    insights.append({
                        "type": "category_forecast",
                        "message": f"{category} spending trend: {trend_pct:+.1f}% per month",
                        "severity": "warning" if trend_pct > 0 else "success"
                    })
                    used_insight_types.add("category_forecast")

            # 3. High-risk spending category
            category_std = filtered_df[filtered_df['is_expense']].groupby('category')['amount_abs'].std()
            if not category_std.empty and "high_risk_category" not in used_insight_types:
                high_risk_category = category_std.idxmax()
                if not pd.isna(high_risk_category):
                    insights.append({
                        "type": "high_risk_category",
                        "message": f"{high_risk_category} has the highest spending volatility (std: LKR {category_std[high_risk_category]:,.2f})",
                        "severity": "warning"
                    })
                    used_insight_types.add("high_risk_category")

            # 4. Transaction volume forecast
            monthly_tx_count = filtered_df[filtered_df['is_expense']].groupby(
                pd.Grouper(key='date', freq='M')).size()
            if len(monthly_tx_count) > 1 and "tx_volume_forecast" not in used_insight_types:
                avg_tx = monthly_tx_count.mean()
                next_month_tx = avg_tx + (monthly_tx_count.diff().mean())
                tx_change = ((next_month_tx - avg_tx) / avg_tx) * 100 if avg_tx > 0 else 0
                insights.append({
                    "type": "tx_volume_forecast",
                    "message": f"Next month's predicted transaction count: {next_month_tx:.0f} ({tx_change:+.1f}% vs average)",
                    "severity": "info"
                })
                used_insight_types.add("tx_volume_forecast")

            # 5. Potential anomaly forecast
            expense_amounts = filtered_df[filtered_df['is_expense']]['amount_abs']
            if not expense_amounts.empty and "anomaly_forecast" not in used_insight_types:
                threshold = expense_amounts.mean() + 2 * expense_amounts.std()
                high_value_count = len(expense_amounts[expense_amounts > threshold])
                if high_value_count > 0:
                    insights.append({
                        "type": "anomaly_forecast",
                        "message": f"{high_value_count} transactions exceed anomaly threshold (LKR {threshold:,.2f})",
                        "severity": "warning"
                    })
                    used_insight_types.add("anomaly_forecast")

    return insights[:5]  # Ensure maximum 5 unique insights