"""AI Insights API Endpoints

Endpoints for AI-powered features:
- Anomaly detection
- Cost predictions
- Quality analysis
- Smart routing
- Safety monitoring
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.ai_services.anomaly_detector import AnomalyDetector
from app.ai_services.cost_predictor import CostPredictor
from app.ai_services.quality_scorer import QualityScorer
from app.ai_services.routing_engine import SmartRoutingEngine, RoutingStrategy
from app.ai_services.safety_monitor import SafetyMonitor


router = APIRouter()

# Initialize AI services
anomaly_detector = AnomalyDetector()
cost_predictor = CostPredictor()
quality_scorer = QualityScorer()
routing_engine = SmartRoutingEngine()
safety_monitor = SafetyMonitor()


# ==================== Anomaly Detection ====================

@router.get("/anomalies")
async def get_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detect anomalies in AI gateway usage.
    
    Returns:
        List of detected anomalies with severity and details
    """
    try:
        anomalies = anomaly_detector.detect_all_anomalies(db)
        
        return {
            "anomalies": [a.to_dict() for a in anomalies],
            "total_count": len(anomalies),
            "critical_count": sum(1 for a in anomalies if a.severity.value == "critical"),
            "high_count": sum(1 for a in anomalies if a.severity.value == "high")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/user/{user_id}")
async def get_user_anomaly_score(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get anomaly score for a specific user.
    
    Args:
        user_id: User ID to analyze
    
    Returns:
        User anomaly analysis
    """
    # Check permissions (admins can view any user, users can view themselves)
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user's data")
    
    try:
        result = anomaly_detector.get_user_anomaly_score(db, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Cost Prediction ====================

@router.get("/cost-prediction")
async def predict_costs(
    days_ahead: int = Query(30, ge=1, le=90, description="Number of days to predict"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Predict future costs based on historical data.
    
    Args:
        days_ahead: Number of days to predict (1-90)
        user_id: Optional user filter
        department_id: Optional department filter
    
    Returns:
        Cost predictions and trends
    """
    # Check permissions
    if user_id and not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        predictions = cost_predictor.predict_costs(
            db,
            days_ahead=days_ahead,
            user_id=user_id,
            department_id=department_id
        )
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-prediction/monthly")
async def predict_monthly_cost(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Predict cost for the remainder of the current month.
    
    Args:
        user_id: Optional user filter
        department_id: Optional department filter
    
    Returns:
        Monthly cost prediction
    """
    # Check permissions
    if user_id and not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        prediction = cost_predictor.predict_monthly_cost(
            db,
            user_id=user_id,
            department_id=department_id
        )
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-optimization")
async def get_cost_optimization(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get cost optimization recommendations.
    
    Args:
        user_id: Optional user filter
        department_id: Optional department filter
    
    Returns:
        Optimization recommendations and potential savings
    """
    # Check permissions
    if user_id and not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        optimization = cost_predictor.optimize_costs(
            db,
            user_id=user_id,
            department_id=department_id
        )
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Quality Analysis ====================

@router.get("/quality/model-analysis")
async def analyze_model_quality(
    model_name: Optional[str] = Query(None, description="Specific model to analyze"),
    days: int = Query(7, ge=1, le=30, description="Days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze quality metrics for models.
    
    Args:
        model_name: Optional model filter
        days: Number of days to analyze (1-30)
    
    Returns:
        Quality analysis by model
    """
    try:
        analysis = quality_scorer.analyze_model_quality(
            db,
            model_name=model_name,
            days=days
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/compare-models")
async def compare_models(
    model_a: str = Query(..., description="First model to compare"),
    model_b: str = Query(..., description="Second model to compare"),
    days: int = Query(7, ge=1, le=30, description="Days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare quality metrics between two models.
    
    Args:
        model_a: First model
        model_b: Second model
        days: Number of days to analyze
    
    Returns:
        Comparison results with recommendation
    """
    try:
        comparison = quality_scorer.compare_models(
            db,
            model_a=model_a,
            model_b=model_b,
            days=days
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/trends")
async def get_quality_trends(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    days: int = Query(30, ge=7, le=90, description="Days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get quality trends over time.
    
    Args:
        user_id: Optional user filter
        department_id: Optional department filter
        days: Number of days to analyze
    
    Returns:
        Quality trends
    """
    # Check permissions
    if user_id and not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        trends = quality_scorer.get_quality_trends(
            db,
            user_id=user_id,
            department_id=department_id,
            days=days
        )
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Smart Routing ====================

@router.post("/routing/recommend")
async def get_routing_recommendation(
    prompt: str = Query(..., description="User prompt to route"),
    strategy: RoutingStrategy = Query(RoutingStrategy.BALANCED, description="Routing strategy"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get smart routing recommendation for a request.
    
    Args:
        prompt: User's input prompt
        strategy: Routing strategy (cost_optimized, speed_optimized, quality_optimized, balanced)
    
    Returns:
        Routing decision with recommended model
    """
    try:
        decision = routing_engine.route_request(
            db,
            prompt=prompt,
            strategy=strategy
        )
        return decision.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/optimize-budget")
async def optimize_for_budget(
    monthly_budget: float = Query(..., description="Monthly budget in USD"),
    expected_requests: int = Query(..., description="Expected requests per month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get routing optimization to stay within budget.
    
    Args:
        monthly_budget: Monthly budget in USD
        expected_requests: Expected number of requests per month
    
    Returns:
        Budget optimization recommendations
    """
    if monthly_budget <= 0 or expected_requests <= 0:
        raise HTTPException(status_code=400, detail="Budget and requests must be positive")
    
    try:
        optimization = routing_engine.optimize_for_budget(
            db,
            monthly_budget=monthly_budget,
            expected_requests=expected_requests
        )
        return optimization
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/ab-test")
async def ab_test_models(
    model_a: str = Query(..., description="First model to test"),
    model_b: str = Query(..., description="Second model to test"),
    days: int = Query(7, ge=1, le=30, description="Days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare performance of two models for A/B testing.
    
    Args:
        model_a: First model
        model_b: Second model
        days: Number of days to analyze
    
    Returns:
        A/B test results
    """
    try:
        results = routing_engine.a_b_test_models(
            db,
            model_a=model_a,
            model_b=model_b,
            days=days
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Safety Monitoring ====================

@router.post("/safety/check")
async def check_safety(
    prompt: str = Query(..., description="Prompt to check"),
    response: Optional[str] = Query(None, description="Response to check"),
    redact_pii: bool = Query(True, description="Whether to redact PII"),
    current_user: User = Depends(get_current_user)
):
    """
    Perform safety check on content.
    
    Args:
        prompt: User's prompt
        response: AI's response (optional)
        redact_pii: Whether to redact detected PII
    
    Returns:
        Safety report with findings
    """
    try:
        report = safety_monitor.check_safety(
            prompt=prompt,
            response=response,
            redact_pii=redact_pii
        )
        return report.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/safety/detect-pii")
async def detect_pii(
    text: str = Query(..., description="Text to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Detect PII in text.
    
    Args:
        text: Text to analyze
    
    Returns:
        List of detected PII items
    """
    try:
        pii_items = safety_monitor.detect_pii(text)
        return {
            "pii_detected": pii_items,
            "count": len(pii_items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/safety/check-compliance")
async def check_compliance(
    prompt: str = Query(..., description="Prompt to check"),
    response: str = Query(..., description="Response to check"),
    current_user: User = Depends(get_current_user)
):
    """
    Check compliance with organizational rules.
    
    Args:
        prompt: User's prompt
        response: AI's response
    
    Returns:
        Compliance report
    """
    try:
        report = safety_monitor.check_compliance(
            prompt=prompt,
            response=response
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Dashboard Summary ====================

@router.get("/insights-summary")
async def get_insights_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary of all AI insights for dashboard.
    
    Returns:
        Summary of anomalies, predictions, and recommendations
    """
    try:
        # Get recent anomalies
        anomalies = anomaly_detector.detect_all_anomalies(db)
        critical_anomalies = [a for a in anomalies if a.severity.value in ["critical", "high"]]
        
        # Get monthly cost prediction
        monthly_prediction = cost_predictor.predict_monthly_cost(db)
        
        # Get cost optimization
        optimization = cost_predictor.optimize_costs(db)
        
        return {
            "anomalies": {
                "total": len(anomalies),
                "critical": len(critical_anomalies),
                "recent": [a.to_dict() for a in critical_anomalies[:5]]
            },
            "cost_prediction": monthly_prediction if "error" not in monthly_prediction else None,
            "cost_optimization": {
                "potential_savings": optimization.get("potential_monthly_savings", 0),
                "top_recommendations": [
                    r for r in optimization.get("recommendations", [])[:3]
                ]
            },
            "generated_at": anomalies[0].detected_at.isoformat() if anomalies else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
