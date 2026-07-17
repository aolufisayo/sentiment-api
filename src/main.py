# src/main.py - FIXED VERSION
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.config import settings
from src.core.logging import setup_logging
from src.core.metrics import setup_metrics, CACHE_SIZE, MODEL_LOADED
from src.services.sentiment_service import SentimentService
from src.api.routes import predict, history, health
from src.api.middleware import ErrorHandlingMiddleware
from src.api.routes.predict import set_sentiment_service

# Setup logging
logger = setup_logging()

# Global service instance
sentiment_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global sentiment_service
    
    logger.info("🚀 Starting application...")
    
    # Initialize service
    sentiment_service = SentimentService()
    
    # Set service for routes
    set_sentiment_service(sentiment_service)
    
    # Set service for dashboard (if created after)
    if hasattr(app, 'sentiment_service'):
        app.sentiment_service = sentiment_service
    
    MODEL_LOADED.set(1)
    
    # Warm up model
    await sentiment_service.analyze_single("Warm up request")
    logger.info("✅ Model warmed up successfully")
    
    # Background task for cache metrics
    async def update_cache_metrics():
        while True:
            if sentiment_service:
                stats = sentiment_service.get_cache_stats()
                CACHE_SIZE.set(stats['size'])
                logger.debug(f"Cache stats: {stats}")
            await asyncio.sleep(60)
    
    task = asyncio.create_task(update_cache_metrics())
    
    yield
    
    # Cleanup
    task.cancel()
    logger.info("🛑 Shutting down application...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-grade sentiment analysis API with caching and monitoring",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Store service reference on app
app.sentiment_service = None

# Add middlewares
app.add_middleware(ErrorHandlingMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup metrics
try:
    logger.info("📊 Setting up Prometheus metrics...")
    setup_metrics(app)
    logger.info("✅ Metrics setup completed")
except Exception as e:
    logger.warning(f"⚠️ Metrics setup failed: {e}")

@app.get("/metrics")
async def metrics_endpoint():
    """Direct Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to see all registered routes"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, 'methods') else []
        })
    return {"routes": routes}

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(predict.router, prefix="/api", tags=["Prediction"])
app.include_router(history.router, prefix="/api", tags=["History"])

# Include Gradio dashboard
try:
    import gradio as gr
    from src.dashboard import create_dashboard
    
    # Create dashboard with service getter function
    def get_service():
        return sentiment_service
    
    dashboard = create_dashboard(get_service)
    app = gr.mount_gradio_app(app, dashboard, path="/dashboard")
    logger.info("📊 Dashboard mounted at /dashboard")
except Exception as e:
    logger.warning(f"Dashboard not available: {e}")

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/api/docs" if settings.DEBUG else "Not available in production"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG
    )