import pytest
import time
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'performance_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all performance tests"""
    logger.info("Starting performance test suite")
    start_time = time.time()
    
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run transaction generation test
    logger.info("\nRunning transaction generation test...")
    pytest.main([
        os.path.join(current_dir, "test_performance.py"),
        "-v",
        "--capture=no"
    ])
    
    # Wait for events to be processed
    logger.info("\nWaiting for events to be processed...")
    time.sleep(5)
    
    # Run Kafka events test
    logger.info("\nRunning Kafka events test...")
    pytest.main([
        os.path.join(current_dir, "test_kafka_events.py"),
        "-v",
        "--capture=no"
    ])
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"\nPerformance test suite completed in {duration:.2f} seconds")

if __name__ == "__main__":
    run_tests() 