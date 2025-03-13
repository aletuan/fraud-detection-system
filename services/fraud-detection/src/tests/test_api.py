import pytest
from fastapi.testclient import TestClient
import time

from api import app
from metrics import REQUESTS, PROCESSING_TIME

client = TestClient(app)

def test_health_check():
    """Test health check endpoint returns correct response"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "fraud-detection"
    }

def test_metrics_increment():
    """Test metrics are incremented when endpoint is called"""
    initial_count = REQUESTS.collect()[0].samples[0].value
    response = client.get("/health")
    assert response.status_code == 200
    final_count = REQUESTS.collect()[0].samples[0].value
    assert final_count == initial_count + 1

def test_processing_time_metric():
    """Test processing time metric is recorded"""
    # Get initial sum of all processing times
    initial_sum = sum(sample.value for sample in PROCESSING_TIME.collect()[0].samples 
                     if sample.name == 'fraud_detection_processing_seconds_sum')
    
    response = client.get("/health")
    assert response.status_code == 200
    
    # Get final sum of all processing times
    final_sum = sum(sample.value for sample in PROCESSING_TIME.collect()[0].samples 
                   if sample.name == 'fraud_detection_processing_seconds_sum')
    
    # The final sum should be greater than initial sum
    assert final_sum > initial_sum

def test_not_found():
    """Test 404 response for non-existent endpoint"""
    response = client.get("/nonexistent")
    assert response.status_code == 404 