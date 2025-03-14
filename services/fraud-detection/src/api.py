from fastapi import FastAPI, HTTPException, Request
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware

from metrics import REQUESTS, PROCESSING_TIME

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            duration = time.time() - start_time
            # Log the request
            logger.info(
                f"Request processed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration": f"{duration:.6f}s",
                    "client_host": request.client.host if request.client else None,
                }
            )
            
        return response

app = FastAPI(title="Fraud Detection Service")
app.add_middleware(LoggingMiddleware)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    start_time = time.time()
    REQUESTS.inc()
    response = {"status": "healthy", "service": "fraud-detection"}
    PROCESSING_TIME.observe(time.time() - start_time)
    return response