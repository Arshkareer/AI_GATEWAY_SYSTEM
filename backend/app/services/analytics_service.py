from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract

from app.models.user import User
from app.models.department import Department
from app.models.request_log import RequestLog, RequestStatus, LLMProvider
from app.models.analytics import Analytics, DailyAnalytics


class AnalyticsService:
    """Analytics service for processing and aggregating usage data."""
    
    def __init__(self):
        pass
    
    def get_dashboard_metrics(self, db: Session, user: User) -> Dict[str, Any]:
        """Get main dashboard metrics for user."""
        
        # Get today's metrics
        today = datetime.now().date()
        
        # Base query for user's requests
        base_query = db.query(RequestLog).filter(RequestLog.user_id == user.id)
        
        # Today's metrics
        today_requests = base_query.filter(
            func.date(RequestLog.created_at) == today
        )
        
        total_requests_today = today_requests.count()
        total_cost_today = today_requests.filter(
            RequestLog.status == RequestStatus.SUCCESS
        ).with_entities(func.sum(RequestLog.total_cost)).scalar() or 0.0
        
        avg_latency_today = today_requests.filter(
            RequestLog.status == RequestStatus.SUCCESS
        ).with_entities(func.avg(RequestLog.latency_ms)).scalar() or 0.0
        
        error_count_today = today_requests.filter(
            RequestLog.status != RequestStatus.SUCCESS
        ).count()
        
        error_rate_today = (error_count_today / total_requests_today * 100) if total_requests_today > 0 else 0.0
        
        # Yesterday's metrics for comparison
        yesterday = today - timedelta(days=1)
        yesterday_requests = base_query.filter(
            func.date(RequestLog.created_at) == yesterday
        )
        
        total_requests_yesterday = yesterday_requests.count()
        total_cost_yesterday = yesterday_requests.filter(
            RequestLog.status == RequestStatus.SUCCESS
        ).with_entities(func.sum(RequestLog.total_cost)).scalar() or 0.0
        
        # Calculate growth
        requests_growth = self._calculate_growth(total_requests_yesterday, total_requests_today)
        cost_growth = self._calculate_growth(total_cost_yesterday, total_cost_today)
        
        return {
            "total_requests_today": total_requests_today,
            "total_cost_today": round(total_cost_today, 4),
            "avg_latency_today": round(avg_latency_today, 2),
            "error_rate_today": round(error_rate_today, 2),
            "requests_growth": round(requests_growth, 2),
            "cost_growth": round(cost_growth, 2),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def get_user_analytics(
        self, 
        db: Session, 
        user_id: int, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get detailed analytics for a specific user."""
        
        # Set default date range (last 30 days)
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Base query
        query = db.query(RequestLog).filter(
            RequestLog.user_id == user_id,
            RequestLog.created_at.between(start_date, end_date)
        )
        
        # Aggregate metrics
        total_requests = query.count()
        successful_requests = query.filter(RequestLog.status == RequestStatus.SUCCESS).count()
        failed_requests = total_requests - successful_requests
        
        cost_sum = query.filter(RequestLog.status == RequestStatus.SUCCESS)\
            .with_entities(func.sum(RequestLog.total_cost)).scalar() or 0.0
        
        tokens_sum = query.filter(RequestLog.status == RequestStatus.SUCCESS)\
            .with_entities(func.sum(RequestLog.total_tokens)).scalar() or 0
        
        avg_latency = query.filter(RequestLog.status == RequestStatus.SUCCESS)\
            .with_entities(func.avg(RequestLog.latency_ms)).scalar() or 0.0
        
        # Most used models and providers
        model_usage = query.with_entities(
            RequestLog.model_name,
            func.count(RequestLog.id).label('count')
        ).group_by(RequestLog.model_name).order_by(desc('count')).limit(5).all()
        
        provider_usage = query.with_entities(
            RequestLog.provider,
            func.count(RequestLog.id).label('count')
        ).group_by(RequestLog.provider).order_by(desc('count')).limit(5).all()
        
        return {
            "user_id": user_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": round((successful_requests / total_requests * 100) if total_requests > 0 else 0, 2),
                "total_cost": round(cost_sum, 4),
                "total_tokens": tokens_sum,
                "avg_latency_ms": round(avg_latency, 2)
            },
            "top_models": [{"model": m.model_name, "count": m.count} for m in model_usage],
            "top_providers": [{"provider": p.provider.value, "count": p.count} for p in provider_usage]
        }
    
    def get_department_analytics(
        self, 
        db: Session, 
        department_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics for a specific department."""
        
        # Set default date range
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get department
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise ValueError(f"Department {department_id} not found")
        
        # Base query
        query = db.query(RequestLog).filter(
            RequestLog.department_id == department_id,
            RequestLog.created_at.between(start_date, end_date)
        )
        
        # Aggregate metrics
        total_requests = query.count()
        successful_requests = query.filter(RequestLog.status == RequestStatus.SUCCESS).count()
        
        cost_sum = query.filter(RequestLog.status == RequestStatus.SUCCESS)\
            .with_entities(func.sum(RequestLog.total_cost)).scalar() or 0.0
        
        # Top users in department
        top_users = query.join(User).with_entities(
            User.username,
            User.full_name,
            func.count(RequestLog.id).label('request_count'),
            func.sum(RequestLog.total_cost).label('total_cost')
        ).group_by(User.id, User.username, User.full_name)\
         .order_by(desc('request_count')).limit(10).all()
        
        return {
            "department_id": department_id,
            "department_name": department.name,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "total_cost": round(cost_sum, 4),
                "user_count": len(top_users)
            },
            "budget_info": {
                "monthly_budget": department.monthly_budget,
                "current_usage": round(cost_sum, 4),
                "budget_utilization": round(department.budget_utilization, 2),
                "remaining_budget": round(department.remaining_budget, 4)
            },
            "top_users": [
                {
                    "username": user.username,
                    "full_name": user.full_name,
                    "requests": user.request_count,
                    "cost": round(user.total_cost or 0, 4)
                }
                for user in top_users
            ]
        }
    
    def get_cost_analysis(
        self,
        db: Session,
        user: Optional[User] = None,
        department_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get detailed cost analysis."""
        
        # Set default date range (current month)
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date.replace(day=1)  # First day of current month
        
        # Build base query
        query = db.query(RequestLog).filter(
            RequestLog.status == RequestStatus.SUCCESS,
            RequestLog.created_at.between(start_date, end_date)
        )
        
        # Apply filters
        if user:
            query = query.filter(RequestLog.user_id == user.id)
        if department_id:
            query = query.filter(RequestLog.department_id == department_id)
        
        # Current period cost
        current_cost = query.with_entities(func.sum(RequestLog.total_cost)).scalar() or 0.0
        
        # Previous period for comparison
        period_length = end_date - start_date
        prev_start = start_date - period_length
        prev_end = start_date
        
        prev_query = db.query(RequestLog).filter(
            RequestLog.status == RequestStatus.SUCCESS,
            RequestLog.created_at.between(prev_start, prev_end)
        )
        
        if user:
            prev_query = prev_query.filter(RequestLog.user_id == user.id)
        if department_id:
            prev_query = prev_query.filter(RequestLog.department_id == department_id)
        
        prev_cost = prev_query.with_entities(func.sum(RequestLog.total_cost)).scalar() or 0.0
        
        # Cost by provider
        provider_costs = query.with_entities(
            RequestLog.provider,
            func.sum(RequestLog.total_cost).label('cost')
        ).group_by(RequestLog.provider).all()
        
        # Cost by model
        model_costs = query.with_entities(
            RequestLog.model_name,
            func.sum(RequestLog.total_cost).label('cost')
        ).group_by(RequestLog.model_name).order_by(desc('cost')).limit(10).all()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "current_period_cost": round(current_cost, 4),
            "previous_period_cost": round(prev_cost, 4),
            "cost_change_percent": round(self._calculate_growth(prev_cost, current_cost), 2),
            "cost_by_provider": [
                {"provider": cost.provider.value, "cost": round(cost.cost, 4)}
                for cost in provider_costs
            ],
            "cost_by_model": [
                {"model": cost.model_name, "cost": round(cost.cost, 4)}
                for cost in model_costs
            ]
        }
    
    def get_performance_metrics(
        self,
        db: Session,
        user: Optional[User] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics."""
        
        # Base query for successful requests in last 24 hours
        yesterday = datetime.now() - timedelta(hours=24)
        query = db.query(RequestLog).filter(
            RequestLog.status == RequestStatus.SUCCESS,
            RequestLog.created_at >= yesterday
        )
        
        # Apply filters
        if user:
            query = query.filter(RequestLog.user_id == user.id)
        if provider:
            query = query.filter(RequestLog.provider == LLMProvider(provider))
        if model:
            query = query.filter(RequestLog.model_name == model)
        
        # Calculate metrics
        latencies = [r.latency_ms for r in query.all()]
        
        if not latencies:
            return {
                "message": "No data available for the specified filters",
                "period_hours": 24
            }
        
        latencies.sort()
        n = len(latencies)
        
        return {
            "period_hours": 24,
            "total_requests": n,
            "avg_latency_ms": round(sum(latencies) / n, 2),
            "p50_latency_ms": latencies[n // 2],
            "p95_latency_ms": latencies[int(n * 0.95)],
            "p99_latency_ms": latencies[int(n * 0.99)],
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies)
        }
    
    def _calculate_growth(self, old_value: float, new_value: float) -> float:
        """Calculate percentage growth between two values."""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        return ((new_value - old_value) / old_value) * 100
    
    def create_daily_analytics(self, db: Session, date: datetime.date) -> DailyAnalytics:
        """Create daily analytics summary for a specific date."""
        
        # Query all requests for the date
        requests = db.query(RequestLog).filter(
            func.date(RequestLog.created_at) == date
        ).all()
        
        if not requests:
            return None
        
        # Calculate metrics
        total_requests = len(requests)
        successful_requests = sum(1 for r in requests if r.status == RequestStatus.SUCCESS)
        total_cost = sum(r.total_cost for r in requests if r.status == RequestStatus.SUCCESS)
        total_tokens = sum(r.total_tokens for r in requests if r.status == RequestStatus.SUCCESS)
        
        # Get unique users and departments
        unique_users = len(set(r.user_id for r in requests))
        unique_departments = len(set(r.department_id for r in requests if r.department_id))
        
        # Create daily analytics record
        daily_analytics = DailyAnalytics(
            date=date,
            total_requests=total_requests,
            total_users=unique_users,
            total_departments=unique_departments,
            total_cost=total_cost,
            total_tokens=total_tokens,
            avg_latency_ms=sum(r.latency_ms for r in requests if r.latency_ms) / len(requests),
            error_rate=(total_requests - successful_requests) / total_requests * 100 if total_requests > 0 else 0
        )
        
        db.add(daily_analytics)
        db.commit()
        db.refresh(daily_analytics)
        
        return daily_analytics