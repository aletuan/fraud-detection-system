"""
Kafka Integration Module

Provides Kafka integration for handling transaction events and message queues.
Components:
- KafkaConsumer: Base consumer class for handling Kafka messages
- TransactionConsumer: Specialized consumer for transaction events
- KafkaConfig: Configuration class for Kafka settings
"""

from .consumer import KafkaConsumer
from .config import KafkaConfig
from .transaction_consumer import TransactionConsumer

__all__ = [
    'KafkaConsumer',
    'KafkaConfig',
    'TransactionConsumer'
]

# Default Kafka configuration
DEFAULT_BOOTSTRAP_SERVERS = 'kafka:29092'
DEFAULT_GROUP_ID = 'fraud-detection-group'
DEFAULT_TRANSACTION_TOPIC = 'transactions'
DEFAULT_DLQ_TOPIC = 'fraud.detection.dlq' 