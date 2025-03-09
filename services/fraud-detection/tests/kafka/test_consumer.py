import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from confluent_kafka import KafkaError, Message

from src.kafka.config import KafkaConfig
from src.kafka.consumer import KafkaConsumer
from src.kafka.transaction_consumer import TransactionConsumer
from src.core.models import Transaction
from src.detection.engine import FraudDetectionEngine, DetectionResult

@pytest.fixture
def kafka_config():
    return KafkaConfig(
        bootstrap_servers="localhost:9092",
        group_id="test-group",
        topics=["test-topic"]
    )

@pytest.fixture
def mock_message():
    message = Mock(spec=Message)
    message.error.return_value = None
    message.value.return_value = json.dumps({
        "id": "tx123",
        "amount": 1000.0,
        "currency": "USD",
        "merchant": "Test Merchant",
        "location": "US",
        "device_id": "device123",
        "timestamp": "2024-03-08T12:00:00",
        "status": "PENDING",
        "user_id": "user123"
    }).encode('utf-8')
    message.topic.return_value = "test-topic"
    message.partition.return_value = 0
    message.offset.return_value = 100
    message.timestamp.return_value = (1, 1709942400000)  # timestamp type, timestamp
    return message

@pytest.fixture
def mock_detection_engine():
    engine = Mock(spec=FraudDetectionEngine)
    engine.evaluate_transaction.return_value = DetectionResult(
        risk_score=0.1,
        is_fraudulent=False,
        rules_triggered=[]
    )
    return engine

def test_kafka_consumer_message_processing(kafka_config, mock_message):
    """Test that messages are properly processed by the base consumer"""
    # Setup
    message_handler = Mock()
    consumer = KafkaConsumer(
        config=kafka_config,
        message_handler=message_handler
    )
    
    # Execute
    consumer._process_message(mock_message)
    
    # Verify
    message_handler.assert_called_once()
    expected_value = json.loads(mock_message.value().decode('utf-8'))
    message_handler.assert_called_with(expected_value)

def test_kafka_consumer_handles_json_decode_error(kafka_config):
    """Test that invalid JSON messages are handled properly"""
    # Setup
    message_handler = Mock()
    consumer = KafkaConsumer(
        config=kafka_config,
        message_handler=message_handler,
        dead_letter_topic="test-dlq"
    )
    
    # Create invalid JSON message
    invalid_message = Mock(spec=Message)
    invalid_message.error.return_value = None
    invalid_message.value.return_value = b'invalid json'
    invalid_message.topic.return_value = "test-topic"
    invalid_message.partition.return_value = 0
    invalid_message.offset.return_value = 100
    invalid_message.timestamp.return_value = (1, 1709942400000)
    
    # Execute
    with patch.object(consumer, '_send_to_dead_letter') as mock_dlq:
        consumer._process_message(invalid_message)
        
        # Verify
        mock_dlq.assert_called_once()
        message_handler.assert_not_called()
    
def test_transaction_consumer_handles_valid_transaction(
    kafka_config,
    mock_message,
    mock_detection_engine
):
    """Test that TransactionConsumer properly processes valid transactions"""
    # Setup
    consumer = TransactionConsumer(
        kafka_config=kafka_config,
        detection_engine=mock_detection_engine
    )
    
    # Get the message handler
    message_handler = consumer._handle_transaction
    
    # Execute
    message_data = json.loads(mock_message.value().decode('utf-8'))
    message_handler(message_data)
    
    # Verify
    mock_detection_engine.evaluate_transaction.assert_called_once()
    call_args = mock_detection_engine.evaluate_transaction.call_args[0][0]
    assert isinstance(call_args, Transaction)
    assert call_args.id == "tx123"
    assert call_args.amount == 1000.0
    assert call_args.currency == "USD"

def test_transaction_consumer_handles_fraud_detection(
    kafka_config,
    mock_message,
    mock_detection_engine
):
    """Test that fraud detection results are handled properly"""
    # Setup
    mock_detection_engine.evaluate_transaction.return_value = DetectionResult(
        risk_score=0.9,
        is_fraudulent=True,
        rules_triggered=['high_amount', 'suspicious_location']
    )
    
    consumer = TransactionConsumer(
        kafka_config=kafka_config,
        detection_engine=mock_detection_engine
    )
    
    # Execute
    message_data = json.loads(mock_message.value().decode('utf-8'))
    with patch('logging.Logger.warning') as mock_warning:
        consumer._handle_transaction(message_data)
        
        # Verify warning was logged for fraud detection
        mock_warning.assert_called_once()

@pytest.mark.parametrize("error_code,expected_reconnect", [
    (KafkaError._PARTITION_EOF, False),
    (KafkaError._TRANSPORT, True)
])
def test_kafka_consumer_error_handling(kafka_config, error_code, expected_reconnect):
    """Test that different Kafka errors are handled appropriately"""
    # Setup
    consumer = KafkaConsumer(
        config=kafka_config,
        message_handler=Mock()
    )
    
    # Create mock error
    error = Mock(spec=KafkaError)
    error.code.return_value = error_code
    error.str.return_value = "Test error"
    
    # Mock reconnect method
    with patch.object(consumer, '_reconnect') as mock_reconnect:
        # Execute
        consumer._handle_error(error)
        
        # Verify
        if expected_reconnect:
            mock_reconnect.assert_called_once()
        else:
            mock_reconnect.assert_not_called() 