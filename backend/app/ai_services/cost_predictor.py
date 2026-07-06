"""Cost Prediction Service

Predicts future AI usage costs using time series forecasting:
- Daily/weekly/monthly cost predictions
- Budget planning recommendations
- Cost optimization suggestions
- Trend analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from app.models.request_log import RequestLog, RequestStatus
from app.models.user import User
from app.models.department import Department


@dataclass
class CostPrediction:
    """Represents a cost prediction."""
    date: datetime
    predicted_cost: float
    lower_bound: float
    upper_bound: float
    confidence: float  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "predicted_cost": round(self.predicted_cost, 4),
            "lower_bound": round(self.lower_bound, 4),
            "upper_bound": round(self.upper_bound, 4),
            "confidence": round(self.confidence, 3)
        }


@dataclass
class CostInsight:
    """Represents a cost insight or recommendation."""
    type: str  # 'optimization', 'warning', 'trend'
    title: str
    description: str
    potential_savings: Optional[float] = None
    priority: str = "medium"  # low, medium, high
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority
        }
        if self.potential_savings:
            result["potential_savings"] = round(self.potential_savings, 4)
        return result


class CostPredictor:
    """AI-powered cost prediction and optimization."""
    
    def __init__(self):
        """Initialize cost predictor with ML models."""
        self.linear_model = LinearRegression()
        self.scaler = StandardScaler()
        
    def predict_costs(
        self,
        db: Session,
        days_ahead: int = 30,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Predict future costs based on historical data.
        
        Args:
            db: Database session
            days_ahead: Number of days to predict
            user_id: Optional user filter
            department_id: Optional department filter
        
        Returns:
            Dict with predictions and insights
        """
        # Get historical data
        historical_data = self._get_historical_costs(
            db, 
            days=90,  # Use 90 days of history
            user_id=user_id,
            department_id=department_id
        )
        
        if len(historical_data) < 7:  # Need at least a week of data
            return {
                "error": "Insufficient historical data",
                "message": "At least 7 days of historical data required for predictions",
                "days_available": len(historical_data)
            }
        
        # Prepare time series data
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Generate predictions
        predictions = self._generate_predictions(df, days_ahead)
        
        # Calculate trends
        trends = self._analyze_trends(df)
        
        # Generate insights
        insights = self._generate_insights(df, predictions, user_id, department_id)
        
        # Calculate budget recommendations
        budget_recs = self._calculate_budget_recommendations(predictions)
        
        return {
            "predictions": [p.to_dict() for p in predictions],
            "trends": trends,
            "insights": [i.to_dict() for i in insights],
            "budget_recommendations": budget_recs,
            "historical_summary": {
                "total_days": len(df),
                "avg_daily_cost": round(df['cost'].mean(), 4),
                "total_cost": round(df['cost'].sum(), 4),
                "min_daily_cost": round(df['cost'].min(), 4),
                "max_daily_cost": round(df['cost'].max(), 4)
            }
        }
    
    def predict_monthly_cost(
        self,
        db: Session,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Predict cost for the remainder of the current month."""
        now = datetime.now()
        days_in_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        days_remaining = (days_in_month.day - now.day) + 1
        
        # Get month-to-date cost
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        query = db.query(RequestLog).filter(
            RequestLog.created_at >= month_start,
            RequestLog.status == RequestStatus.SUCCESS
        )
        
        if user_id:
            query = query.filter(RequestLog.user_id == user_id)
        if department_id:
            query = query.filter(RequestLog.department_id == department_id)
        
        mtd_cost = query.with_entities(
            db.func.sum(RequestLog.total_cost)
        ).scalar() or 0.0
        
        # Predict remaining days
        prediction_result = self.predict_costs(
            db,
            days_ahead=days_remaining,
            user_id=user_id,
            department_id=department_id
        )
        
        if "error" in prediction_result:
            return prediction_result
        
        # Calculate projected month-end cost
        predicted_remaining = sum(
            p["predicted_cost"] 
            for p in prediction_result["predictions"]
        )
        
        projected_total = mtd_cost + predicted_remaining
        
        # Get budget info if department specified
        budget_info = None
        if department_id:
            dept = db.query(Department).filter(Department.id == department_id).first()
            if dept:
                budget_info = {
                    "monthly_budget": dept.monthly_budget,
                    "projected_utilization": round(
                        (projected_total / dept.monthly_budget * 100) if dept.monthly_budget > 0 else 0,
                        2
                    ),
                    "within_budget": projected_total <= dept.monthly_budget,
                    "projected_overage": max(0, projected_total - dept.monthly_budget)
                }
        
        return {
            "month": now.strftime("%Y-%m"),
            "days_elapsed": now.day,
            "days_remaining": days_remaining,
            "month_to_date_cost": round(mtd_cost, 4),
            "predicted_remaining_cost": round(predicted_remaining, 4),
            "projected_month_end_cost": round(projected_total, 4),
            "budget_info": budget_info,
            "daily_predictions": prediction_result["predictions"]
        }
    
    def optimize_costs(
        self,
        db: Session,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate cost optimization recommendations."""
        
        # Get usage patterns
        patterns = self._analyze_usage_patterns(db, user_id, department_id)
        
        # Generate optimization recommendations
        recommendations = []
        potential_savings = 0.0
        
        # Check for expensive model usage
        if patterns['expensive_model_usage'] > 0.5:  # >50% expensive models
            savings = patterns['expensive_model_cost'] * 0.3  # Assume 30% savings
            recommendations.append(CostInsight(
                type="optimization",
                title="Switch to Cost-Effective Models",
                description=f"You're using expensive models {patterns['expensive_model_usage']:.1%} of the time. "
                           f"Consider using GPT-3.5 or Claude Haiku for simpler tasks.",
                potential_savings=savings,
                priority="high"
            ))
            potential_savings += savings
        
        # Check for high token usage
        if patterns['avg_tokens'] > 2000:
            savings = patterns['total_cost'] * 0.15  # 15% savings potential
            recommendations.append(CostInsight(
                type="optimization",
                title="Optimize Token Usage",
                description=f"Average request uses {patterns['avg_tokens']:.0f} tokens. "
                           f"Consider reducing prompt length and implementing response caching.",
                potential_savings=savings,
                priority="medium"
            ))
            potential_savings += savings
        
        # Check for off-peak usage opportunity
        if patterns['peak_usage_ratio'] > 0.7:
            savings = patterns['total_cost'] * 0.10  # 10% savings
            recommendations.append(CostInsight(
                type="optimization",
                title="Shift Non-Urgent Tasks Off-Peak",
                description="70% of requests occur during peak hours. "
                           "Schedule batch processing during off-peak times.",
                potential_savings=savings,
                priority="low"
            ))
            potential_savings += savings
        
        # Check for caching opportunities
        if patterns['duplicate_ratio'] > 0.1:  # >10% similar requests
            savings = patterns['total_cost'] * patterns['duplicate_ratio']
            recommendations.append(CostInsight(
                type="optimization",
                title="Implement Response Caching",
                description=f"{patterns['duplicate_ratio']:.1%} of requests are similar. "
                           f"Implement caching to avoid redundant API calls.",
                potential_savings=savings,
                priority="high"
            ))
            potential_savings += savings
        
        # Check for failed request waste
        if patterns['error_rate'] > 0.05:  # >5% error rate
            savings = patterns['total_cost'] * patterns['error_rate']
            recommendations.append(CostInsight(
                type="optimization",
                title="Reduce Failed Requests",
                description=f"Error rate is {patterns['error_rate']:.1%}. "
                           f"Implement better input validation and retry logic.",
                potential_savings=savings,
                priority="medium"
            ))
            potential_savings += savings
        
        return {
            "analysis_period_days": 30,
            "current_monthly_cost": round(patterns['total_cost'], 4),
            "potential_monthly_savings": round(potential_savings, 4),
            "optimization_percentage": round(
                (potential_savings / patterns['total_cost'] * 100) if patterns['total_cost'] > 0 else 0,
                2
            ),
            "recommendations": [r.to_dict() for r in recommendations],
            "usage_patterns": {
                "total_requests": patterns['total_requests'],
                "avg_tokens_per_request": round(patterns['avg_tokens'], 0),
                "expensive_model_usage": f"{patterns['expensive_model_usage']:.1%}",
                "error_rate": f"{patterns['error_rate']:.1%}",
                "duplicate_requests": f"{patterns['duplicate_ratio']:.1%}"
            }
        }
    
    def _get_historical_costs(
        self,
        db: Session,
        days: int,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get historical daily costs."""
        start_date = datetime.now() - timedelta(days=days)
        
        query = db.query(
            db.func.date(RequestLog.created_at).label('date'),
            db.func.sum(RequestLog.total_cost).label('cost'),
            db.func.count(RequestLog.id).label('requests')
        ).filter(
            RequestLog.created_at >= start_date,
            RequestLog.status == RequestStatus.SUCCESS
        )
        
        if user_id:
            query = query.filter(RequestLog.user_id == user_id)
        if department_id:
            query = query.filter(RequestLog.department_id == department_id)
        
        query = query.group_by(db.func.date(RequestLog.created_at))
        
        results = []
        for row in query.all():
            results.append({
                'date': row.date,
                'cost': float(row.cost or 0),
                'requests': int(row.requests)
            })
        
        return sorted(results, key=lambda x: x['date'])
    
    def _generate_predictions(
        self,
        df: pd.DataFrame,
        days_ahead: int
    ) -> List[CostPrediction]:
        """Generate cost predictions using linear regression."""
        # Prepare features
        df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Create rolling averages
        df['cost_ma7'] = df['cost'].rolling(window=7, min_periods=1).mean()
        
        # Prepare training data
        X = df[['days_since_start', 'day_of_week', 'is_weekend', 'cost_ma7']].values
        y = df['cost'].values
        
        # Fit model
        self.linear_model.fit(X, y)
        
        # Generate future dates
        last_date = df['date'].max()
        future_dates = [last_date + timedelta(days=i+1) for i in range(days_ahead)]
        
        # Prepare future features
        predictions = []
        last_ma7 = df['cost_ma7'].iloc[-1]
        
        for i, future_date in enumerate(future_dates):
            days_since_start = (future_date - df['date'].min()).days
            day_of_week = future_date.dayofweek
            is_weekend = 1 if day_of_week in [5, 6] else 0
            
            # Use last moving average initially, then update with predictions
            cost_ma7 = last_ma7 if i < 7 else np.mean([p.predicted_cost for p in predictions[-7:]])
            
            X_future = np.array([[days_since_start, day_of_week, is_weekend, cost_ma7]])
            predicted_cost = self.linear_model.predict(X_future)[0]
            
            # Calculate confidence based on historical variance
            std_dev = df['cost'].std()
            confidence = 1.0 / (1.0 + (i / days_ahead))  # Decrease confidence for further predictions
            
            # Calculate bounds (confidence interval)
            margin = 1.96 * std_dev * (1 - confidence + 0.5)  # 95% CI
            
            prediction = CostPrediction(
                date=future_date,
                predicted_cost=max(0, predicted_cost),
                lower_bound=max(0, predicted_cost - margin),
                upper_bound=predicted_cost + margin,
                confidence=confidence
            )
            predictions.append(prediction)
        
        return predictions
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze cost trends."""
        # Calculate trend direction
        recent_7d = df.tail(7)['cost'].mean()
        previous_7d = df.tail(14).head(7)['cost'].mean()
        
        trend_change = ((recent_7d - previous_7d) / previous_7d * 100) if previous_7d > 0 else 0
        
        if trend_change > 10:
            trend_direction = "increasing"
            trend_description = f"Costs are increasing by {trend_change:.1f}%"
        elif trend_change < -10:
            trend_direction = "decreasing"
            trend_description = f"Costs are decreasing by {abs(trend_change):.1f}%"
        else:
            trend_direction = "stable"
            trend_description = "Costs are relatively stable"
        
        # Calculate volatility
        volatility = df['cost'].std() / df['cost'].mean() if df['cost'].mean() > 0 else 0
        
        return {
            "direction": trend_direction,
            "change_percentage": round(trend_change, 2),
            "description": trend_description,
            "volatility": round(volatility, 3),
            "volatility_level": "high" if volatility > 0.5 else "medium" if volatility > 0.2 else "low"
        }
    
    def _generate_insights(
        self,
        df: pd.DataFrame,
        predictions: List[CostPrediction],
        user_id: Optional[int],
        department_id: Optional[int]
    ) -> List[CostInsight]:
        """Generate actionable insights from predictions."""
        insights = []
        
        # Check for predicted cost spike
        avg_historical = df['cost'].mean()
        future_costs = [p.predicted_cost for p in predictions[:7]]  # Next 7 days
        avg_predicted = np.mean(future_costs)
        
        if avg_predicted > avg_historical * 1.3:  # 30% increase predicted
            insights.append(CostInsight(
                type="warning",
                title="Cost Spike Predicted",
                description=f"Predicted costs are {((avg_predicted/avg_historical - 1) * 100):.1f}% higher "
                           f"than historical average. Review usage patterns.",
                priority="high"
            ))
        
        # Check for cost decline opportunity
        if avg_predicted < avg_historical * 0.7:  # 30% decrease possible
            insights.append(CostInsight(
                type="trend",
                title="Cost Reduction Detected",
                description="Your optimizations are working! Costs are trending downward.",
                priority="low"
            ))
        
        return insights
    
    def _calculate_budget_recommendations(
        self,
        predictions: List[CostPrediction]
    ) -> Dict[str, Any]:
        """Calculate budget recommendations based on predictions."""
        
        # Calculate monthly projection
        monthly_prediction = sum(p.predicted_cost for p in predictions[:30])
        monthly_upper_bound = sum(p.upper_bound for p in predictions[:30])
        
        # Recommend budget with 20% buffer
        recommended_budget = monthly_upper_bound * 1.2
        
        return {
            "predicted_monthly_cost": round(monthly_prediction, 4),
            "upper_bound_monthly": round(monthly_upper_bound, 4),
            "recommended_monthly_budget": round(recommended_budget, 4),
            "buffer_percentage": 20,
            "confidence_level": "95%"
        }
    
    def _analyze_usage_patterns(
        self,
        db: Session,
        user_id: Optional[int],
        department_id: Optional[int]
    ) -> Dict[str, Any]:
        """Analyze usage patterns for optimization."""
        # Last 30 days
        start_date = datetime.now() - timedelta(days=30)
        
        query = db.query(RequestLog).filter(
            RequestLog.created_at >= start_date
        )
        
        if user_id:
            query = query.filter(RequestLog.user_id == user_id)
        if department_id:
            query = query.filter(RequestLog.department_id == department_id)
        
        all_requests = query.all()
        
        if not all_requests:
            return {
                'total_requests': 0,
                'total_cost': 0,
                'avg_tokens': 0,
                'expensive_model_usage': 0,
                'expensive_model_cost': 0,
                'error_rate': 0,
                'duplicate_ratio': 0,
                'peak_usage_ratio': 0
            }
        
        total_requests = len(all_requests)
        successful_requests = [r for r in all_requests if r.status == RequestStatus.SUCCESS]
        
        # Calculate metrics
        total_cost = sum(r.total_cost for r in successful_requests)
        avg_tokens = np.mean([r.total_tokens or 0 for r in successful_requests]) if successful_requests else 0
        
        # Expensive models (GPT-4, Claude Opus)
        expensive_models = ['gpt-4', 'gpt-4-32k', 'claude-3-opus']
        expensive_requests = [r for r in successful_requests if any(m in r.model_name for m in expensive_models)]
        expensive_model_usage = len(expensive_requests) / len(successful_requests) if successful_requests else 0
        expensive_model_cost = sum(r.total_cost for r in expensive_requests)
        
        # Error rate
        error_rate = (total_requests - len(successful_requests)) / total_requests if total_requests > 0 else 0
        
        # Duplicate detection (simplified - would need more sophisticated hashing)
        duplicate_ratio = 0.1  # Placeholder
        
        # Peak usage (9 AM - 5 PM)
        peak_requests = [r for r in all_requests if 9 <= r.created_at.hour < 17]
        peak_usage_ratio = len(peak_requests) / total_requests if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'total_cost': total_cost,
            'avg_tokens': avg_tokens,
            'expensive_model_usage': expensive_model_usage,
            'expensive_model_cost': expensive_model_cost,
            'error_rate': error_rate,
            'duplicate_ratio': duplicate_ratio,
            'peak_usage_ratio': peak_usage_ratio
        }
