import json
import logging
from typing import Optional
from datetime import datetime
from confluent_kafka import Producer
from prometheus_client import Counter

from .alerts import FraudAlert
from config import settings

logger = logging.getLogger(__name__)

# Metrics
ALERTS_PUBLISHED = Counter(
    'fraud_alerts_published_total',
    'Total number of fraud alerts published',
    ['status']
)

class AlertService:
    """Service for publishing fraud alerts"""
    
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        alert_topic: Optional[str] = None
    ):
        """Initialize alert service
        
        Args:
            bootstrap_servers: Kafka bootstrap servers
            alert_topic: Topic to publish alerts to
        """
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.alert_topic = alert_topic or settings.SECURITY_ALERT_TOPIC
        
        # Initialize Kafka producer
        self.producer = Producer({
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': 'fraud-detection-alerts'
        })
        
    def publish_alert(self, alert: FraudAlert) -> None:
        """Publish fraud alert to Kafka
        
        Args:
            alert: Fraud alert to publish
        """
        try:
            # Convert alert to JSON
            alert_data = {
                'transaction_id': alert.transaction_id,
                'user_id': alert.user_id,
                'risk_score': alert.risk_score,
                'rules_triggered': alert.rules_triggered,
                'transaction_amount': alert.transaction_amount,
                'transaction_currency': alert.transaction_currency,
                'merchant': alert.merchant,
                'location': alert.location,
                'device_info': alert.device_info,
                'timestamp': alert.timestamp.isoformat(),
                'metadata': alert.metadata,
                'alert_type': 'FRAUD_DETECTION',
                'alert_severity': 'HIGH',
                'alert_timestamp': datetime.utcnow().isoformat()
            }
            
            # Publish to Kafka
            self.producer.produce(
                topic=self.alert_topic,
                key=alert.transaction_id,
                value=json.dumps(alert_data),
                on_delivery=self._delivery_callback
            )
            
            # Ensure message is sent
            self.producer.flush()
            
            logger.info(
                f"Published fraud alert for transaction {alert.transaction_id}:\n"
                f"- Risk score: {alert.risk_score}\n"
                f"- Rules triggered: {alert.rules_triggered}"
            )
            
            ALERTS_PUBLISHED.labels(status='success').inc()
            
        except Exception as e:
            logger.error(f"Failed to publish fraud alert: {str(e)}")
            ALERTS_PUBLISHED.labels(status='error').inc()
            raise
            
    def _delivery_callback(self, err, msg):
        """Callback for message delivery confirmation
        
        Args:
            err: Error that occurred, if any
            msg: Message that was delivered
        """
        if err:
            logger.error(f'Failed to deliver message: {str(err)}')
            ALERTS_PUBLISHED.labels(status='error').inc()
        else:
            logger.debug(
                f'Successfully delivered message to {msg.topic()} [{msg.partition()}] '
                f'at offset {msg.offset()}'
            ) 