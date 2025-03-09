import os
from typing import Dict, Any

# Kafka settings
KAFKA_CONFIG: Dict[str, Any] = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    'group.id': os.getenv('KAFKA_GROUP_ID', 'fraud-detection-group'),
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,
}

# Topics
TRANSACTION_TOPIC = os.getenv('KAFKA_TRANSACTION_TOPIC', 'transactions')
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