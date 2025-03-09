import json
import logging
from typing import Callable, Optional
from confluent_kafka import Consumer, KafkaError, Message, KafkaException
from .config import KafkaConfig

logger = logging.getLogger(__name__)

class KafkaConsumer:
    def __init__(
        self,
        config: KafkaConfig,
        message_handler: Callable,
        error_handler: Optional[Callable] = None,
        dead_letter_topic: Optional[str] = None
    ):
        """Initialize Kafka consumer
        
        Args:
            config: Kafka configuration
            message_handler: Callback function to process messages
            error_handler: Optional callback function to handle errors
            dead_letter_topic: Optional topic for failed messages
        """
        self.config = config
        self.message_handler = message_handler
        self.error_handler = error_handler
        self.dead_letter_topic = dead_letter_topic
        self.consumer = None
        self.running = False
        
    def start(self):
        """Start the consumer"""
        try:
            self.consumer = Consumer(self.config.to_dict())
            self.consumer.subscribe(self.config.topics, on_assign=self._on_assign)
            self.running = True
            
            while self.running:
                try:
                    msg = self.consumer.poll(timeout=1.0)
                    if msg is None:
                        continue
                    
                    if msg.error():
                        self._handle_error(msg.error())
                        continue
                        
                    self._process_message(msg)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    if self.error_handler:
                        self.error_handler(e)
                        
        except KafkaException as e:
            logger.error(f"Kafka error: {str(e)}")
            raise
        finally:
            self._close()
            
    def stop(self):
        """Stop the consumer"""
        self.running = False
        
    def _process_message(self, msg: Message):
        """Process a single message"""
        try:
            # Parse message value
            value = json.loads(msg.value().decode('utf-8'))
            
            # Process message
            self.message_handler(value)
            
            # Manual commit after successful processing
            self.consumer.commit(msg)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {str(e)}")
            self._send_to_dead_letter(msg, "Invalid JSON format")
            
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            self._send_to_dead_letter(msg, str(e))
            
    def _handle_error(self, error: KafkaError):
        """Handle Kafka errors"""
        if error.code() == KafkaError._PARTITION_EOF:
            logger.info("Reached end of partition")
        elif error.code() == KafkaError._TRANSPORT:
            logger.error("Transport error occurred")
            self._reconnect()
        else:
            logger.error(f"Kafka error: {error.str()}")
            
    def _send_to_dead_letter(self, msg: Message, error_reason: str):
        """Send failed message to dead letter topic"""
        if not self.dead_letter_topic:
            return
            
        try:
            dead_letter_msg = {
                'original_topic': msg.topic(),
                'original_partition': msg.partition(),
                'original_offset': msg.offset(),
                'original_value': msg.value().decode('utf-8'),
                'error_reason': error_reason,
                'timestamp': msg.timestamp()[1]
            }
            
            # TODO: Implement dead letter queue producer
            logger.info(f"Message sent to dead letter topic: {dead_letter_msg}")
            
        except Exception as e:
            logger.error(f"Failed to send message to dead letter topic: {str(e)}")
            
    def _reconnect(self):
        """Attempt to reconnect to Kafka"""
        try:
            logger.info("Attempting to reconnect to Kafka...")
            self._close()
            self.consumer = Consumer(self.config.to_dict())
            self.consumer.subscribe(self.config.topics, on_assign=self._on_assign)
            logger.info("Successfully reconnected to Kafka")
        except Exception as e:
            logger.error(f"Failed to reconnect to Kafka: {str(e)}")
            
    def _on_assign(self, consumer, partitions):
        """Callback for partition assignment"""
        logger.info(f"Assigned partitions: {partitions}")
        
    def _close(self):
        """Close the consumer"""
        if self.consumer:
            self.consumer.close()
            self.consumer = None 