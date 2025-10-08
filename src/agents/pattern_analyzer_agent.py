from typing import Dict, Any, List
from datetime import datetime, timedelta
from ..schemas.transaction_schemas import ClassifiedTransaction

class PatternAnalyzerAgent:
    """
    Pattern Analyzer Agent

    Responsibilities:
    - Analyze income vs expense patterns
    - Track category distributions
    - Identify recurring transactions
    - Detect spending patterns and trends
    - Generate key financial insights
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def analyze_income_expenses(self, transactions: List[ClassifiedTransaction]) -> Dict[str, Any]:
        """Analyze total income and expenses with category breakdowns"""
        income_total = 0.0
        expense_total = 0.0
        income_by_category = {}
        expenses_by_category = {}

        for tx in transactions:
            if tx.amount > 0:  # Positive amounts are income
                income_total += tx.amount
                if tx.predicted_category not in income_by_category:
                    income_by_category[tx.predicted_category] = 0
                income_by_category[tx.predicted_category] += tx.amount
            else:  # Negative amounts are expenses
                expense_amount = abs(tx.amount)
                expense_total += expense_amount
                if tx.predicted_category not in expenses_by_category:
                    expenses_by_category[tx.predicted_category] = 0
                expenses_by_category[tx.predicted_category] += expense_amount

        # Calculate percentages
        category_percentages = {}
        if expense_total > 0:
            category_percentages = {
                category: (amount / expense_total) * 100
                for category, amount in expenses_by_category.items()
            }

        return {
            'total_income': income_total,
            'total_expenses': expense_total,
            'net_cashflow': income_total - expense_total,
            'income_by_category': income_by_category,
            'expenses_by_category': expenses_by_category,
            'category_percentages': category_percentages
        }

    def generate_key_findings(self, transactions: List[ClassifiedTransaction],
                            financial_summary: Dict[str, Any],
                            recurring: List[Dict[str, Any]],
                            spikes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate top key findings and insights"""
        findings = []

        # Cash flow analysis
        if financial_summary['net_cashflow'] < 0:
            findings.append({
                'type': 'cash_flow',
                'message': f"Net cash flow is negative: LKR {abs(financial_summary['net_cashflow']):.2f}",
                'severity': 'warning'
            })
        elif financial_summary['net_cashflow'] > financial_summary['total_income'] * 0.2:
            findings.append({
                'type': 'cash_flow',
                'message': f"Healthy savings rate: {(financial_summary['net_cashflow']/financial_summary['total_income']*100):.1f}% of income",
                'severity': 'success'
            })

        # Top expense category
        if financial_summary['expenses_by_category']:
            top_category = max(financial_summary['expenses_by_category'].items(), key=lambda x: x[1])
            percentage = financial_summary['category_percentages'].get(top_category[0], 0)

            if percentage > 30:  # Only add if significant
                findings.append({
                    'type': 'spending_category',
                    'message': f"{top_category[0]} represents {percentage:.1f}% of total expenses",
                    'severity': 'warning' if percentage > 50 else 'info'
                })

        # Recurring payments analysis
        total_recurring = sum(rec['amount'] for rec in recurring)
        if total_recurring > financial_summary['total_expenses'] * 0.3:  # Only if significant
            findings.append({
                'type': 'recurring_payments',
                'message': f"Recurring payments: LKR {total_recurring:.2f} ({len(recurring)} transactions)",
                'severity': 'info'
            })

        # Spending spikes
        if spikes:
            high_spikes = [s for s in spikes if s['deviation'] > 3]
            if high_spikes:
                findings.append({
                    'type': 'spending_anomaly',
                    'message': f"Detected {len(high_spikes)} significant spending spikes",
                    'severity': 'warning'
                })

        return findings[:5]  # Return top 5 findings

    def detect_recurring_transactions(self, transactions: List[ClassifiedTransaction]) -> List[Dict[str, Any]]:
        """Identify recurring transactions based on merchant, amount, and frequency"""
        recurring = {}

        # Group transactions by merchant and amount
        for tx in transactions:
            key = f"{tx.merchant_standardized}_{tx.amount}"
            if key not in recurring:
                recurring[key] = {
                    'merchant': tx.merchant_standardized,
                    'amount': tx.amount,
                    'category': tx.predicted_category,
                    'dates': [tx.date],
                    'transactions': [tx]
                }
            else:
                recurring[key]['dates'].append(tx.date)
                recurring[key]['transactions'].append(tx)

        # Analyze frequency patterns
        recurring_patterns = []
        for key, data in recurring.items():
            if len(data['dates']) >= 2:  # Need at least 2 transactions to detect pattern
                # Calculate time intervals
                sorted_dates = sorted(data['dates'])
                intervals = [(sorted_dates[i+1] - sorted_dates[i]).days for i in range(len(sorted_dates)-1)]
                avg_interval = sum(intervals) / len(intervals)
                std_dev = (sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)) ** 0.5

                # Determine frequency and confidence
                if 25 <= avg_interval <= 31 and std_dev < 3:
                    frequency = 'monthly'
                    confidence = 0.9
                elif 6 <= avg_interval <= 8 and std_dev < 2:
                    frequency = 'weekly'
                    confidence = 0.9
                elif std_dev < avg_interval/2:
                    frequency = f'every {round(avg_interval)} days'
                    confidence = 0.7
                else:
                    continue  # Skip if no clear pattern

                recurring_patterns.append({
                    'merchant': data['merchant'],
                    'amount': abs(data['amount']),
                    'category': data['category'],
                    'frequency': frequency,
                    'confidence': confidence,
                    'transaction_count': len(data['dates']),
                    'first_date': min(data['dates']),
                    'last_date': max(data['dates']),
                    'transactions': data['transactions']  # Include the actual transaction objects
                })

        return recurring_patterns

    def detect_spending_spikes(self, transactions: List[ClassifiedTransaction]) -> List[Dict[str, Any]]:
        """Detect unusual spending spikes by category or merchant"""
        # Group transactions by category
        category_spending = {}
        for tx in transactions:
            if tx.amount < 0:  # Only analyze expenses
                if tx.predicted_category not in category_spending:
                    category_spending[tx.predicted_category] = []
                category_spending[tx.predicted_category].append({
                    'date': tx.date,
                    'amount': abs(tx.amount)
                })

        spikes = []
        for category, txs in category_spending.items():
            if len(txs) < 3:  # Need at least 3 transactions to detect spikes
                continue

            amounts = [tx['amount'] for tx in txs]
            mean = sum(amounts) / len(amounts)
            std_dev = (sum((x - mean) ** 2 for x in amounts) / len(amounts)) ** 0.5

            # Detect spikes (amounts more than 2 standard deviations from mean)
            for tx_dict in txs:
                if std_dev > 0:  # Avoid division by zero
                    deviation = (tx_dict['amount'] - mean) / std_dev
                    if deviation > 2:  # More than 2 standard deviations
                        spikes.append({
                            'category': category,
                            'date': tx_dict['date'],
                            'amount': tx_dict['amount'],
                            'deviation': deviation,
                            'normal_range': {
                                'min': mean - std_dev,
                                'max': mean + std_dev
                            }
                        })

        return sorted(spikes, key=lambda x: x['deviation'], reverse=True)

    def analyze_monthly_habits(self, transactions: List[ClassifiedTransaction]) -> Dict[str, Any]:
        """Analyze monthly spending patterns and habits"""
        monthly_data = {}

        for tx in transactions:
            month_key = tx.date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'total_spending': 0,
                    'transaction_count': 0,
                    'by_category': {},
                    'by_weekday': {i: 0 for i in range(7)},
                    'by_week': {i: 0 for i in range(1, 6)}
                }

            if tx.amount < 0:  # Only analyze expenses
                amount = abs(tx.amount)
                monthly_data[month_key]['total_spending'] += amount
                monthly_data[month_key]['transaction_count'] += 1

                # Category spending
                category = tx.predicted_category
                if category not in monthly_data[month_key]['by_category']:
                    monthly_data[month_key]['by_category'][category] = 0
                monthly_data[month_key]['by_category'][category] += amount

                # Day of week spending
                monthly_data[month_key]['by_weekday'][tx.date.weekday()] += amount

                # Week of month spending (1-5)
                week = (tx.date.day - 1) // 7 + 1
                monthly_data[month_key]['by_week'][week] += amount

        return monthly_data

    def analyze_category_trends(self, transactions: List[ClassifiedTransaction]) -> Dict[str, Any]:
        """Analyze spending trends by category over time"""
        category_data = {}

        for tx in transactions:
            if tx.amount < 0:  # Only analyze expenses
                month_key = tx.date.strftime('%Y-%m')
                category = tx.predicted_category

                if category not in category_data:
                    category_data[category] = {}
                if month_key not in category_data[category]:
                    category_data[category][month_key] = 0

                category_data[category][month_key] += abs(tx.amount)

        # Calculate trends for each category
        trends = {}
        for category, monthly_amounts in category_data.items():
            sorted_months = sorted(monthly_amounts.keys())
            if len(sorted_months) >= 2:
                amounts = [monthly_amounts[m] for m in sorted_months]
                first_amount = amounts[0]
                last_amount = amounts[-1]

                trend = ((last_amount - first_amount) / first_amount * 100
                        if first_amount > 0 else 0)

                trends[category] = {
                    'trend': trend,
                    'monthly_data': monthly_amounts,
                    'total': sum(amounts),
                    'average': sum(amounts) / len(amounts),
                    'min': min(amounts),
                    'max': max(amounts)
                }

        return trends

    def _get_season(self, date):
        """Get season for a given date"""
        month = date.month
        if month in [12, 1, 2]: return 'winter'
        elif month in [3, 4, 5]: return 'spring'
        elif month in [6, 7, 8]: return 'summer'
        else: return 'fall'

    def detect_seasonal_patterns(self, transactions: List[ClassifiedTransaction]) -> List[Dict[str, Any]]:
        """Detect seasonal spending patterns"""
        seasonal_data = {
            'winter': {'total': 0, 'count': 0},  # Dec-Feb
            'spring': {'total': 0, 'count': 0},  # Mar-May
            'summer': {'total': 0, 'count': 0},  # Jun-Aug
            'fall': {'total': 0, 'count': 0}     # Sep-Nov
        }

        # Aggregate spending by season
        for tx in transactions:
            if tx.amount < 0:  # Only analyze expenses
                season = self._get_season(tx.date)
                amount = abs(tx.amount)
                seasonal_data[season]['total'] += amount
                seasonal_data[season]['count'] += 1

        # Calculate seasonal patterns
        total_spending = sum(s['total'] for s in seasonal_data.values())
        patterns = []

        for season, data in seasonal_data.items():
            if data['count'] > 0:
                spending_percentage = (data['total'] / total_spending * 100
                                    if total_spending > 0 else 0)
                patterns.append({
                    'season': season,
                    'total_spending': data['total'],
                    'transaction_count': data['count'],
                    'average_transaction': data['total'] / data['count'],
                    'percentage_of_total': spending_percentage,
                    'is_significant': spending_percentage > 30
                })

        return sorted(patterns, key=lambda x: x['total_spending'], reverse=True)

    def analyze_income_expense_trends(self, transactions: List[ClassifiedTransaction]) -> Dict[str, Any]:
        """Analyze income and expense trends over time"""
        monthly_data = {}

        for tx in transactions:
            month_key = tx.date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'income': 0, 'expenses': 0}

            if tx.amount > 0:
                monthly_data[month_key]['income'] += tx.amount
            else:
                monthly_data[month_key]['expenses'] += abs(tx.amount)

        # Calculate trends
        months = sorted(monthly_data.keys())
        if len(months) >= 2:
            first_month = monthly_data[months[0]]
            last_month = monthly_data[months[-1]]

            income_change = ((last_month['income'] - first_month['income']) / first_month['income'] * 100
                           if first_month['income'] > 0 else 0)
            expense_change = ((last_month['expenses'] - first_month['expenses']) / first_month['expenses'] * 100
                            if first_month['expenses'] > 0 else 0)

            return {
                'income_trend': income_change,
                'expense_trend': expense_change,
                'monthly_data': monthly_data
            }

        return {
            'income_trend': 0,
            'expense_trend': 0,
            'monthly_data': monthly_data
        }

    def process(self, input_data: List[ClassifiedTransaction]) -> Dict[str, Any]:
        """Process transactions and detect spending patterns"""
        # Sort transactions by date for temporal analysis
        sorted_txs = sorted(input_data, key=lambda x: x.date)

        # Run core financial analysis
        financial_summary = self.analyze_income_expenses(sorted_txs)

        # Run pattern detection analyses
        trends = self.analyze_income_expense_trends(sorted_txs)
        recurring = self.detect_recurring_transactions(sorted_txs)
        spikes = self.detect_spending_spikes(sorted_txs)
        monthly_habits = self.analyze_monthly_habits(sorted_txs)
        category_trends = self.analyze_category_trends(sorted_txs)
        seasonal = self.detect_seasonal_patterns(sorted_txs)

        # Generate pattern insights
        pattern_insights = []

        # Add recurring payment insights
        for rec in recurring:
            transaction_ids = [tx.id for tx in rec['transactions']]
            pattern_insights.append({
                'insight_type': 'recurring',
                'category': rec['category'],
                'description': f"Found recurring {rec['category']} payment of LKR {rec['amount']:.2f} "
                             f"to {rec['merchant']} ({rec['frequency']})",
                'severity': 'medium',
                'transactions_involved': transaction_ids,
                'metadata': {
                    'frequency': rec['frequency'],
                    'frequency_days': 30 if rec['frequency'] == 'monthly' else 7 if rec['frequency'] == 'weekly' else 1,
                    'avg_amount': rec['amount'],
                    'confidence': rec['confidence'],
                    'transaction_count': rec['transaction_count'],
                    'merchant': rec['merchant']
                }
            })

        # Add spending spike insights
        for spike in spikes:
            # Find transaction IDs for this spike
            spike_tx_ids = []
            for tx in sorted_txs:
                if (tx.date == spike['date'] and
                    tx.predicted_category == spike['category'] and
                    abs(tx.amount) == spike['amount']):
                    spike_tx_ids.append(tx.id)
                    break

            pattern_insights.append({
                'insight_type': 'spike',
                'category': spike['category'],
                'description': f"Unusual spending of LKR {spike['amount']:.2f} in {spike['category']} "
                             f"on {spike['date'].strftime('%Y-%m-%d')} "
                             f"({spike['deviation']:.1f}x above normal)",
                'severity': 'high' if spike['deviation'] > 3 else 'medium',
                'transactions_involved': spike_tx_ids,
                'metadata': {
                    'deviation': spike['deviation'],
                    'normal_range': spike['normal_range']
                }
            })

        # Add trend insights
        if trends['income_trend'] != 0:
            # Get all income transaction IDs
            income_tx_ids = [tx.id for tx in sorted_txs if tx.amount > 0]
            pattern_insights.append({
                'insight_type': 'trend',
                'category': 'income',
                'description': f"Income has {'increased' if trends['income_trend'] > 0 else 'decreased'} "
                             f"by {abs(trends['income_trend']):.1f}% over the period",
                'severity': 'high' if abs(trends['income_trend']) > 50 else 'medium',
                'transactions_involved': income_tx_ids,
                'metadata': {
                    'trend_percentage': trends['income_trend'],
                    'monthly_data': trends['monthly_data']
                }
            })

        if trends['expense_trend'] != 0:
            # Get all expense transaction IDs
            expense_tx_ids = [tx.id for tx in sorted_txs if tx.amount < 0]
            pattern_insights.append({
                'insight_type': 'trend',
                'category': 'expenses',
                'description': f"Expenses have {'increased' if trends['expense_trend'] > 0 else 'decreased'} "
                             f"by {abs(trends['expense_trend']):.1f}% over the period",
                'severity': 'high' if abs(trends['expense_trend']) > 50 else 'medium',
                'transactions_involved': expense_tx_ids,
                'metadata': {
                    'trend_percentage': trends['expense_trend'],
                    'monthly_data': trends['monthly_data']
                }
            })

        # Add seasonal insights
        for season in seasonal:
            if season['is_significant']:
                # Get transaction IDs for this season
                season_tx_ids = []
                for tx in sorted_txs:
                    if tx.amount < 0:  # Only expenses
                        tx_season = self._get_season(tx.date)
                        if tx_season == season['season']:
                            season_tx_ids.append(tx.id)

                pattern_insights.append({
                    'insight_type': 'seasonal',
                    'category': None,
                    'description': f"Significant {season['season']} spending pattern detected "
                                 f"(LKR {season['total_spending']:.2f}, "
                                 f"{season['percentage_of_total']:.1f}% of total spending)",
                    'severity': 'low',
                    'transactions_involved': season_tx_ids,
                    'metadata': {
                        'season': season['season'],
                        'total_spending': season['total_spending'],
                        'percentage': season['percentage_of_total']
                    }
                })

        # Add category trend insights
        for category, data in category_trends.items():
            if abs(data['trend']) > 20:
                # Get transaction IDs for this category
                category_tx_ids = [tx.id for tx in sorted_txs
                                 if tx.predicted_category == category and tx.amount < 0]

                pattern_insights.append({
                    'insight_type': 'category_trend',
                    'category': category,
                    'description': f"{category} spending has {'increased' if data['trend'] > 0 else 'decreased'} "
                                 f"by {abs(data['trend']):.1f}% over the period",
                    'severity': 'high' if abs(data['trend']) > 50 else 'medium',
                    'transactions_involved': category_tx_ids,
                    'metadata': {
                        'trend_percentage': data['trend'],
                        'monthly_data': data['monthly_data']
                    }
                })

        # Extract top findings
        key_findings = []
        sorted_insights = sorted(pattern_insights, key=lambda x: x['metadata'].get('confidence', 0), reverse=True)
        for insight in sorted_insights[:5]:
            key_findings.append({
                'type': insight['insight_type'],
                'finding': insight['description'],
                'confidence': insight['metadata'].get('confidence', 0)
            })

        # Create spending trends summary
        spending_trends = {
            'income_expense_trends': trends,
            'monthly_patterns': monthly_habits,
            'category_trends': category_trends,
            'seasonal_patterns': seasonal
        }

        return {
            'total_income': financial_summary['total_income'],
            'total_expenses': financial_summary['total_expenses'],
            'net_cashflow': financial_summary['net_cashflow'],
            'income_by_category': financial_summary['income_by_category'],
            'expenses_by_category': financial_summary['expenses_by_category'],
            'category_percentages': financial_summary['category_percentages'],
            'pattern_insights': pattern_insights,
            'recurring_transactions': recurring,
            'spending_trends': spending_trends,
            'key_findings': key_findings
        }
