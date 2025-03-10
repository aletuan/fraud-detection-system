from fastapi import FastAPI, HTTPException
import logging

from metrics import REQUESTS, PROCESSING_TIME

logger = logging.getLogger(__name__)

app = FastAPI(title="Fraud Detection Service")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fraud-detection"}