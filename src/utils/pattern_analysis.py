"""Pattern analysis utilities for detecting spending patterns"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics


class PatternDetector:
    """Utility class for detecting spending patterns and habits"""
    
    def __init__(self):
        self.recurring_threshold = 3  # Minimum occurrences to be considered recurring
        self.spike_multiplier = 2.5   # Multiplier for detecting spending spikes
    
    def detect_recurring_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect recurring transactions based on merchant and amount similarity"""
        recurring_patterns = []
        
        # Group transactions by merchant
        merchant_groups = defaultdict(list)
        for txn in transactions:
            merchant = txn.get('merchant_standardized', 'Unknown')
            merchant_groups[merchant].append(txn)
        
        for merchant, txns in merchant_groups.items():
            if len(txns) >= self.recurring_threshold:
                # Analyze amount patterns
                amounts = [txn.get('amount', 0) for txn in txns]
                
                # Check for consistent amounts (within 10% variance)
                if amounts:
                    avg_amount = statistics.mean(amounts)
                    consistent_amounts = [amt for amt in amounts if abs(amt - avg_amount) / avg_amount <= 0.1]
                    
                    if len(consistent_amounts) >= self.recurring_threshold:
                        # Calculate frequency
                        dates = [datetime.fromisoformat(txn.get('date', '2024-01-01').replace('Z', '+00:00')) 
                                for txn in txns if txn.get('date')]
                        
                        if len(dates) >= 2:
                            dates.sort()
                            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                            avg_interval = statistics.mean(intervals) if intervals else 0
                            
                            recurring_patterns.append({
                                'merchant': merchant,
                                'category': txns[0].get('predicted_category', 'unknown'),
                                'avg_amount': avg_amount,
                                'frequency_days': avg_interval,
                                'occurrence_count': len(consistent_amounts),
                                'pattern_type': 'recurring',
                                'confidence': min(len(consistent_amounts) / 10, 1.0)
                            })
        
        return recurring_patterns
    
    def detect_spending_spikes(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect unusual spending spikes by category and time period"""
        spikes = []
        
        # Group by category and month
        category_monthly = defaultdict(lambda: defaultdict(list))
        for txn in transactions:
            category = txn.get('predicted_category', 'unknown')
            amount = txn.get('amount', 0)
            
            try:
                date = datetime.fromisoformat(txn.get('date', '2024-01-01').replace('Z', '+00:00'))
                month_key = f"{date.year}-{date.month:02d}"
                category_monthly[category][month_key].append(amount)
            except:
                continue
        
        # Analyze each category for spikes
        for category, monthly_data in category_monthly.items():
            monthly_totals = {month: sum(amounts) for month, amounts in monthly_data.items()}
            
            if len(monthly_totals) >= 2:
                totals = list(monthly_totals.values())
                avg_spending = statistics.mean(totals)
                
                for month, total in monthly_totals.items():
                    if total > avg_spending * self.spike_multiplier:
                        spikes.append({
                            'category': category,
                            'month': month,
                            'amount': total,
                            'avg_amount': avg_spending,
                            'spike_ratio': total / avg_spending if avg_spending > 0 else 0,
                            'pattern_type': 'spike',
                            'severity': 'high' if total > avg_spending * 4 else 'medium'
                        })
        
        return spikes
    
    def analyze_monthly_habits(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze monthly spending habits and patterns"""
        monthly_analysis = {
            'category_breakdown': defaultdict(float),
            'weekday_vs_weekend': {'weekday': 0, 'weekend': 0},
            'monthly_trends': defaultdict(float),
            'payment_method_usage': defaultdict(float),
            'average_transaction_size': 0,
            'most_frequent_merchants': []
        }
        
        weekday_amounts = []
        weekend_amounts = []
        merchant_counts = Counter()
        
        for txn in transactions:
            amount = abs(txn.get('amount', 0))  # Use absolute value for spending analysis
            category = txn.get('predicted_category', 'unknown')
            payment_method = txn.get('payment_method', 'unknown')
            merchant = txn.get('merchant_standardized', 'Unknown')
            
            # Category breakdown
            monthly_analysis['category_breakdown'][category] += amount
            
            # Payment method usage
            monthly_analysis['payment_method_usage'][payment_method] += amount
            
            # Merchant frequency
            merchant_counts[merchant] += 1
            
            # Weekday vs weekend analysis
            try:
                date = datetime.fromisoformat(txn.get('date', '2024-01-01').replace('Z', '+00:00'))
                if date.weekday() < 5:  # Monday = 0, Sunday = 6
                    weekday_amounts.append(amount)
                else:
                    weekend_amounts.append(amount)
                
                # Monthly trends
                month_key = f"{date.year}-{date.month:02d}"
                monthly_analysis['monthly_trends'][month_key] += amount
            except:
                continue
        
        # Calculate averages
        if weekday_amounts:
            monthly_analysis['weekday_vs_weekend']['weekday'] = statistics.mean(weekday_amounts)
        if weekend_amounts:
            monthly_analysis['weekday_vs_weekend']['weekend'] = statistics.mean(weekend_amounts)
        
        all_amounts = [txn.get('amount', 0) for txn in transactions]
        if all_amounts:
            monthly_analysis['average_transaction_size'] = statistics.mean(all_amounts)
        
        # Most frequent merchants
        monthly_analysis['most_frequent_merchants'] = merchant_counts.most_common(10)
        
        return dict(monthly_analysis)
    
    def detect_seasonal_patterns(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect seasonal spending patterns"""
        seasonal_patterns = []
        
        # Group by month and category
        monthly_category = defaultdict(lambda: defaultdict(float))
        
        for txn in transactions:
            try:
                date = datetime.fromisoformat(txn.get('date', '2024-01-01').replace('Z', '+00:00'))
                month = date.month
                category = txn.get('predicted_category', 'unknown')
                amount = abs(txn.get('amount', 0))
                
                monthly_category[month][category] += amount
            except:
                continue
        
        # Analyze seasonal patterns
        for category in set().union(*(d.keys() for d in monthly_category.values())):
            monthly_totals = [monthly_category[month].get(category, 0) for month in range(1, 13)]
            
            if sum(monthly_totals) > 0:
                # Find peak months
                max_amount = max(monthly_totals)
                peak_months = [i+1 for i, amount in enumerate(monthly_totals) if amount > max_amount * 0.8]
                
                if peak_months and max_amount > 0:
                    seasonal_patterns.append({
                        'category': category,
                        'peak_months': peak_months,
                        'peak_amount': max_amount,
                        'pattern_type': 'seasonal',
                        'season': self._get_season_name(peak_months)
                    })
        
        return seasonal_patterns
    
    def _get_season_name(self, months: List[int]) -> str:
        """Get season name based on peak months"""
        if any(month in [12, 1, 2] for month in months):
            return 'winter'
        elif any(month in [3, 4, 5] for month in months):
            return 'spring'
        elif any(month in [6, 7, 8] for month in months):
            return 'summer'
        elif any(month in [9, 10, 11] for month in months):
            return 'fall'
        else:
            return 'year-round'
    
    def calculate_pattern_insights(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate comprehensive pattern insights"""
        insights = []
        
        # Get all pattern types
        recurring = self.detect_recurring_transactions(transactions)
        spikes = self.detect_spending_spikes(transactions)
        habits = self.analyze_monthly_habits(transactions)
        seasonal = self.detect_seasonal_patterns(transactions)
        
        # Convert to insights format
        for pattern in recurring:
            insights.append({
                'insight_type': 'recurring',
                'category': pattern['category'],
                'description': f"Recurring transaction at {pattern['merchant']} every {pattern['frequency_days']:.0f} days",
                'severity': 'low',
                'transactions_involved': [],
                'metadata': pattern
            })
        
        for spike in spikes:
            insights.append({
                'insight_type': 'spike',
                'category': spike['category'],
                'description': f"Spending spike in {spike['category']} during {spike['month']}",
                'severity': spike['severity'],
                'transactions_involved': [],
                'metadata': spike
            })
        
        # Add habit insights
        if habits['weekday_vs_weekend']['weekend'] > habits['weekday_vs_weekend']['weekday'] * 1.5:
            insights.append({
                'insight_type': 'habit',
                'category': None,
                'description': "Significantly higher spending on weekends",
                'severity': 'medium',
                'transactions_involved': [],
                'metadata': habits['weekday_vs_weekend']
            })
        
        return insights
