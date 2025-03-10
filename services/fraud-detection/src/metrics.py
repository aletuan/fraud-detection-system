"""
Metrics Module

Provides centralized metrics collection for the fraud detection service.
"""

from prometheus_client import Counter, Histogram

# Request metrics
REQUESTS = Counter('fraud_detection_requests_total', 'Total requests processed')
PROCESSING_TIME = Histogram('fraud_detection_processing_seconds', 'Time spent processing request')

# Transaction metrics
TRANSACTIONS_PROCESSED = Counter('fraud_detection_transactions_processed_total', 'Total transactions processed')
FRAUD_DETECTED = Counter('fraud_detection_fraud_detected_total', 'Total fraudulent transactions detected')
RISK_SCORE = Histogram('fraud_detection_risk_score', 'Risk score distribution') 