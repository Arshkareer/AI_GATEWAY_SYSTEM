from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Any
import asyncio
import json

from app.api.deps import get_current_active_user, get_db, rate_limit_gateway
from app.models.user import User
from app.schemas.gateway import (
    GatewayRequest, 
    GatewayResponse, 
    ModelInfo,
    BatchRequest,
    BatchResponse
)
from app.services.gateway_service import GatewayService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize gateway service
gateway_service = GatewayService()


@router.post("/chat", response_model=GatewayResponse)
async def process_chat_request(
    request: GatewayRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _: Any = Depends(rate_limit_gateway)
):
    """Process AI chat request through the gateway."""
    
    try:
        response = await gateway_service.process_request(
            request=request,
            user=current_user,
            db=db,
            stream=False
        )
        return response
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Gateway request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal gateway error"
        )


@router.post("/chat/stream")
async def process_chat_stream(
    request: GatewayRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _: Any = Depends(rate_limit_gateway)
):
    """Process streaming AI chat request through the gateway."""
    
    try:
        async def generate_stream():
            async for chunk in await gateway_service.process_request(
                request=request,
                user=current_user,
                db=db,
                stream=True
            ):
                yield f"data: {json.dumps(chunk.dict())}\n\n"
            
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Gateway streaming failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal gateway error"
        )


@router.post("/batch", response_model=BatchResponse)
async def process_batch_request(
    batch_request: BatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process batch AI requests."""
    
    try:
        # Process requests concurrently
        tasks = []
        for req in batch_request.requests:
            task = gateway_service.process_request(
                request=req,
                user=current_user,
                db=db,
                stream=False
            )
            tasks.append(task)
        
        # Wait for all requests to complete
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate successful responses from errors
        successful_responses = []
        errors = []
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                errors.append({
                    "request_index": i,
                    "error": str(response),
                    "request_id": batch_request.requests[i].request_id
                })
            else:
                successful_responses.append(response)
        
        # Calculate aggregate metrics
        total_tokens = sum(r.total_tokens for r in successful_responses)
        total_cost = sum(r.cost for r in successful_responses)
        total_latency = sum(r.latency_ms for r in successful_responses)
        
        return BatchResponse(
            batch_id=batch_request.batch_id or f"batch_{len(tasks)}",
            total_requests=len(batch_request.requests),
            successful_requests=len(successful_responses),
            failed_requests=len(errors),
            total_tokens=total_tokens,
            total_cost=total_cost,
            total_latency_ms=total_latency,
            responses=successful_responses,
            errors=errors,
            started_at=batch_request.created_at if hasattr(batch_request, 'created_at') else None,
            completed_at=None,  # Would need to track timing
            processing_time_ms=0  # Would need to calculate
        )
    
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch processing failed"
        )


@router.get("/models", response_model=List[ModelInfo])
async def list_available_models(
    current_user: User = Depends(get_current_active_user)
):
    """List available AI models from all providers."""
    
    try:
        models = await gateway_service.get_available_models()
        
        # Convert to ModelInfo format
        model_infos = []
        for model in models:
            model_infos.append(ModelInfo(
                name=model.get("id", "unknown"),
                provider=model.get("provider", "unknown"),
                description=model.get("description", ""),
                max_tokens=model.get("max_tokens", 4096),
                supports_streaming=model.get("supports_streaming", True),
                supports_functions=model.get("supports_functions", False),
                supports_vision=model.get("supports_vision", False),
                input_cost_per_1k=model.get("input_cost_per_1k", 0.0),
                output_cost_per_1k=model.get("output_cost_per_1k", 0.0),
                avg_latency_ms=1200,  # Default estimate
                quality_rating=4.0,   # Default rating
                is_available=True,
                rate_limit_per_minute=60  # Default rate limit
            ))
        
        return model_infos
    
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve models"
        )


@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_active_user)
):
    """List available AI providers and their status."""
    
    try:
        status = await gateway_service.get_provider_status()
        return status
    
    except Exception as e:
        logger.error(f"Failed to get provider status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve provider status"
        )


@router.get("/health")
async def gateway_health():
    """Gateway health check."""
    
    try:
        provider_status = await gateway_service.get_provider_status()
        
        return {
            "status": "healthy" if provider_status["healthy_providers"] > 0 else "degraded",
            "timestamp": provider_status["timestamp"],
            "providers": provider_status["providers"],
            "healthy_providers": provider_status["healthy_providers"],
            "total_providers": provider_status["total_providers"]
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": None
        }


@router.get("/usage/quota")
async def get_user_quota(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's usage quota and limits."""
    
    # Calculate current month usage
    from datetime import datetime
    from sqlalchemy import func, extract
    from app.models.request_log import RequestLog
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_usage = db.query(
        func.sum(RequestLog.total_cost).label("total_cost"),
        func.count(RequestLog.id).label("total_requests"),
        func.sum(RequestLog.total_tokens).label("total_tokens")
    ).filter(
        RequestLog.user_id == current_user.id,
        extract('month', RequestLog.created_at) == current_month,
        extract('year', RequestLog.created_at) == current_year
    ).first()
    
    current_usage = monthly_usage.total_cost or 0.0
    current_requests = monthly_usage.total_requests or 0
    current_tokens = monthly_usage.total_tokens or 0
    
    return {
        "user_id": current_user.id,
        "monthly_budget": current_user.monthly_budget,
        "current_usage": current_usage,
        "remaining_budget": max(0, current_user.monthly_budget - current_usage),
        "requests_this_month": current_requests,
        "tokens_this_month": current_tokens,
        "budget_utilization": (current_usage / current_user.monthly_budget * 100) if current_user.monthly_budget > 0 else 0,
        "quota_reset_date": f"{current_year}-{current_month + 1 if current_month < 12 else current_year + 1}-01T00:00:00Z"
    }


@router.get("/stats")
async def get_gateway_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get gateway usage statistics."""
    
    from sqlalchemy import func, desc
    from app.models.request_log import RequestLog
    
    # Get recent requests
    recent_requests = db.query(RequestLog).filter(
        RequestLog.user_id == current_user.id
    ).order_by(desc(RequestLog.created_at)).limit(10).all()
    
    # Get usage by provider
    provider_usage = db.query(
        RequestLog.provider,
        func.count(RequestLog.id).label("count"),
        func.sum(RequestLog.total_cost).label("cost")
    ).filter(
        RequestLog.user_id == current_user.id
    ).group_by(RequestLog.provider).all()
    
    return {
        "recent_requests": [
            {
                "request_id": req.request_id,
                "provider": req.provider,
                "model": req.model_name,
                "cost": req.total_cost,
                "tokens": req.total_tokens,
                "latency_ms": req.latency_ms,
                "status": req.status,
                "created_at": req.created_at.isoformat()
            }
            for req in recent_requests
        ],
        "provider_usage": [
            {
                "provider": usage.provider,
                "requests": usage.count,
                "cost": usage.cost
            }
            for usage in provider_usage
        ]
    }