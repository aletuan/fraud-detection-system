import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .consumer import KafkaConsumer
from .config import KafkaConfig
from core.models import Transaction
from detection.engine import FraudDetectionEngine
from config import settings

logger = logging.getLogger(__name__)

class TransactionConsumer:
    def __init__(
        self,
        kafka_config: Optional[KafkaConfig] = None,
        detection_engine: Optional[FraudDetectionEngine] = None,
        dead_letter_topic: Optional[str] = "fraud.detection.dlq"
    ):
        """Initialize Transaction Consumer
        
        Args:
            kafka_config: Kafka configuration, uses settings if not provided
            detection_engine: Fraud detection engine instance
            dead_letter_topic: Topic for failed messages
        """
        self.detection_engine = detection_engine or FraudDetectionEngine()
        
        if kafka_config is None:
            kafka_config = KafkaConfig(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                topics=[settings.TRANSACTION_TOPIC]
            )
            
        self.consumer = KafkaConsumer(
            config=kafka_config,
            message_handler=self._handle_transaction,
            error_handler=self._handle_error,
            dead_letter_topic=dead_letter_topic
        )
        
    def start(self):
        """Start consuming transaction events"""
        logger.info("Starting transaction consumer...")
        self.consumer.start()
        
    def stop(self):
        """Stop consuming transaction events"""
        logger.info("Stopping transaction consumer...")
        self.consumer.stop()
        
    def _handle_transaction(self, message: Dict[str, Any]):
        """Handle transaction event
        
        Args:
            message: Transaction event message
        """
        try:
            # Extract transaction data from event wrapper
            event_data = json.loads(message) if isinstance(message, str) else message
            transaction_data = event_data.get('transaction', {})
            
            # Convert message to Transaction model
            transaction = Transaction(
                id=transaction_data.get('id'),
                amount=transaction_data.get('amount'),
                currency=transaction_data.get('currency'),
                merchant=transaction_data.get('merchant_name', ''),
                location=transaction_data.get('location', {}),
                device_id=transaction_data.get('device_info', {}).get('device_id', ''),
                timestamp=datetime.fromisoformat(transaction_data.get('created_at')),
                status=transaction_data.get('status'),
                user_id=transaction_data.get('account_id')
            )
            
            # Process transaction through detection engine
            result = self.detection_engine.evaluate_transaction(transaction)
            
            logger.info(
                f"Processed transaction {transaction.id} with risk score {result.risk_score}"
            )
            
            if result.is_fraudulent:
                logger.warning(
                    f"Fraud detected for transaction {transaction.id} "
                    f"with risk score {result.risk_score}"
                )
                # TODO: Publish fraud alert
            
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
            raise
            
    def _handle_error(self, error: Exception):
        """Handle processing errors
        
        Args:
            error: Exception that occurred
        """
        logger.error(f"Error in transaction consumer: {str(error)}")
        # TODO: Implement error handling strategy (retry, alert, etc) 