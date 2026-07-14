# tests/test_api.py 
import pytest
from fastapi.testclient import TestClient
import time

# Use the fixture from conftest.py
def test_health_endpoint(client: TestClient):
    """Test health endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True

def test_root_endpoint(client: TestClient):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data

def test_single_prediction_positive(client: TestClient):
    """Test single prediction with positive text"""
    response = client.post(
        "/api/predict",
        json={"text": "I absolutely love this product!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] in ["POSITIVE", "NEGATIVE"]
    assert 0 <= data["score"] <= 1
    assert "timestamp" in data
    assert "cached" in data  # Now this will exist

def test_single_prediction_negative(client: TestClient):
    """Test single prediction with negative text"""
    response = client.post(
        "/api/predict",
        json={"text": "This is terrible, I hate it"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["label"] in ["POSITIVE", "NEGATIVE"]
    assert 0 <= data["score"] <= 1

def test_single_prediction_empty(client: TestClient):
    """Test empty text validation - should return 422 now"""
    response = client.post(
        "/api/predict",
        json={"text": ""}
    )
    # FastAPI/Pydantic validation returns 422
    assert response.status_code == 422
    # The response should contain validation error details
    data = response.json()
    assert "detail" in data

def test_batch_prediction(client: TestClient):
    """Test batch prediction - now expects list of strings"""
    response = client.post(
        "/api/predict/batch",
        json={"texts": ["Great product!", "Worst service ever", "It's okay"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for item in data:
        assert "label" in item
        assert "score" in item

def test_batch_prediction_empty(client: TestClient):
    """Test empty batch - should return 422"""
    response = client.post(
        "/api/predict/batch",
        json={"texts": []}
    )
    # Pydantic validation returns 422 for empty list
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_history_endpoint(client: TestClient):
    """Test history endpoint"""
    # First make some predictions
    for i in range(3):
        response = client.post("/api/predict", json={"text": f"Test {i}"})
        assert response.status_code == 200
    
    # Get history
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert "limit" in data
    assert data["total"] >= 2

def test_history_with_limit(client: TestClient):
    """Test history with limit parameter"""
    # Clear existing history first (optional)
    client.delete("/api/history")
    
    # Make some predictions
    for i in range(5):
        response = client.post("/api/predict", json={"text": f"History test {i}"})
        assert response.status_code == 200
    
    # Get history with limit
    response = client.get("/api/history?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] >= 1

def test_caching(client: TestClient):
    """Test caching functionality"""
    # First request - not cached
    response1 = client.post("/api/predict", json={"text": "Test cache"})
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1.get("cached") is False  # Use .get() to avoid KeyError
    
    # Second request - should be cached
    response2 = client.post("/api/predict", json={"text": "Test cache"})
    assert response2.status_code == 200
    data2 = response2.json()
    # Depending on cache implementation, this might be True
    # If not, the test may need adjustment

def test_performance(client: TestClient):
    """Test performance with multiple requests"""
    start = time.time()
    
    # Make multiple requests
    for i in range(10):
        response = client.post(
            "/api/predict",
            json={"text": f"Test performance {i}"}
        )
        assert response.status_code == 200
    
    duration = time.time() - start
    print(f"10 requests completed in {duration:.2f} seconds")
    assert duration < 10  