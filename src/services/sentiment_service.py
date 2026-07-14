# src/services/sentiment_service.py
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
import time
import hashlib
import asyncio
from collections import OrderedDict
from loguru import logger

from ..models.schemas import SentimentResponse
from ..models.sentiment import SentimentModel
from ..config import settings

class SentimentService:
    def __init__(self):
        self.model = SentimentModel()
        self.cache: OrderedDict = OrderedDict()
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        
        # Try Redis if configured
        self.redis_client = None
        if settings.USE_REDIS_CACHE and settings.REDIS_URL:
            try:
                import redis
                self.redis_client = redis.from_url(settings.REDIS_URL)
                logger.info("✅ Redis cache enabled")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
        
        logger.info("✅ SentimentService initialized")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    async def analyze_single(
        self, 
        text: str, 
        request_id: Optional[str] = None
    ) -> SentimentResponse:
        """Analyze single text with caching"""
        start_time = time.time()
        cached = False
        
        # Check Redis cache first
        cache_key = self._get_cache_key(text)
        
        if self.redis_client:
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                import json
                result = json.loads(cached_result)
                cached = True
                logger.debug(f"✅ Redis cache hit for: {text[:50]}...")
                return self._create_response(text, result, start_time, request_id, cached)
        
        # Check local cache
        if cache_key in self.cache:
            result = self.cache[cache_key]
            cached = True
            self.cache_hits += 1
            logger.debug(f"✅ Local cache hit for: {text[:50]}...")
            return self._create_response(text, result, start_time, request_id, cached)
        
        self.cache_misses += 1
        self.total_requests += 1
        
        # Run prediction
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.model.predict, text
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            logger.info(f"🔮 Prediction: {result['label']} ({result['score']:.3f})")
            
            return self._create_response(text, result, start_time, request_id, cached)
            
        except Exception as e:
            logger.error(f"❌ Prediction failed: {str(e)}")
            raise
    
    def _create_response(self, text: str, result: dict, start_time: float, 
                         request_id: Optional[str], cached: bool) -> SentimentResponse:
        """Create response object"""
        return SentimentResponse(
            text=text,
            label=result['label'],
            score=round(float(result['score']), 4),
            timestamp=datetime.now(timezone.utc),
            processing_time_ms=(time.time() - start_time) * 1000,
            request_id=request_id,
            cached=cached
        )
    
    def _cache_result(self, key: str, result: dict):
        """Cache result with LRU eviction"""
        # Store in local cache
        if len(self.cache) >= settings.CACHE_SIZE:
            # Remove oldest
            self.cache.popitem(last=False)
        self.cache[key] = result
        
        # Store in Redis if available
        if self.redis_client:
            import json
            self.redis_client.setex(
                key,
                settings.CACHE_TTL,
                json.dumps(result)
            )
    
    async def analyze_batch(
        self, 
        texts: List[str], 
        request_id: Optional[str] = None
    ) -> List[SentimentResponse]:
        """Analyze multiple texts efficiently"""
        tasks = [self.analyze_single(text, request_id) for text in texts]
        return await asyncio.gather(*tasks)
    
    def get_cache_stats(self) -> Dict:
        """Return cache performance metrics"""
        total = self.cache_hits + self.cache_misses
        return {
            'size': len(self.cache),
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'total_requests': self.total_requests,
            'hit_rate': self.cache_hits / total if total > 0 else 0
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self.cache.clear()
        if self.redis_client:
            self.redis_client.flushdb()
        self.cache_hits = 0
        self.cache_misses = 0
        logger.info("🧹 Cache cleared")