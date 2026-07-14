# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.services.sentiment_service import SentimentService
from src.api.routes.predict import set_sentiment_service
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def client():
    """Create test client with initialized service"""
    # Initialize the service
    sentiment_service = SentimentService()
    
    # Set service for routes
    set_sentiment_service(sentiment_service)
    
    # Store service on app for dashboard
    app.sentiment_service = sentiment_service
    
    # Warm up model (synchronous version for tests)
    import asyncio
    asyncio.run(sentiment_service.analyze_single("Warm up request"))
    
    # Return test client
    with TestClient(app) as test_client:
        yield test_client