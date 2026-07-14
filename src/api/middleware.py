# src/api/middleware.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from loguru import logger
from typing import Dict, Any
from ..config import settings

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "unknown")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Add processing time header
            processing_time = time.time() - start_time
            response.headers["X-Processing-Time"] = f"{processing_time:.4f}s"
            response.headers["X-Request-ID"] = request_id
            
            # Log request
            logger.info(
                f"{request.method} {request.url.path} "
                f"→ {response.status_code} ({processing_time:.3f}s)"
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"{request.method} {request.url.path} "
                f"→ ERROR: {str(e)} ({processing_time:.3f}s)",
                exc_info=True
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(e) if settings.DEBUG else "An unexpected error occurred",
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting (use Redis for production)"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests = {}  # In-memory only for demo
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        
        # Rate limiting logic
        if client_ip in self.client_requests:
            self.client_requests[client_ip] += 1
        else:
            self.client_requests[client_ip] = 1
        
        # Check rate limit
        if self.client_requests[client_ip] > self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit of {self.requests_per_minute} per minute exceeded"
                }
            )
        
        response = await call_next(request)
        
        # Clean up old entries periodically
        if len(self.client_requests) > 10000:
            self.client_requests.clear()
        
        return response