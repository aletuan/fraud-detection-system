import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from confluent_kafka import Consumer, KafkaError, Message
from src.config import settings
from src.core.models import Transaction
from src.detection.engine import FraudDetectionEngine

logger = logging.getLogger(__name__)

class TransactionConsumer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or settings.KAFKA_CONFIG
        self.consumer = Consumer(self.config)
        self.engine = FraudDetectionEngine()
        self.running = False

    def start(self):
        """Start consuming messages from Kafka"""
        try:
            self.consumer.subscribe([settings.TRANSACTION_TOPIC])
            self.running = True
            
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug("Reached end of partition")
                    else:
                        logger.error(f"Error while consuming message: {msg.error()}")
                    continue
                
                self._process_message(msg)
                
        except Exception as e:
            logger.error(f"Error in consumer: {e}")
            raise
        finally:
            self.stop()

    def stop(self):
        """Stop consuming messages and close the consumer"""
        self.running = False
        self.consumer.close()

    def _process_message(self, msg: Message):
        """Process a single message from Kafka"""
        try:
            transaction_data = json.loads(msg.value())
            # Convert string timestamp to datetime
            transaction_data['created_at'] = datetime.fromisoformat(
                transaction_data['created_at'].replace('Z', '+00:00')
            )
            
            transaction = Transaction(**transaction_data)
            result = self.engine.analyze_transaction(transaction)
            
            if result.is_fraudulent:
                logger.info(
                    f"Fraud detected for transaction {transaction.id} "
                    f"with risk score {result.risk_score}"
                )
                # TODO: Publish fraud alert
            
            self.consumer.commit(msg)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}") 