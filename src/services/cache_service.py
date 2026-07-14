# src/services/cache_service.py
import json
import redis
from typing import Optional, Any
from loguru import logger
from ..config import settings

class CacheService:
    """Redis cache service wrapper"""
    
    def __init__(self):
        self.client = None
        self.enabled = False
        
        if settings.USE_REDIS_CACHE and settings.REDIS_URL:
            try:
                self.client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                self.client.ping()
                self.enabled = True
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        if not self.enabled:
            return
        
        try:
            ttl = ttl or settings.CACHE_TTL
            self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    def delete(self, key: str):
        """Delete from cache"""
        if not self.enabled:
            return
        
        try:
            self.client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete failed: {e}")
    
    def clear(self):
        """Clear all cache"""
        if not self.enabled:
            return
        
        try:
            self.client.flushdb()
            logger.info("🧹 Redis cache cleared")
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")