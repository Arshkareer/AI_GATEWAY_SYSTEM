from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from app.models.request_log import LLMProvider


class UsageStats(BaseModel):
    """Usage statistics schema."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    avg_latency_ms: float
    
    # Calculated metrics
    success_rate: float = Field(..., ge=0.0, le=100.0)
    avg_cost_per_request: float
    avg_tokens_per_request: float
    cost_per_1k_tokens: float


class ProviderStats(BaseModel):
    """Provider-specific statistics."""
    provider: LLMProvider
    stats: UsageStats
    top_models: List[Dict[str, Any]]
    market_share: float  # Percentage of total requests


class UserStats(BaseModel):
    """User statistics schema."""
    user_id: int
    username: str
    full_name: str
    department: Optional[str]
    stats: UsageStats
    
    # Trends
    daily_usage: List[Dict[str, Any]]
    monthly_budget: float
    budget_utilized: float
    
    # Top usage patterns
    favorite_models: List[str]
    peak_usage_hours: List[int]


class DepartmentStats(BaseModel):
    """Department statistics schema."""
    department_id: int
    department_name: str
    user_count: int
    stats: UsageStats
    
    # Budget information
    monthly_budget: float
    budget_utilization: float
    remaining_budget: float
    is_over_budget: bool
    
    # Top performers
    top_users: List[Dict[str, Any]]
    usage_by_model: List[Dict[str, Any]]


class TimeSeriesData(BaseModel):
    """Time series data point."""
    timestamp: datetime
    value: float
    label: Optional[str] = None


class DashboardMetrics(BaseModel):
    """Main dashboard metrics schema."""
    
    # Overview metrics
    total_requests_today: int
    total_cost_today: float
    avg_latency_today: float
    error_rate_today: float
    
    # Growth metrics (compared to yesterday)
    requests_growth: float
    cost_growth: float
    latency_change: float
    
    # Current active metrics
    active_users_today: int
    requests_last_hour: int
    current_cost_per_hour: float
    
    # Top performers
    top_user_today: Optional[Dict[str, Any]]
    top_department_today: Optional[Dict[str, Any]]
    top_model_today: str
    most_expensive_request_today: float
    
    # Provider breakdown
    provider_stats: List[ProviderStats]
    
    # Time series data (last 24 hours)
    requests_timeline: List[TimeSeriesData]
    cost_timeline: List[TimeSeriesData]
    latency_timeline: List[TimeSeriesData]
    error_timeline: List[TimeSeriesData]


class AnalyticsResponse(BaseModel):
    """General analytics response schema."""
    
    # Metadata
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_records: int
    
    # Aggregated data
    summary: UsageStats
    
    # Breakdowns
    by_user: List[UserStats]
    by_department: List[DepartmentStats]
    by_provider: List[ProviderStats]
    by_model: List[Dict[str, Any]]
    
    # Time-based data
    daily_breakdown: List[Dict[str, Any]]
    hourly_breakdown: List[Dict[str, Any]]
    
    # Insights and recommendations
    insights: List[str]
    cost_optimization_tips: List[str]
    anomalies_detected: List[Dict[str, Any]]


class CostAnalysis(BaseModel):
    """Cost analysis schema."""
    
    # Current period
    current_month_cost: float
    previous_month_cost: float
    cost_change_percent: float
    
    # Projections
    projected_month_end_cost: float
    projected_annual_cost: float
    
    # Breakdown
    cost_by_provider: List[Dict[str, float]]
    cost_by_model: List[Dict[str, float]]
    cost_by_department: List[Dict[str, float]]
    cost_by_user: List[Dict[str, float]]
    
    # Optimization opportunities
    most_expensive_models: List[Dict[str, Any]]
    cost_saving_opportunities: List[str]
    budget_alerts: List[Dict[str, Any]]


class PerformanceMetrics(BaseModel):
    """Performance metrics schema."""
    
    # Latency metrics
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    
    # Throughput metrics
    requests_per_second: float
    tokens_per_second: float
    
    # Reliability metrics
    success_rate: float
    error_rate: float
    timeout_rate: float
    
    # Provider comparison
    provider_performance: List[Dict[str, Any]]
    
    # Trends
    performance_trends: List[TimeSeriesData]


class AlertsResponse(BaseModel):
    """Alerts response schema."""
    
    # Alert counts
    total_alerts: int
    critical_alerts: int
    warning_alerts: int
    info_alerts: int
    
    # Recent alerts
    recent_alerts: List[Dict[str, Any]]
    
    # Alert categories
    cost_alerts: List[Dict[str, Any]]
    performance_alerts: List[Dict[str, Any]]
    security_alerts: List[Dict[str, Any]]
    usage_alerts: List[Dict[str, Any]]


class ExportRequest(BaseModel):
    """Data export request schema."""
    
    # Time range
    start_date: date
    end_date: date
    
    # Filters
    user_ids: Optional[List[int]] = None
    department_ids: Optional[List[int]] = None
    providers: Optional[List[LLMProvider]] = None
    models: Optional[List[str]] = None
    
    # Export options
    format: str = Field("csv", regex="^(csv|json|xlsx)$")
    include_prompts: bool = False
    include_responses: bool = False
    
    # Aggregation level
    aggregate_by: str = Field("request", regex="^(request|hour|day|user|department)$")


class ForecastRequest(BaseModel):
    """Usage forecasting request schema."""
    
    # Forecast parameters
    days_ahead: int = Field(30, ge=1, le=365)
    confidence_interval: float = Field(0.95, ge=0.8, le=0.99)
    
    # Scope
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    provider: Optional[LLMProvider] = None
    model: Optional[str] = None
    
    # Forecast type
    metric: str = Field("cost", regex="^(cost|requests|tokens)$")


class ForecastResponse(BaseModel):
    """Usage forecast response schema."""
    
    # Forecast metadata
    forecast_generated_at: datetime
    forecast_period_days: int
    confidence_interval: float
    model_accuracy: float
    
    # Historical data (last 30 days)
    historical_data: List[TimeSeriesData]
    
    # Forecast data
    forecast_data: List[TimeSeriesData]
    upper_bound: List[TimeSeriesData]
    lower_bound: List[TimeSeriesData]
    
    # Summary predictions
    total_predicted_value: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    seasonality_detected: bool
    
    # Insights
    key_insights: List[str]
    recommendations: List[str]