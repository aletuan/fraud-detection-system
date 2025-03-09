import os
import sys
import pytest

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import fixtures that should be available to all tests
from tests.kafka.test_consumer import (
    kafka_config,
    mock_message,
    mock_detection_engine
)

# Register fixtures
__all__ = ['kafka_config', 'mock_message', 'mock_detection_engine'] 