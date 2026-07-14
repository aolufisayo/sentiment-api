# src/utils/validators.py
import re
from typing import Optional
from loguru import logger

def validate_text_length(text: str, min_length: int = 1, max_length: int = 500) -> bool:
    """Validate text length constraints"""
    if not text:
        return False
    
    length = len(text.strip())
    if length < min_length:
        logger.warning(f"Text too short: {length} chars")
        return False
    
    if length > max_length:
        logger.warning(f"Text too long: {length} chars")
        return False
    
    return True

def sanitize_text(text: str) -> str:
    """Sanitize input text"""
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    
    # Truncate if too long
    if len(text) > 500:
        text = text[:497] + "..."
    
    return text

def validate_batch_size(size: int, max_size: int = 32) -> bool:
    """Validate batch size"""
    if size < 1:
        logger.warning(f"Batch size too small: {size}")
        return False
    
    if size > max_size:
        logger.warning(f"Batch size too large: {size} (max: {max_size})")
        return False
    
    return True

def extract_request_id(headers: dict) -> str:
    """Extract or generate request ID"""
    request_id = headers.get("X-Request-ID")
    if not request_id:
        import uuid
        request_id = str(uuid.uuid4())[:8]
    return request_id