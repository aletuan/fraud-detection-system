import logging
import os
import signal
import sys
import threading
from typing import Optional

import uvicorn
from api import app
from kafka.config import KafkaConfig
from kafka.transaction_consumer import TransactionConsumer
from detection.engine import FraudDetectionEngine

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FraudDetectionService:
    def __init__(self):
        """Initialize the Fraud Detection Service"""
        self.consumer: Optional[TransactionConsumer] = None
        self.running = False
        self.api_thread = None
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
    def start(self):
        """Start the Fraud Detection Service"""
        try:
            logger.info("Starting Fraud Detection Service...")
            
            # Start API server in a separate thread
            self.api_thread = threading.Thread(
                target=uvicorn.run,
                args=(app,),
                kwargs={
                    "host": "0.0.0.0",
                    "port": 8000,
                    "log_level": "info"
                },
                daemon=True
            )
            self.api_thread.start()
            
            # Initialize Kafka config
            kafka_config = KafkaConfig(
                bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
                group_id=os.getenv('KAFKA_CONSUMER_GROUP', 'fraud-detection-group'),
                topics=[os.getenv('KAFKA_TRANSACTION_TOPIC', 'transactions')]
            )
            
            # Initialize detection engine
            detection_engine = FraudDetectionEngine()
            
            # Initialize and start consumer
            self.consumer = TransactionConsumer(
                kafka_config=kafka_config,
                detection_engine=detection_engine,
                dead_letter_topic=os.getenv('KAFKA_DLQ_TOPIC', 'fraud.detection.dlq')
            )
            
            self.running = True
            self.consumer.start()
            
        except Exception as e:
            logger.error(f"Failed to start service: {str(e)}")
            self.shutdown()
            sys.exit(1)
            
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.shutdown()
        
    def shutdown(self):
        """Shutdown the service gracefully"""
        logger.info("Shutting down Fraud Detection Service...")
        self.running = False
        if self.consumer:
            self.consumer.stop()
        sys.exit(0)

if __name__ == "__main__":
    service = FraudDetectionService()
    service.start() 