from fastapi import FastAPI, HTTPException
import logging
import time

from metrics import REQUESTS, PROCESSING_TIME

logger = logging.getLogger(__name__)

app = FastAPI(title="Fraud Detection Service")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    start_time = time.time()
    REQUESTS.inc()
    response = {"status": "healthy", "service": "fraud-detection"}
    PROCESSING_TIME.observe(time.time() - start_time)
    return response