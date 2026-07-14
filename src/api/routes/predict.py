# src/api/routes/predict.py
from fastapi import APIRouter, HTTPException, Depends, Request, status
from typing import List
from loguru import logger
import uuid
import time

from ...models.schemas import TextRequest, BatchTextRequest, SentimentResponse
from ...services.sentiment_service import SentimentService
from ...core.metrics import PREDICTION_COUNT, PREDICTION_LATENCY
from .history import add_to_history

router = APIRouter()

# Global service instance
_sentiment_service = None

def get_sentiment_service() -> SentimentService:
    global _sentiment_service
    if _sentiment_service is None:
        raise RuntimeError("Sentiment service not initialized")
    return _sentiment_service

def set_sentiment_service(service: SentimentService):
    global _sentiment_service
    _sentiment_service = service

@router.post(
    "/predict",
    response_model=SentimentResponse,
    status_code=status.HTTP_200_OK
)
async def predict_single(
    request: Request,
    text_request: TextRequest,
    service: SentimentService = Depends(get_sentiment_service)
):
    """Single text sentiment prediction"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        # Analyze the text
        response = await service.analyze_single(
            text_request.text,
            request_id=request_id
        )
        
        # Save to history
        add_to_history(response.model_dump())
        
        # Update metrics
        PREDICTION_COUNT.labels(label=response.label).inc()
        PREDICTION_LATENCY.observe(time.time() - start_time)
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )

@router.post(
    "/predict/batch",
    response_model=List[SentimentResponse]
)
async def predict_batch(
    request: Request,
    batch_request: BatchTextRequest,
    service: SentimentService = Depends(get_sentiment_service)
):
    """Batch sentiment prediction"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    try:
        # Get texts from the request (now they're strings directly)
        texts = batch_request.texts
        responses = await service.analyze_batch(texts, request_id=request_id)
        
        # Save each response to history
        for response in responses:
            add_to_history(response.model_dump())
            PREDICTION_COUNT.labels(label=response.label).inc()
        
        PREDICTION_LATENCY.observe(time.time() - start_time)
        
        return responses
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )