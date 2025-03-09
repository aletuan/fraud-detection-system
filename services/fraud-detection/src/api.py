from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram
import logging

logger = logging.getLogger(__name__)

# Metrics
REQUESTS = Counter('fraud_detection_requests_total', 'Total requests processed')
PROCESSING_TIME = Histogram('fraud_detection_processing_seconds', 'Time spent processing request')

app = FastAPI(title="Fraud Detection Service")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fraud-detection"}