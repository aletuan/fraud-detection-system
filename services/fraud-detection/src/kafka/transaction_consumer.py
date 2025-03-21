import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .consumer import KafkaConsumer
from .config import KafkaConfig
from .concurrent_processor import ConcurrentProcessor, Message
from core.alerts import FraudAlert
from core.alert_service import AlertService

# Default Kafka configuration
DEFAULT_BOOTSTRAP_SERVERS = 'kafka:29092'
DEFAULT_GROUP_ID = 'fraud-detection-group'
DEFAULT_TRANSACTION_TOPIC = 'transactions'
DEFAULT_DLQ_TOPIC = 'fraud.detection.dlq'

from core.models import (
    Transaction,
    Location,
    DeviceInfo,
    TransactionStatus,
    DEFAULT_STATUS
)
from detection.engine import FraudDetectionEngine
from config import settings

logger = logging.getLogger(__name__)

class TransactionConsumer:
    def __init__(
        self,
        kafka_config: Optional[KafkaConfig] = None,
        detection_engine: Optional[FraudDetectionEngine] = None,
        alert_service: Optional[AlertService] = None,
        dead_letter_topic: Optional[str] = DEFAULT_DLQ_TOPIC,
        max_workers: int = 10,
        preserve_ordering: bool = True
    ):
        """Initialize Transaction Consumer
        
        Args:
            kafka_config: Kafka configuration, uses settings if not provided
            detection_engine: Fraud detection engine instance
            alert_service: Alert service instance
            dead_letter_topic: Topic for failed messages
            max_workers: Maximum number of concurrent workers
            preserve_ordering: Whether to preserve message ordering within partition
        """
        self.detection_engine = detection_engine or FraudDetectionEngine()
        self.alert_service = alert_service or AlertService()
        
        if kafka_config is None:
            kafka_config = KafkaConfig(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS or DEFAULT_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP or DEFAULT_GROUP_ID,
                topics=[settings.TRANSACTION_TOPIC or DEFAULT_TRANSACTION_TOPIC]
            )
            
        self.processor = ConcurrentProcessor(
            max_workers=max_workers,
            preserve_ordering=preserve_ordering
        )
            
        self.consumer = KafkaConsumer(
            config=kafka_config,
            message_handler=self._handle_message,
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
        self.processor.shutdown()
        
    def _handle_message(self, kafka_message: Dict[str, Any]):
        """Handle incoming Kafka message
        
        Args:
            kafka_message: Raw Kafka message
        """
        # Create message wrapper
        message = Message(
            partition=kafka_message.partition() if hasattr(kafka_message, 'partition') else 0,
            offset=kafka_message.offset() if hasattr(kafka_message, 'offset') else 0,
            key=kafka_message.key() if hasattr(kafka_message, 'key') else None,
            value=kafka_message.value() if hasattr(kafka_message, 'value') else None,
            timestamp=kafka_message.timestamp()[1] if hasattr(kafka_message, 'timestamp') else 0.0
        )
        
        # Submit for processing
        future = self.processor.submit(
            message=message,
            processor=self._process_transaction
        )
        
        # Optionally wait for result
        if message.key and isinstance(message.key, bytes):
            key_str = message.key.decode('utf-8')
            if key_str.startswith('URGENT'):
                try:
                    future.result(timeout=5.0)  # Wait up to 5 seconds
                except Exception as e:
                    logger.error(f"Error processing urgent message: {str(e)}")
                    raise
        
    def _process_transaction(self, message: Dict[str, Any]):
        """Process transaction message
        
        Args:
            message: Transaction message to process
        """
        try:
            # Extract transaction data from event wrapper
            logger.info(f"Raw message: {message}")
            message_value = message.value if isinstance(message, Message) else message
            logger.info(f"Message value: {message_value}")
            
            if message_value is None:
                raise ValueError("Message value is None")
                
            # If message_value is bytes, decode it
            if isinstance(message_value, bytes):
                message_value = message_value.decode('utf-8')
                
            event_data = json.loads(message_value) if isinstance(message_value, str) else message_value
            logger.info(f"Event data: {event_data}")
            
            # Extract transaction data from event
            transaction_data = event_data.get('transaction')
            if not transaction_data:
                raise ValueError("No transaction data found in event")
            
            logger.info(f"Transaction data: {transaction_data}")
            
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
                timestamp=datetime.fromisoformat(transaction_data.get('created_at').replace('Z', '+00:00')),
                status=transaction_data.get('status', DEFAULT_STATUS),
                user_id=transaction_data.get('account_id'),
                device_info=device_info,
                metadata={
                    'merchant_country': location_data.get('country'),
                    'merchant_category': event_data.get('metadata', {}).get('merchant_category', 'retail')
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
                
                # Create and publish fraud alert
                alert = FraudAlert.from_transaction(
                    transaction=transaction,
                    risk_score=result.risk_score,
                    rules_triggered=result.rules_triggered
                )
                self.alert_service.publish_alert(alert)
                
            return result
            
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