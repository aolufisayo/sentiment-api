# src/models/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class SentimentLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"

class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="Text to analyze")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Text cannot be empty or whitespace only')
        return v.strip()

class BatchTextRequest(BaseModel):
    # Change this to accept a list of strings directly
    texts: List[str] = Field(..., min_length=1, max_length=32)
    
    @field_validator('texts')
    @classmethod
    def validate_batch(cls, v: List[str]) -> List[str]:
        if len(v) > 32:
            raise ValueError('Batch size cannot exceed 32 items')
        # Validate each text
        for text in v:
            if not text or not text.strip():
                raise ValueError('Text cannot be empty or whitespace only')
        return [t.strip() for t in v]

class SentimentResponse(BaseModel):
    text: str
    label: str
    score: float = Field(..., ge=0, le=1)
    timestamp: datetime
    processing_time_ms: Optional[float] = None
    request_id: Optional[str] = None
    cached: bool = False
    
    class Config:
        # Allow datetime serialization
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    cache_size: int
    cache_hit_rate: float
    timestamp: datetime
    version: str

class HistoryResponse(BaseModel):
    total: int
    items: List[SentimentResponse]
    limit: int
    offset: int

class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime
    request_id: Optional[str] = None