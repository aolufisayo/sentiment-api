# src/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI

# Application info
APP_INFO = Info('sentiment_api', 'Sentiment API information')

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)

# Prediction metrics
PREDICTION_COUNT = Counter(
    'predictions_total',
    'Total predictions',
    ['label']
)

PREDICTION_LATENCY = Histogram(
    'prediction_duration_seconds',
    'Model prediction latency',
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5)
)

# Cache metrics
CACHE_SIZE = Gauge(
    'cache_size',
    'Number of items in cache'
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate'
)

# Model metrics
MODEL_LOADED = Gauge(
    'model_loaded',
    'Whether model is successfully loaded'
)

MODEL_LOAD_TIME = Gauge(
    'model_load_seconds',
    'Time to load model'
)

# System metrics
ACTIVE_REQUESTS = Gauge(
    'active_requests',
    'Number of active requests'
)

def setup_metrics(app: FastAPI):
    """Setup Prometheus metrics for FastAPI"""
    
    # Create instrumentator
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics"],
        env_var_name="ENABLE_METRICS"
    )
    
    # Instrument app
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    
    # Add custom metrics middleware
    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        ACTIVE_REQUESTS.inc()
        response = await call_next(request)
        ACTIVE_REQUESTS.dec()
        return response
    
    # Update cache hit rate periodically
    from ..services.sentiment_service import SentimentService
    
    return instrumentator