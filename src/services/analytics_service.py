"""
Analytics Service - Implements financial analytics using pattern analyzer
and database queries for user transaction analysis with Supabase
"""

from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from supabase import Client
import statistics

from ..models.analytics import (
    SpendingAnalytics, CategoryBreakdown, TrendAnalysis,
    SpendingPattern, CashFlowAnalysis, AnalyticsPeriod
)
from ..agents.pattern_analyzer_agent import PatternAnalyzerAgent
from ..schemas.transaction_schemas import ClassifiedTransaction
from ..db.operations import TransactionCRUD

class AnalyticsService:
    """Service for financial analytics and pattern detection using Supabase"""

    def __init__(self, db: Client):
        self.db = db
        self.pattern_analyzer = PatternAnalyzerAgent()

    async def get_transactions_for_period(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        categories: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Helper method to get transactions for a period"""
        filters = {
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        }
        if categories:
            filters['categories'] = categories

        transactions, _ = await TransactionCRUD.get_transactions(self.db, filters)
        return transactions

    async def get_spending_analytics(
        self,
        user_id: str,
        period: str,
        start_date: date,
        end_date: date,
        categories: List[str] = None
    ) -> SpendingAnalytics:
        """Get comprehensive spending analytics for a given period"""
        # Get transactions for the period
        transactions = await self.get_transactions_for_period(
            user_id, start_date, end_date, categories
        )

        # Convert to ClassifiedTransaction objects for pattern analyzer
        classified_txns = [
            ClassifiedTransaction(
                id=str(tx['id']),
                user_id=tx['user_id'],
                date=datetime.fromisoformat(tx['date']).date() if isinstance(tx['date'], str) else tx['date'],
                amount=Decimal(str(tx['amount'])),
                description=tx['description'],
                predicted_category=tx.get('category', 'Uncategorized'),
                merchant_standardized=tx.get('merchant', 'Unknown Merchant')
            ) for tx in transactions
        ]

        # Calculate metrics
        total_spending = sum(abs(Decimal(str(tx['amount']))) for tx in transactions if Decimal(str(tx['amount'])) < 0)
        transaction_count = len(transactions)
        average_transaction = total_spending / transaction_count if transaction_count > 0 else Decimal(0)

        # Get category breakdown
        category_totals = {}
        for tx in transactions:
            if Decimal(str(tx['amount'])) < 0:  # Only expenses
                category = tx.get('category', 'Uncategorized')
                category_totals[category] = category_totals.get(category, Decimal(0)) + abs(Decimal(str(tx['amount'])))

        # Find top category
        top_category = max(category_totals.items(), key=lambda x: x[1])[0] if category_totals else None

        # Get trend from pattern analyzer
        if classified_txns:
            result = self.pattern_analyzer.process(classified_txns)
            trend_analysis = result.spending_trends.get('monthly', {})
            spending_trend = trend_analysis.get('trend', 'stable')
        else:
            spending_trend = 'stable'

        # Compare with previous period
        period_days = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_days)
        previous_end = start_date - timedelta(days=1)

        previous_txns = await self.get_transactions_for_period(
            user_id, previous_start, previous_end, categories
        )
        previous_total = sum(abs(Decimal(str(tx['amount']))) for tx in previous_txns if Decimal(str(tx['amount'])) < 0)

        period_comparison = {
            'previous_period': previous_total,
            'change': ((total_spending - previous_total) / previous_total * 100) if previous_total else 0
        }

        return SpendingAnalytics(
            period=period,
            total_spending=total_spending,
            average_transaction=average_transaction,
            transaction_count=transaction_count,
            top_category=top_category,
            spending_trend=spending_trend,
            period_comparison=period_comparison,
            category_breakdown=category_totals
        )

    async def get_category_breakdown(
        self,
        user_id: str,
        period: str,
        start_date: date,
        end_date: date
    ) -> CategoryBreakdown:
        """Get detailed breakdown of spending by category"""
        transactions = await self.get_transactions_for_period(user_id, start_date, end_date)

        # Calculate category metrics
        categories = {}
        total_amount = Decimal(0)

        for tx in transactions:
            amount = abs(Decimal(str(tx['amount'])))
            category = tx.get('category', 'Uncategorized')

            if category not in categories:
                categories[category] = {
                    'total': Decimal(0),
                    'count': 0,
                    'average': Decimal(0),
                    'percentage': 0
                }
            categories[category]['total'] += amount
            categories[category]['count'] += 1
            total_amount += amount

        # Calculate percentages and averages
        for cat in categories.values():
            cat['average'] = cat['total'] / cat['count'] if cat['count'] > 0 else Decimal(0)
            cat['percentage'] = (cat['total'] / total_amount * 100) if total_amount > 0 else Decimal(0)

        # Get top categories by spending
        top_categories = [
            {
                'category': cat,
                'total': data['total'],
                'percentage': data['percentage'],
                'transaction_count': data['count']
            }
            for cat, data in sorted(
                categories.items(),
                key=lambda x: x[1]['total'],
                reverse=True
            )[:5]
        ]

        return CategoryBreakdown(
            period=period,
            categories=categories,
            total_amount=total_amount,
            category_count=len(categories),
            top_categories=top_categories
        )

    async def get_trend_analysis(
        self,
        user_id: str,
        metric: str,
        period: str,
        start_date: date,
        end_date: date
    ) -> TrendAnalysis:
        """Get trend analysis for specified metric over time"""
        transactions = await self.get_transactions_for_period(user_id, start_date, end_date)

        # Get period duration in days
        period_durations = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'yearly': 365
        }
        period_days = period_durations.get(period, 30)

        # Group transactions by period
        period_groups = {}
        for tx in transactions:
            tx_date = datetime.fromisoformat(tx['date']).date() if isinstance(tx['date'], str) else tx['date']
            period_start = tx_date - timedelta(days=tx_date.toordinal() % period_days)
            if period_start not in period_groups:
                period_groups[period_start] = []
            period_groups[period_start].append(tx)

        # Calculate metric values for each period
        data_points = []
        for period_start, period_txns in sorted(period_groups.items()):
            if metric == "spending":
                value = sum(abs(Decimal(str(tx['amount']))) for tx in period_txns if Decimal(str(tx['amount'])) < 0)
            elif metric == "income":
                value = sum(Decimal(str(tx['amount'])) for tx in period_txns if Decimal(str(tx['amount'])) > 0)
            elif metric == "balance":
                value = sum(Decimal(str(tx['amount'])) for tx in period_txns)
            else:  # transactions count
                value = len(period_txns)

            data_points.append({
                'date': period_start,
                'value': value
            })

        # Calculate trend direction and strength
        if len(data_points) >= 2:
            values = [float(dp['value']) for dp in data_points]
            avg_change = (values[-1] - values[0]) / len(values)
            trend_direction = 'increasing' if avg_change > 0 else 'decreasing' if avg_change < 0 else 'stable'

            # Calculate trend strength (normalized)
            if len(values) > 1:
                std_val = statistics.stdev(values)
                mean_val = statistics.mean(values)
                trend_strength = min(abs(avg_change) / (std_val + 1e-6), 1.0) if std_val > 0 else 0.5
            else:
                trend_strength = 0.5
        else:
            trend_direction = 'stable'
            trend_strength = 0.5

        # Simple forecast based on trend
        forecast = []
        if len(data_points) >= 2:
            last_value = data_points[-1]['value']
            avg_change = (data_points[-1]['value'] - data_points[0]['value']) / len(data_points)

            for i in range(3):
                forecast_date = data_points[-1]['date'] + timedelta(days=period_days * (i + 1))
                forecast_value = last_value + (avg_change * (i + 1))
                confidence = max(0.3, 0.9 - (0.15 * i))  # Decreasing confidence

                forecast.append({
                    'date': forecast_date,
                    'value': forecast_value,
                    'confidence': confidence
                })

        return TrendAnalysis(
            metric=metric,
            period=period,
            data_points=data_points,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            forecast=forecast
        )

    async def get_dashboard_summary(
        self,
        user_id: str,
        current_period_start: date,
        current_period_end: date,
        previous_period_start: date,
        previous_period_end: date
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard summary comparing current and previous periods"""
        current_transactions = await self.get_transactions_for_period(
            user_id, current_period_start, current_period_end
        )

        previous_transactions = await self.get_transactions_for_period(
            user_id, previous_period_start, previous_period_end
        )

        # Calculate current period metrics
        current_spending = sum(abs(Decimal(str(tx['amount']))) for tx in current_transactions if Decimal(str(tx['amount'])) < 0)
        current_income = sum(Decimal(str(tx['amount'])) for tx in current_transactions if Decimal(str(tx['amount'])) > 0)
        current_balance = sum(Decimal(str(tx['amount'])) for tx in current_transactions)

        # Calculate previous period metrics
        previous_spending = sum(abs(Decimal(str(tx['amount']))) for tx in previous_transactions if Decimal(str(tx['amount'])) < 0)

        # Calculate spending change percentage
        spending_change = ((current_spending - previous_spending) / previous_spending * 100) if previous_spending else 0

        # Get category breakdown for current period
        category_totals = {}
        for tx in current_transactions:
            if Decimal(str(tx['amount'])) < 0:
                category = tx.get('category', 'Uncategorized')
                category_totals[category] = category_totals.get(category, Decimal(0)) + abs(Decimal(str(tx['amount'])))

        # Get top 5 spending categories
        top_categories = [
            {
                'category': category,
                'amount': amount,
                'percentage': (amount / current_spending * 100) if current_spending else 0
            }
            for category, amount in sorted(
                category_totals.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]

        return {
            "current_balance": current_balance,
            "current_spending": current_spending,
            "current_income": current_income,
            "previous_spending": previous_spending,
            "spending_change": spending_change,
            "transaction_count": len(current_transactions),
            "top_categories": top_categories,
            "period_start": current_period_start.isoformat(),
            "period_end": current_period_end.isoformat()
        }

    async def get_top_merchants(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get top merchants by spending amount and frequency"""
        transactions = await self.get_transactions_for_period(user_id, start_date, end_date)

        # Filter expenses only
        expense_txns = [tx for tx in transactions if Decimal(str(tx['amount'])) < 0]

        # Aggregate by merchant
        merchant_stats = {}
        for tx in expense_txns:
            merchant = tx.get('merchant', 'Unknown')
            if merchant not in merchant_stats:
                merchant_stats[merchant] = {
                    'total_amount': Decimal(0),
                    'transaction_count': 0,
                    'categories': set(),
                    'last_transaction': None
                }

            stats = merchant_stats[merchant]
            stats['total_amount'] += abs(Decimal(str(tx['amount'])))
            stats['transaction_count'] += 1
            stats['categories'].add(tx.get('category', 'Uncategorized'))

            tx_date = datetime.fromisoformat(tx['date']).date() if isinstance(tx['date'], str) else tx['date']
            stats['last_transaction'] = max(tx_date, stats['last_transaction']) if stats['last_transaction'] else tx_date

        # Prepare results
        results = []
        for merchant, stats in merchant_stats.items():
            avg_transaction = stats['total_amount'] / stats['transaction_count']
            results.append({
                'merchant': merchant,
                'total_spent': stats['total_amount'],
                'transaction_count': stats['transaction_count'],
                'average_transaction': avg_transaction,
                'categories': list(stats['categories']),
                'last_transaction_date': stats['last_transaction'].isoformat()
            })

        # Sort by total spent and limit results
        return sorted(results, key=lambda x: x['total_spent'], reverse=True)[:limit]

    async def get_spending_forecast(
        self,
        user_id: str,
        forecast_days: int
    ) -> Dict[str, Any]:
        """Generate spending forecast based on historical patterns"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)

        transactions = await self.get_transactions_for_period(user_id, start_date, end_date)
        expense_txns = [tx for tx in transactions if Decimal(str(tx['amount'])) < 0]

        # Calculate daily average spending
        total_spending = sum(abs(Decimal(str(tx['amount']))) for tx in expense_txns)
        days_covered = (end_date - start_date).days or 1
        daily_average = total_spending / days_covered

        # Use pattern analyzer for trend
        if expense_txns:
            classified_txns = [
                ClassifiedTransaction(
                    id=str(tx['id']),
                    user_id=tx['user_id'],
                    date=datetime.fromisoformat(tx['date']).date() if isinstance(tx['date'], str) else tx['date'],
                    amount=Decimal(str(tx['amount'])),
                    description=tx['description'],
                    predicted_category=tx.get('category', 'Uncategorized'),
                    merchant_standardized=tx.get('merchant', 'Unknown')
                ) for tx in expense_txns
            ]

            pattern_results = self.pattern_analyzer.process(classified_txns)
            trend_info = pattern_results.spending_trends.get('monthly', {})
            trend_direction = trend_info.get('trend', 'stable')
            trend_strength = trend_info.get('trend_strength', 0.5)
        else:
            trend_direction = 'stable'
            trend_strength = 0.5

        # Adjust prediction based on trend
        trend_factor = {'increasing': 1.1, 'decreasing': 0.9, 'stable': 1.0}.get(trend_direction, 1.0)
        base_prediction = daily_average * forecast_days
        adjusted_prediction = base_prediction * trend_factor

        # Calculate confidence
        data_confidence = min(days_covered / 90, 1.0)
        transaction_confidence = min(len(expense_txns) / 50, 1.0) if expense_txns else 0.1
        horizon_confidence = max(0.5, 1.0 - (forecast_days / 90))
        confidence = (data_confidence * 0.4 + transaction_confidence * 0.3 + horizon_confidence * 0.3)
        confidence = max(0.2, min(0.95, confidence))

        return {
            "forecast_days": forecast_days,
            "predicted_spending": adjusted_prediction,
            "confidence": confidence,
            "base_daily_average": daily_average,
            "trend_direction": trend_direction,
            "historical_days": days_covered
        }

    async def get_cash_flow_analysis(
        self,
        user_id: str,
        period: str,
        lookback_periods: int
    ) -> CashFlowAnalysis:
        """Analyze cash flow patterns over multiple periods"""
        period_duration = {
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
            'yearly': timedelta(days=365)
        }.get(period, timedelta(days=30))

        end_date = datetime.now().date()
        start_date = end_date - (period_duration * lookback_periods)

        transactions = await self.get_transactions_for_period(user_id, start_date, end_date)

        # Analyze cash flow by period
        periods_data = []
        for i in range(lookback_periods):
            period_end = end_date - (period_duration * i)
            period_start = period_end - period_duration

            period_txns = [
                tx for tx in transactions
                if period_start <= (datetime.fromisoformat(tx['date']).date() if isinstance(tx['date'], str) else tx['date']) <= period_end
            ]

            income = sum(Decimal(str(tx['amount'])) for tx in period_txns if Decimal(str(tx['amount'])) > 0)
            expenses = abs(sum(Decimal(str(tx['amount'])) for tx in period_txns if Decimal(str(tx['amount'])) < 0))
            net = income - expenses

            periods_data.append({
                'period': period_start.strftime('%Y-%m-%d'),
                'income': income,
                'expenses': expenses,
                'net': net
            })

        # Calculate averages
        if periods_data:
            avg_income = sum(p['income'] for p in periods_data) / len(periods_data)
            avg_expenses = sum(p['expenses'] for p in periods_data) / len(periods_data)
            avg_net = avg_income - avg_expenses
        else:
            avg_income = avg_expenses = avg_net = Decimal(0)

        return CashFlowAnalysis(
            period=period,
            periods=periods_data,
            average_income=avg_income,
            average_expenses=avg_expenses,
            average_net=avg_net,
            trend='stable'  # Simplified
        )

    async def get_spending_patterns(
        self,
        user_id: str
    ) -> SpendingPattern:
        """Get spending patterns analysis using pattern analyzer agent"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)

        transactions = await self.get_transactions_for_period(user_id, start_date, end_date)

        # Convert to ClassifiedTransaction objects
        classified_txns = [
            ClassifiedTransaction(
                id=str(tx['id']),
                user_id=tx['user_id'],
                date=datetime.fromisoformat(tx['date']).date() if isinstance(tx['date'], str) else tx['date'],
                amount=Decimal(str(tx['amount'])),
                description=tx['description'],
                predicted_category=tx.get('category', 'Uncategorized'),
                merchant_standardized=tx.get('merchant', 'Unknown')
            ) for tx in transactions
        ]

        if not classified_txns:
            return SpendingPattern(
                by_day_of_week={},
                by_hour_of_day={},
                by_month={},
                seasonal_trends={},
                peak_spending_times=[]
            )

        # Process with pattern analyzer
        result = self.pattern_analyzer.process(classified_txns)
        spending_trends = result.spending_trends
        monthly_patterns = spending_trends.get('monthly', {})

        return SpendingPattern(
            by_day_of_week=monthly_patterns.get('day_of_week_distribution', {}),
            by_hour_of_day=monthly_patterns.get('hour_distribution', {}),
            by_month=spending_trends.get('category', {}).get('monthly_totals', {}),
            seasonal_trends={},
            peak_spending_times=[]
        )

    async def get_category_comparison(
        self,
        user_id: str,
        compare_periods: int,
        period_type: str
    ) -> Dict[str, Any]:
        """Compare category spending across multiple periods"""
        period_duration = {
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
            'yearly': timedelta(days=365)
        }.get(period_type, timedelta(days=30))

        end_date = datetime.now().date()
        start_date = end_date - (period_duration * compare_periods)

        transactions = await self.get_transactions_for_period(user_id, start_date, end_date)
        expense_txns = [tx for tx in transactions if Decimal(str(tx['amount'])) < 0]

        # Group by period and category
        period_categories = {}
        all_categories = set()

        for tx in expense_txns:
            tx_date = datetime.fromisoformat(tx['date']).date() if isinstance(tx['date'], str) else tx['date']
            period_start = tx_date - timedelta(days=tx_date.toordinal() % period_duration.days)
            period_key = period_start.isoformat()
            category = tx.get('category', 'Uncategorized')

            if period_key not in period_categories:
                period_categories[period_key] = {}
            if category not in period_categories[period_key]:
                period_categories[period_key][category] = Decimal(0)

            period_categories[period_key][category] += abs(Decimal(str(tx['amount'])))
            all_categories.add(category)

        # Calculate trends
        category_trends = {}
        for category in all_categories:
            values = [float(period_categories.get(p, {}).get(category, Decimal(0))) for p in sorted(period_categories.keys())]

            if len(values) >= 2:
                change = ((values[-1] - values[0]) / values[0] * 100) if values[0] else 0
                trend = 'increasing' if change > 10 else 'decreasing' if change < -10 else 'stable'
            else:
                change = 0
                trend = 'insufficient_data'

            category_trends[category] = {
                'change': change,
                'trend': trend,
                'average': sum(values) / len(values) if values else 0
            }

        return {
            "periods": compare_periods,
            "period_type": period_type,
            "comparison": {cat: {p: period_categories.get(p, {}).get(cat, Decimal(0)) for p in sorted(period_categories.keys())} for cat in all_categories},
            "category_trends": category_trends,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }

    async def detect_spending_anomalies(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        sensitivity: float
    ) -> Dict[str, Any]:
        """Detect spending anomalies using pattern analysis"""
        transactions = await self.get_transactions_for_period(user_id, start_date, end_date)

        # Calculate category averages and standard deviations
        category_averages = {}
        category_stddev = {}
        anomalies = []

        for tx in transactions:
            category = tx.get('category', 'Uncategorized')
            if category not in category_averages:
                category_txns = [t for t in transactions if t.get('category', 'Uncategorized') == category]
                amounts = [abs(float(t['amount'])) for t in category_txns]
                if amounts and len(amounts) > 1:
                    avg = statistics.mean(amounts)
                    stddev = statistics.stdev(amounts)
                    category_averages[category] = avg
                    category_stddev[category] = stddev

        # Detect anomalies
        for tx in transactions:
            category = tx.get('category', 'Uncategorized')
            if category in category_averages and category in category_stddev:
                amount = abs(float(tx['amount']))
                avg = category_averages[category]
                stddev = category_stddev[category]
                z_score = (amount - avg) / stddev if stddev > 0 else 0

                if abs(z_score) > (3 * sensitivity):
                    tx_date = datetime.fromisoformat(tx['date']).date() if isinstance(tx['date'], str) else tx['date']
                    anomalies.append({
                        'type': 'category_anomaly',
                        'date': tx_date.isoformat(),
                        'amount': amount,
                        'category': category,
                        'merchant': tx.get('merchant', 'Unknown'),
                        'description': tx['description'],
                        'deviation': z_score,
                        'average': avg
                    })

        risk_score = min(len(anomalies) / max(len(transactions), 1) * 10, 1.0) if transactions else 0.0

        return {
            "anomalies": sorted(anomalies, key=lambda x: abs(x['deviation']), reverse=True),
            "risk_score": risk_score,
            "total_transactions": len(transactions),
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

    async def generate_custom_report(
        self,
        user_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate customized financial report based on configuration"""
        report_data = {}
        start_date = datetime.strptime(config.get('start_date', ''), '%Y-%m-%d').date()
        end_date = datetime.strptime(config.get('end_date', ''), '%Y-%m-%d').date()

        # Process requested sections
        for section in config.get('sections', []):
            if section == 'spending_analytics':
                analytics = await self.get_spending_analytics(
                    user_id,
                    config.get('period', 'monthly'),
                    start_date,
                    end_date
                )
                report_data['spending_analytics'] = analytics.dict()

            elif section == 'category_breakdown':
                breakdown = await self.get_category_breakdown(
                    user_id,
                    config.get('period', 'monthly'),
                    start_date,
                    end_date
                )
                report_data['category_breakdown'] = breakdown.dict()

            elif section == 'trends':
                for metric in config.get('metrics', ['spending']):
                    trends = await self.get_trend_analysis(
                        user_id,
                        metric,
                        config.get('period', 'monthly'),
                        start_date,
                        end_date
                    )
                    report_data[f'{metric}_trends'] = trends.dict()

            elif section == 'anomalies':
                anomalies = await self.detect_spending_anomalies(
                    user_id,
                    start_date,
                    end_date,
                    config.get('sensitivity', 1.0)
                )
                report_data['spending_anomalies'] = anomalies

        return {
            "report_type": "custom",
            "config": config,
            "data": report_data,
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
