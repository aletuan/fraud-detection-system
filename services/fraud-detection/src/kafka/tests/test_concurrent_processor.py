import pytest
import time
from concurrent.futures import Future
from unittest.mock import Mock, patch

from src.kafka.concurrent_processor import ConcurrentProcessor, Message

@pytest.fixture
def processor():
    """Create ConcurrentProcessor instance"""
    return ConcurrentProcessor(max_workers=2)

@pytest.fixture
def sample_message():
    """Create sample message"""
    return Message(
        partition=0,
        offset=0,
        key="test-key",
        value={"test": "data"},
        timestamp=time.time()
    )

def test_initialization():
    """Test processor initialization"""
    processor = ConcurrentProcessor(
        max_workers=5,
        preserve_ordering=True,
        batch_size=50
    )
    
    assert processor.executor._max_workers == 5
    assert processor.preserve_ordering is True
    assert processor.batch_size == 50
    assert len(processor.futures) == 0
    assert len(processor.partition_locks) == 0
    assert len(processor.ordered_processors) == 0

def test_submit_message(processor, sample_message):
    """Test submitting single message"""
    mock_processor = Mock(return_value="result")
    
    future = processor.submit(sample_message, mock_processor)
    
    assert isinstance(future, Future)
    assert 0 in processor.futures
    assert 0 in processor.futures[0]
    assert future == processor.futures[0][0]
    
    result = future.result(timeout=1.0)
    assert result == "result"
    mock_processor.assert_called_once_with(sample_message.value)

def test_parallel_processing(processor):
    """Test processing multiple messages in parallel"""
    results = []
    processed = []
    
    def slow_processor(value):
        time.sleep(0.1)  # Simulate work
        processed.append(value['id'])
        return value['id']
    
    # Submit multiple messages
    messages = [
        Message(
            partition=0,
            offset=i,
            key=f"key-{i}",
            value={"id": i},
            timestamp=time.time()
        )
        for i in range(5)
    ]
    
    # Submit and collect futures
    futures = [
        processor.submit(message, slow_processor)
        for message in messages
    ]
    
    # Wait for all results
    for future in futures:
        results.append(future.result(timeout=1.0))
    
    # Verify parallel execution
    assert len(results) == 5
    assert len(processed) == 5
    # Order of processing may vary
    assert sorted(results) == [0, 1, 2, 3, 4]
    assert sorted(processed) == [0, 1, 2, 3, 4]

def test_preserve_ordering(processor):
    """Test message ordering preservation"""
    def track_processor(value):
        return value['id']
    
    # Submit messages out of order
    messages = [
        Message(
            partition=0,
            offset=i,
            key=f"key-{i}",
            value={"id": i},
            timestamp=time.time()
        )
        for i in [2, 0, 1, 4, 3]  # Intentionally out of order
    ]
    
    # Submit all messages
    futures = [
        processor.submit(message, track_processor)
        for message in messages
    ]
    
    # Wait for completion
    for future in futures:
        future.result(timeout=1.0)
        
    # Allow time for result processing
    time.sleep(0.1)
        
    # Get ordered results
    ordered_results = processor.get_results(0)
    
    # Verify order preservation
    assert ordered_results == [0, 1, 2, 3, 4]

def test_error_handling(processor, sample_message):
    """Test error handling during processing"""
    def failing_processor(value):
        raise ValueError("Test error")
    
    future = processor.submit(sample_message, failing_processor)
    
    with pytest.raises(ValueError, match="Test error"):
        future.result(timeout=1.0)
    
    # Verify cleanup
    assert len(processor.futures[0]) == 0

@patch('prometheus_client.Counter.inc')
@patch('prometheus_client.Histogram.observe')
def test_metrics(mock_observe, mock_inc, processor, sample_message):
    """Test metrics recording"""
    mock_processor = Mock(return_value="result")
    
    future = processor.submit(sample_message, mock_processor)
    future.result(timeout=1.0)
    
    # Verify metrics
    assert mock_observe.call_count >= 2  # Latency and concurrent tasks
    assert mock_inc.call_count >= 1  # Processed messages

def test_multiple_partitions(processor):
    """Test processing messages from multiple partitions"""
    results = {}
    
    def partition_processor(value):
        time.sleep(0.1)  # Simulate work
        partition = value['partition']
        if partition not in results:
            results[partition] = []
        results[partition].append(value['id'])
        return value['id']
    
    # Create messages for different partitions
    messages = []
    for partition in range(3):
        for offset in range(3):
            messages.append(
                Message(
                    partition=partition,
                    offset=offset,
                    key=f"key-{partition}-{offset}",
                    value={
                        "id": offset,
                        "partition": partition
                    },
                    timestamp=time.time()
                )
            )
    
    # Submit all messages
    futures = [
        processor.submit(message, partition_processor)
        for message in messages
    ]
    
    # Wait for completion
    for future in futures:
        future.result(timeout=1.0)
    
    # Verify results per partition
    assert len(results) == 3
    for partition in range(3):
        assert sorted(results[partition]) == [0, 1, 2]

def test_shutdown(processor):
    """Test graceful shutdown"""
    processed = []
    
    def slow_processor(value):
        time.sleep(0.1)
        processed.append(value['id'])
        return value['id']
    
    # Submit some messages
    messages = [
        Message(
            partition=0,
            offset=i,
            key=f"key-{i}",
            value={"id": i},
            timestamp=time.time()
        )
        for i in range(3)
    ]
    
    # Submit messages
    for message in messages:
        processor.submit(message, slow_processor)
    
    # Shutdown and verify completion
    processor.shutdown()
    
    assert len(processed) == 3
    assert sorted(processed) == [0, 1, 2]
    assert len(processor.futures) == 1  # Only partition 0
    assert len(processor.futures[0]) == 0  # All messages processed 