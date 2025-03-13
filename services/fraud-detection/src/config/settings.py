import os
from typing import Dict, Any

# Kafka settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
KAFKA_CONSUMER_GROUP = os.getenv('KAFKA_CONSUMER_GROUP', 'fraud-detection-group')
TRANSACTION_TOPIC = os.getenv('TRANSACTION_TOPIC', 'transactions')
SECURITY_ALERT_TOPIC = os.getenv('SECURITY_ALERT_TOPIC', 'security.alerts')

# Topics
FRAUD_ALERT_TOPIC = os.getenv('KAFKA_FRAUD_ALERT_TOPIC', 'fraud-alerts')

# Rule Engine settings
AMOUNT_THRESHOLD = float(os.getenv('AMOUNT_THRESHOLD', '10000.0'))
FREQUENCY_WINDOW_MINUTES = int(os.getenv('FREQUENCY_WINDOW_MINUTES', '60'))
MAX_TRANSACTIONS_PER_WINDOW = int(os.getenv('MAX_TRANSACTIONS_PER_WINDOW', '10'))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Metrics
METRICS_PORT = int(os.getenv('METRICS_PORT', '8000'))

# Service Settings
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8000))
SERVICE_HOST = os.getenv('SERVICE_HOST', '0.0.0.0') 