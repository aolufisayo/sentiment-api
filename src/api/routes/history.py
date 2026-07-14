# src/api/routes/history.py
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime
from loguru import logger

from ...models.schemas import SentimentResponse, HistoryResponse

router = APIRouter()

# In-memory history with better storage
_history = []
MAX_HISTORY = 10000

def add_to_history(response: dict) -> None:
    """Add a prediction response to history"""
    global _history
    _history.append(response)
    # Keep only the last MAX_HISTORY items
    if len(_history) > MAX_HISTORY:
        _history = _history[-MAX_HISTORY:]
    logger.debug(f"History size: {len(_history)}")

def clear_history() -> None:
    """Clear all history"""
    global _history
    _history.clear()
    logger.info("History cleared")

@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get prediction history"
)
async def get_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    label: Optional[str] = Query(None, description="Filter by label (POSITIVE/NEGATIVE)")
):
    """Get prediction history with pagination"""
    try:
        # Filter if label specified
        items = _history
        if label:
            items = [h for h in items if h.get('label') == label.upper()]
        
        # Paginate
        total = len(items)
        items = items[offset:offset + limit]
        
        # Convert to response objects
        responses = [SentimentResponse(**item) for item in items]
        
        return HistoryResponse(
            total=total,
            items=responses,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}"
        )

@router.delete(
    "/history",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear history"
)
async def clear_history_endpoint():
    """Clear all history"""
    clear_history()
    return None