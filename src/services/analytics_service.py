"""
Analytics Service - Implements financial analytics using pattern analyzer
and database queries for user transaction analysis
"""

from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models.analytics import (
    SpendingAnalytics, CategoryBreakdown, TrendAnalysis,
    SpendingPattern, CashFlowAnalysis, AnalyticsPeriod
)
from ..models.transaction import Transaction
from ..agents.pattern_analyzer_agent import PatternAnalyzerAgent
from ..schemas.transaction_schemas import ClassifiedTransaction

class AnalyticsService:
    """Service for financial analytics and pattern detection"""
    
    def __init__(self, db: Session):
        self.db = db
        self.pattern_analyzer = PatternAnalyzerAgent()
    
    async def get_spending_analytics(self, user_id: str, period: str, start_date: date, end_date: date, categories: List[str] = None) -> SpendingAnalytics:
        """Get comprehensive spending analytics for a given period"""
        # Query transactions for the period
        query = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        )
        
        if categories:
            query = query.filter(Transaction.category.in_(categories))
            
        transactions = query.all()
        
        # Convert to ClassifiedTransaction objects
        classified_txns = [
            ClassifiedTransaction(
                id=str(tx.id),
                user_id=tx.user_id,
                date=tx.date,
                amount=tx.amount,
                description=tx.description,
                category=tx.category,
                merchant=tx.merchant
            ) for tx in transactions
        ]
        
        # Process with pattern analyzer
        result = self.pattern_analyzer.process(classified_txns)
        
        # Calculate metrics
        total_spending = sum(tx.amount for tx in transactions)
        transaction_count = len(transactions)
        average_transaction = total_spending / transaction_count if transaction_count > 0 else Decimal(0)
        
        # Get category breakdown
        category_totals = {}
        for tx in transactions:
            category_totals[tx.category] = category_totals.get(tx.category, Decimal(0)) + tx.amount
        
        # Find top category
        top_category = max(category_totals.items(), key=lambda x: x[1])[0] if category_totals else None
        
        # Get trend from pattern analyzer
        trend_analysis = result.spending_trends.get('monthly', {})
        spending_trend = trend_analysis.get('trend', 'stable')
        
        # Compare with previous period
        previous_start = start_date - timedelta(days=(end_date - start_date).days)
        previous_end = start_date - timedelta(days=1)
        
        previous_total = (
            self.db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= previous_start,
                Transaction.date <= previous_end
            )
            .scalar() or Decimal(0)
        )
        
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
    
    async def get_category_breakdown(self, user_id: str, period: str, start_date: date, end_date: date) -> CategoryBreakdown:
        """Get detailed breakdown of spending by category"""
        # Query transactions
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            .all()
        )
        
        # Process with pattern analyzer for category insights
        classified_txns = [
            ClassifiedTransaction(
                id=str(tx.id),
                user_id=tx.user_id,
                date=tx.date,
                amount=tx.amount,
                description=tx.description,
                category=tx.category,
                merchant=tx.merchant
            ) for tx in transactions
        ]
        
        # Process with pattern analyzer
        pattern_results = self.pattern_analyzer.process(classified_txns)
        
        # Calculate category metrics
        categories = {}
        total_amount = Decimal(0)
        
        for tx in transactions:
            if tx.category not in categories:
                categories[tx.category] = {
                    'total': Decimal(0),
                    'count': 0,
                    'average': Decimal(0),
                    'percentage': 0
                }
            categories[tx.category]['total'] += abs(tx.amount)
            categories[tx.category]['count'] += 1
            total_amount += abs(tx.amount)
        
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
            )[:5]  # Top 5 categories
        ]
        
        return CategoryBreakdown(
            period=period,
            categories=categories,
            total_amount=total_amount,
            category_count=len(categories),
            top_categories=top_categories
        )
    
    async def get_trend_analysis(self, user_id: str, metric: str, period: str, start_date: date, end_date: date) -> TrendAnalysis:
        """Get trend analysis for specified metric over time"""
        # Query transactions
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            .order_by(Transaction.date)
            .all()
        )
        
        # Convert to ClassifiedTransaction objects for pattern analyzer
        classified_txns = [
            ClassifiedTransaction(
                id=str(tx.id),
                user_id=tx.user_id,
                date=tx.date,
                amount=tx.amount,
                description=tx.description,
                category=tx.category,
                merchant=tx.merchant
            ) for tx in transactions
        ]
        
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
            period_start = tx.date - timedelta(days=tx.date.toordinal() % period_days)
            if period_start not in period_groups:
                period_groups[period_start] = []
            period_groups[period_start].append(tx)
        
        # Calculate metric values for each period
        data_points = []
        for period_start, period_txns in sorted(period_groups.items()):
            if metric == "spending":
                value = sum(abs(tx.amount) for tx in period_txns if tx.amount < 0)
            elif metric == "income":
                value = sum(tx.amount for tx in period_txns if tx.amount > 0)
            elif metric == "balance":
                value = sum(tx.amount for tx in period_txns)
            else:  # transactions count
                value = len(period_txns)
                
            data_points.append({
                'date': period_start,
                'value': value
            })
        
        # Process with pattern analyzer for trend detection
        pattern_results = self.pattern_analyzer.process(classified_txns)
        
        # Get trend information
        trend_info = pattern_results.get('spending_trends', {}).get('monthly_patterns', {})
        trend_direction = trend_info.get('trend', 'stable')
        trend_strength = trend_info.get('trend_strength', 0.5)
        
        # Simple forecast based on trend
        if len(data_points) >= 2:
            last_value = data_points[-1]['value']
            avg_change = (data_points[-1]['value'] - data_points[0]['value']) / len(data_points)
            forecast = []
            for i in range(3):  # Forecast next 3 periods
                forecast_date = data_points[-1]['date'] + timedelta(days=period_days * (i + 1))
                forecast_value = last_value + (avg_change * (i + 1))
                forecast.append({
                    'date': forecast_date,
                    'value': forecast_value,
                    'confidence': max(0.8 - (0.1 * i), 0.5)  # Decreasing confidence
                })
        else:
            forecast = []
        
        return TrendAnalysis(
            metric=metric,
            period=period,
            data_points=data_points,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            forecast=forecast
        )
    
    async def get_dashboard_summary(self, user_id: str, current_period_start: date, current_period_end: date, previous_period_start: date, previous_period_end: date) -> Dict[str, Any]:
        """Get comprehensive dashboard summary comparing current and previous periods"""
        # Query current period transactions
        current_transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= current_period_start,
                Transaction.date <= current_period_end
            )
            .all()
        )
        
        # Query previous period transactions
        previous_transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= previous_period_start,
                Transaction.date <= previous_period_end
            )
            .all()
        )
        
        # Calculate current period metrics
        current_spending = sum(abs(tx.amount) for tx in current_transactions if tx.amount < 0)
        current_income = sum(tx.amount for tx in current_transactions if tx.amount > 0)
        current_balance = sum(tx.amount for tx in current_transactions)
        
        # Calculate previous period metrics
        previous_spending = sum(abs(tx.amount) for tx in previous_transactions if tx.amount < 0)
        
        # Calculate spending change percentage
        spending_change = ((current_spending - previous_spending) / previous_spending * 100) if previous_spending else 0
        
        # Get category breakdown for current period
        category_totals = {}
        for tx in current_transactions:
            if tx.amount < 0:  # Only consider expenses for top categories
                category_totals[tx.category] = category_totals.get(tx.category, Decimal(0)) + abs(tx.amount)
        
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
    
    async def get_top_merchants(self, user_id: str, start_date: date, end_date: date, limit: int) -> List[Dict[str, Any]]:
        """Get top merchants by spending amount and frequency"""
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount < 0  # Only consider expenses
            )
            .all()
        )
        
        # Aggregate by merchant
        merchant_stats = {}
        for tx in transactions:
            if tx.merchant not in merchant_stats:
                merchant_stats[tx.merchant] = {
                    'total_amount': Decimal(0),
                    'transaction_count': 0,
                    'categories': set(),
                    'average_transaction': Decimal(0),
                    'last_transaction': None
                }
            
            stats = merchant_stats[tx.merchant]
            stats['total_amount'] += abs(tx.amount)
            stats['transaction_count'] += 1
            stats['categories'].add(tx.category)
            stats['last_transaction'] = max(tx.date, stats['last_transaction']) if stats['last_transaction'] else tx.date
        
        # Calculate averages and prepare results
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
        return sorted(
            results,
            key=lambda x: x['total_spent'],
            reverse=True
        )[:limit]
    
    async def get_spending_forecast(self, user_id: str, forecast_days: int) -> Dict[str, Any]:
        """Generate spending forecast based on historical patterns"""
        # Get historical transactions for pattern analysis
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)  # Use last 90 days for training
        
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount < 0  # Only consider expenses
            )
            .order_by(Transaction.date)
            .all()
        )
        
        # Convert to ClassifiedTransaction objects
        classified_txns = [
            ClassifiedTransaction(
                id=str(tx.id),
                user_id=tx.user_id,
                date=tx.date,
                amount=tx.amount,
                description=tx.description,
                category=tx.category,
                merchant=tx.merchant
            ) for tx in transactions
        ]
        
        # Use pattern analyzer for trend analysis
        pattern_results = self.pattern_analyzer.process(classified_txns)
        
        # Calculate daily average spending
        total_spending = sum(abs(tx.amount) for tx in transactions)
        days_covered = (end_date - start_date).days or 1
        daily_average = total_spending / days_covered
        
        # Get trend factors from pattern analysis
        trend_info = pattern_results.spending_trends.get('monthly', {})
        trend_direction = trend_info.get('trend', 'stable')
        trend_strength = trend_info.get('trend_strength', 0.5)
        
        # Adjust prediction based on trend
        trend_factor = {
            'increasing': 1.1,
            'decreasing': 0.9,
            'stable': 1.0
        }.get(trend_direction, 1.0)
        
        # Calculate prediction
        base_prediction = daily_average * forecast_days
        adjusted_prediction = base_prediction * trend_factor
        
        # Calculate confidence based on data quality and trend strength
        data_confidence = min(days_covered / 90, 1.0)  # Higher confidence with more historical data
        confidence = (data_confidence + trend_strength) / 2
        
        return {
            "forecast_days": forecast_days,
            "predicted_spending": adjusted_prediction,
            "confidence": confidence,
            "base_daily_average": daily_average,
            "trend_direction": trend_direction,
            "historical_days": days_covered
        }
    

    
    async def get_cash_flow_analysis(self, user_id: str, period: str, lookback_periods: int) -> CashFlowAnalysis:
        """Analyze cash flow patterns over multiple periods"""
        # Calculate period duration
        period_duration = {
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
            'yearly': timedelta(days=365)
        }.get(period, timedelta(days=30))
        
        end_date = datetime.now().date()
        start_date = end_date - (period_duration * lookback_periods)
        
        # Query transactions for the entire period
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            .order_by(Transaction.date)
            .all()
        )
        
        # Process with pattern analyzer for trend detection
        classified_txns = [
            ClassifiedTransaction(
                id=str(tx.id),
                user_id=tx.user_id,
                date=tx.date,
                amount=tx.amount,
                description=tx.description,
                category=tx.category,
                merchant=tx.merchant
            ) for tx in transactions
        ]
        
        pattern_results = self.pattern_analyzer.process(classified_txns)
        
        # Analyze cash flow by period
        periods_data = []
        for i in range(lookback_periods):
            period_end = end_date - (period_duration * i)
            period_start = period_end - period_duration
            
            period_txns = [tx for tx in transactions 
                          if period_start <= tx.date <= period_end]
            
            income = sum(tx.amount for tx in period_txns if tx.amount > 0)
            expenses = abs(sum(tx.amount for tx in period_txns if tx.amount < 0))
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
        
        # Get trend from pattern analysis
        trend = pattern_results.spending_trends.get('monthly', {}).get('trend', 'stable')
        
        return CashFlowAnalysis(
            period=period,
            periods=periods_data,
            average_income=avg_income,
            average_expenses=avg_expenses,
            average_net=avg_net,
            trend=trend
        )
    
    async def get_spending_patterns(self, user_id: str) -> SpendingPattern:
        """Get spending patterns analysis using pattern analyzer agent"""
        # Get user transactions
        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.date)
            .all()
        )
        
        # Convert to ClassifiedTransaction objects
        classified_txns = [
            ClassifiedTransaction(
                id=str(tx.id),
                user_id=tx.user_id,
                date=tx.date,
                amount=tx.amount,
                description=tx.description,
                category=tx.category,
                merchant=tx.merchant
            ) for tx in transactions
        ]
        
        # Process with pattern analyzer
        input_data = PatternAnalyzerAgentInput( # type: ignore
            classified_transactions=classified_txns,
            historical_data=[]  # No additional historical data needed for patterns
        )
        result = self.pattern_analyzer.process(input_data)
        
        # Extract patterns from results
        spending_trends = result.spending_trends
        monthly_patterns = spending_trends.get('monthly', {})
        
        # Create SpendingPattern model
        return SpendingPattern(
            by_day_of_week=monthly_patterns.get('day_of_week_distribution', {}),
            by_hour_of_day=monthly_patterns.get('hour_distribution', {}),
            by_month=spending_trends.get('category', {}).get('monthly_totals', {}),
            seasonal_trends={
                pattern['season']: {
                    'total_spending': pattern['total_spending'],
                    'transaction_count': pattern['transaction_count'],
                    'average_transaction': pattern['average_transaction'],
                    'spending_percentage': pattern['spending_percentage']
                }
                for pattern in spending_trends.get('seasonal', [])
            },
            peak_spending_times=[{
                'period': pattern['period'],
                'amount': pattern['amount'],
                'frequency': pattern['frequency']
            } for pattern in monthly_patterns.get('peak_times', [])]
        )

    
    async def get_category_comparison(self, user_id: str, compare_periods: int, period_type: str) -> Dict[str, Any]:
        """Compare category spending across multiple periods"""
        # Calculate period duration
        period_duration = {
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
            'yearly': timedelta(days=365)
        }.get(period_type, timedelta(days=30))
        
        end_date = datetime.now().date()
        start_date = end_date - (period_duration * compare_periods)
        
        # Get transactions for all periods
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.amount < 0  # Only consider expenses
            )
            .order_by(Transaction.date)
            .all()
        )
        
        # Group transactions by period and category
        period_categories = {}
        all_categories = set()
        
        for tx in transactions:
            period_start = tx.date - timedelta(days=tx.date.toordinal() % period_duration.days)
            period_key = period_start.isoformat()
            
            if period_key not in period_categories:
                period_categories[period_key] = {}
            
            if tx.category not in period_categories[period_key]:
                period_categories[period_key][tx.category] = Decimal(0)
            
            period_categories[period_key][tx.category] += abs(tx.amount)
            all_categories.add(tx.category)
        
        # Prepare period comparison data
        comparison = {
            category: {
                period: period_categories.get(period, {}).get(category, Decimal(0))
                for period in sorted(period_categories.keys())
            }
            for category in all_categories
        }
        
        # Calculate trends and changes
        category_trends = {}
        for category in all_categories:
            values = [period_categories.get(p, {}).get(category, Decimal(0)) 
                     for p in sorted(period_categories.keys())]
            
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
            "comparison": comparison,
            "category_trends": category_trends,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    async def detect_spending_anomalies(self, user_id: str, start_date: date, end_date: date, sensitivity: float) -> Dict[str, Any]:
        """Detect spending anomalies using pattern analysis"""
        # Get transactions
        transactions = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            .order_by(Transaction.date)
            .all()
        )
        
        # Convert to ClassifiedTransaction objects
        classified_txns = [
            ClassifiedTransaction(
                id=str(tx.id),
                user_id=tx.user_id,
                date=tx.date,
                amount=tx.amount,
                description=tx.description,
                category=tx.category,
                merchant=tx.merchant
            ) for tx in transactions
        ]
        
        # Process with pattern analyzer
        # Process with pattern analyzer
        pattern_results = self.pattern_analyzer.process(classified_txns)
        
        # Get spending spikes and patterns
        spending_patterns = pattern_results.spending_trends.get('monthly', {})
        anomalies = []
        
        # Detect category anomalies
        category_averages = {}
        category_stddev = {}
        
        for tx in transactions:
            if tx.category not in category_averages:
                category_txns = [t for t in transactions if t.category == tx.category]
                amounts = [abs(t.amount) for t in category_txns]
                if amounts:
                    avg = sum(amounts) / len(amounts)
                    variance = sum((x - avg) ** 2 for x in amounts) / len(amounts)
                    stddev = variance ** 0.5
                    category_averages[tx.category] = avg
                    category_stddev[tx.category] = stddev
            
            # Check for anomalies
            if tx.category in category_averages:
                avg = category_averages[tx.category]
                stddev = category_stddev[tx.category]
                amount = abs(tx.amount)
                z_score = (amount - avg) / stddev if stddev > 0 else 0
                
                if abs(z_score) > (3 * sensitivity):  # Adjustable threshold
                    anomalies.append({
                        'type': 'category_anomaly',
                        'date': tx.date.isoformat(),
                        'amount': amount,
                        'category': tx.category,
                        'merchant': tx.merchant,
                        'description': tx.description,
                        'deviation': z_score,
                        'average': avg
                    })
        
        # Calculate overall risk score based on anomalies
        risk_score = min(len(anomalies) / len(transactions) + 
                        sum(abs(a['deviation']) for a in anomalies) / (10 * len(transactions)), 
                        1.0) if transactions else 0.0
        
        return {
            "anomalies": sorted(anomalies, key=lambda x: abs(x['deviation']), reverse=True),
            "risk_score": risk_score,
            "total_transactions": len(transactions),
            "analysis_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    async def generate_custom_report(self, user_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
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