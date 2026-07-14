# src/api/routes/health.py
from fastapi import APIRouter, Depends, status
from datetime import datetime, timezone
from loguru import logger

from ...models.schemas import HealthResponse
from ...config import settings
from ...services.sentiment_service import SentimentService
from ...api.routes.predict import get_sentiment_service

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check API health status"
)
async def health_check(
    service: SentimentService = Depends(get_sentiment_service)
):
    """Health check endpoint"""
    try:
        stats = service.get_cache_stats()
        
        return HealthResponse(
            status="healthy",
            model_loaded=True,
            cache_size=stats['size'],
            cache_hit_rate=stats['hit_rate'],
            timestamp=datetime.now(timezone.utc),
            version=settings.VERSION
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            model_loaded=False,
            cache_size=0,
            cache_hit_rate=0,
            timestamp=datetime.now(timezone.utc),
            version=settings.VERSION
        )

@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Kubernetes readiness probe"
)
async def readiness():
    """Kubernetes readiness check"""
    return {"status": "ready"}

@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Kubernetes liveness probe"
)
async def liveness():
    """Kubernetes liveness check"""
    return {"status": "alive"}