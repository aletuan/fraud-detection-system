import logging
import signal
import sys
from typing import Optional

from src.config import settings
from src.kafka.consumer import TransactionConsumer
from src.utils.logging import setup_logging

logger = logging.getLogger(__name__)
consumer: Optional[TransactionConsumer] = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    if consumer:
        consumer.stop()
    sys.exit(0)

def main():
    """Main entry point for the fraud detection service"""
    try:
        # Setup logging
        setup_logging()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start consumer
        global consumer
        consumer = TransactionConsumer()
        
        logger.info("Starting Fraud Detection Service")
        consumer.start()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 