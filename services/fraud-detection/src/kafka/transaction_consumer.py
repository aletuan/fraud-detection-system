import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .consumer import KafkaConsumer
from .config import KafkaConfig
from core.models import Transaction, Location, DeviceInfo
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
            location_data = transaction_data.get('location', {})
            device_data = transaction_data.get('device_info', {})
            
            location = Location(
                country=location_data.get('country', ''),
                city=location_data.get('city')
            )
            
            device_info = DeviceInfo(
                device_type=device_data.get('device_type', 'unknown'),
                browser_type=device_data.get('browser_type', 'unknown'),
                device_os=device_data.get('device_os', 'unknown'),
                is_mobile=device_data.get('is_mobile', False),
                device_id=device_data.get('device_id'),
                ip_address=device_data.get('ip_address')
            )
            
            transaction = Transaction(
                id=transaction_data.get('id'),
                amount=transaction_data.get('amount'),
                currency=transaction_data.get('currency'),
                merchant=transaction_data.get('merchant_name', ''),
                location=location,
                device_id=device_data.get('device_id', ''),
                timestamp=datetime.fromisoformat(transaction_data.get('created_at')),
                status=transaction_data.get('status'),
                user_id=transaction_data.get('account_id'),
                device_info=device_info,
                metadata={
                    'merchant_country': location_data.get('country'),
                    'merchant_category': 'retail',  # Default category for now
                }
            )
            
            # Process transaction through detection engine
            logger.info(
                f"Processing transaction {transaction.id}:\n"
                f"- Location: {transaction.location.country} ({transaction.location.city})\n"
                f"- Device: {transaction.device_info.device_type} ({transaction.device_info.browser_type} on {transaction.device_info.device_os})\n"
                f"- Amount: {transaction.amount} {transaction.currency}"
            )
            
            result = self.detection_engine.evaluate_transaction(transaction)
            
            logger.info(
                f"Processed transaction {transaction.id}:\n"
                f"- Risk score: {result.risk_score}\n"
                f"- Is fraudulent: {result.is_fraudulent}\n"
                f"- Rules triggered: {result.rules_triggered}\n"
                f"- Location: {transaction.location.country} ({transaction.location.city})\n"
                f"- Device: {transaction.device_info.device_type} ({transaction.device_info.browser_type} on {transaction.device_info.device_os})\n"
                f"- Amount: {transaction.amount} {transaction.currency}"
            )
            
            if result.is_fraudulent:
                logger.warning(
                    f"Fraud detected for transaction {transaction.id}:\n"
                    f"- Risk score: {result.risk_score}\n"
                    f"- Rules triggered: {result.rules_triggered}\n"
                    f"- Location: {transaction.location.country} ({transaction.location.city})\n"
                    f"- Device: {transaction.device_info.device_type} ({transaction.device_info.browser_type} on {transaction.device_info.device_os})\n"
                    f"- Amount: {transaction.amount} {transaction.currency}"
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