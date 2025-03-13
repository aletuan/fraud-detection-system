import logging
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from queue import PriorityQueue, Queue
from time import time
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Metrics
PROCESSING_LATENCY = Histogram(
    'transaction_processing_latency_seconds',
    'Time spent processing transactions',
    ['partition']
)
PROCESSED_MESSAGES = Counter(
    'processed_messages_total',
    'Total number of processed messages',
    ['partition', 'status']
)
CONCURRENT_TASKS = Histogram(
    'concurrent_tasks',
    'Number of concurrent tasks',
    ['partition']
)

@dataclass
class Message:
    """Message wrapper with ordering information"""
    partition: int
    offset: int
    key: Optional[str]
    value: Dict[str, Any]
    timestamp: float
    
    def __lt__(self, other):
        # First compare partition
        if self.partition != other.partition:
            return self.partition < other.partition
        # Then compare offset within same partition
        return self.offset < other.offset

@dataclass
class ProcessingResult:
    """Result of message processing"""
    message: Message
    result: Any
    error: Optional[Exception] = None

class OrderedProcessor:
    """Handles ordered processing of messages within a partition"""
    def __init__(self):
        self.next_offset = 0
        self.results = {}
        self.lock = threading.Lock()
        self.result_available = threading.Event()
        self.ordered_results = []
        self.running = True  # Set running before starting thread
        self.processing_thread = threading.Thread(
            target=self._process_results,
            daemon=True
        )
        self.processing_thread.start()
        
    def submit_result(self, result: ProcessingResult):
        """Submit processing result"""
        with self.lock:
            self.results[result.message.offset] = result
            self.result_available.set()
            
    def _process_results(self):
        """Process results in order"""
        while self.running:
            self.result_available.wait()
            
            with self.lock:
                while self.next_offset in self.results:
                    result = self.results.pop(self.next_offset)
                    if result.error is None:  # Only add successful results
                        self.ordered_results.append(result.result)
                    self.next_offset += 1
                    
                if not self.results:
                    self.result_available.clear()
                    
    def get_results(self) -> list:
        """Get ordered results"""
        return self.ordered_results.copy()  # Return copy to prevent modification
        
    def stop(self):
        """Stop processing"""
        self.running = False
        self.result_available.set()  # Wake up processing thread
        self.processing_thread.join(timeout=1.0)  # Wait with timeout

class ConcurrentProcessor:
    def __init__(
        self,
        max_workers: int = 10,
        preserve_ordering: bool = True,
        batch_size: int = 100
    ):
        """Initialize concurrent processor
        
        Args:
            max_workers: Maximum number of worker threads
            preserve_ordering: Whether to preserve message ordering within partition
            batch_size: Maximum number of messages to process in parallel
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.preserve_ordering = preserve_ordering
        self.batch_size = batch_size
        
        # Track futures by partition
        self.futures: Dict[int, Dict[int, Future]] = {}
        self.partition_locks = {}
        
        # Ordered processors by partition
        self.ordered_processors: Dict[int, OrderedProcessor] = {}
        
    def submit(
        self,
        message: Message,
        processor: Callable[[Dict[str, Any]], Any]
    ) -> Future:
        """Submit message for processing
        
        Args:
            message: Message to process
            processor: Callback function to process message
            
        Returns:
            Future for the processing task
        """
        partition = message.partition
        
        # Initialize tracking for new partition
        if partition not in self.futures:
            self.futures[partition] = {}
            self.partition_locks[partition] = threading.Lock()
            if self.preserve_ordering:
                self.ordered_processors[partition] = OrderedProcessor()
            
        with self.partition_locks[partition]:
            # Submit task to thread pool
            future = self.executor.submit(
                self._process_message,
                message,
                processor
            )
            
            # Track future
            self.futures[partition][message.offset] = future
            
            # Update metrics
            CONCURRENT_TASKS.labels(partition=partition).observe(
                len(self.futures[partition])
            )
            
            return future
            
    def _process_message(
        self,
        message: Message,
        processor: Callable[[Dict[str, Any]], Any]
    ):
        """Process single message with metrics
        
        Args:
            message: Message to process
            processor: Processing callback
        """
        start_time = time()
        partition = message.partition
        
        try:
            # Process message
            result = processor(message.value)
            
            # Create processing result
            proc_result = ProcessingResult(
                message=message,
                result=result
            )
            
            # Submit to ordered processor if needed
            if self.preserve_ordering:
                self.ordered_processors[partition].submit_result(proc_result)
            
            # Update metrics
            PROCESSED_MESSAGES.labels(
                partition=partition,
                status="success"
            ).inc()
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error processing message {message.partition}:{message.offset} - {str(e)}"
            )
            PROCESSED_MESSAGES.labels(
                partition=partition,
                status="error"
            ).inc()
            
            if self.preserve_ordering:
                self.ordered_processors[partition].submit_result(
                    ProcessingResult(
                        message=message,
                        result=None,
                        error=e
                    )
                )
            raise
            
        finally:
            # Record processing time
            PROCESSING_LATENCY.labels(partition=partition).observe(
                time() - start_time
            )
            
            # Cleanup
            with self.partition_locks[partition]:
                self.futures[partition].pop(message.offset, None)
                
    def get_results(self, partition: int) -> list:
        """Get ordered results for partition
        
        Args:
            partition: Partition to get results for
            
        Returns:
            List of results in order
        """
        if not self.preserve_ordering:
            return []
            
        return self.ordered_processors[partition].get_results()
            
    def shutdown(self):
        """Shutdown processor and wait for completion"""
        # Stop ordered processors
        for processor in self.ordered_processors.values():
            processor.stop()
            
        # Shutdown thread pool
        self.executor.shutdown(wait=True) 