import pytest
import time
from confluent_kafka import Consumer, KafkaError
import json
import logging
from typing import List, Dict
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_iso_datetime(dt_str: str) -> datetime:
    """Safely parse ISO datetime string"""
    try:
        # Remove any whitespace
        dt_str = dt_str.strip()
        
        # Handle microseconds format
        if '.' in dt_str:
            main_part, ms_part = dt_str.split('.')
            if 'Z' in ms_part:
                ms_part = ms_part.replace('Z', '')
            # Ensure microseconds are 6 digits
            ms_part = ms_part[:6].ljust(6, '0')
            dt_str = f"{main_part}.{ms_part}+00:00"
        else:
            # Add UTC timezone if no timezone specified
            if not any(x in dt_str for x in ['+', '-', 'Z']):
                dt_str = dt_str + '+00:00'
            elif 'Z' in dt_str:
                dt_str = dt_str.replace('Z', '+00:00')
                
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError) as e:
        logger.error(f"Error parsing datetime '{dt_str}': {str(e)}")
        return None

class KafkaEventChecker:
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.consumer = None
        self.events = []
        
    def setup(self):
        """Setup Kafka consumer"""
        self.consumer = Consumer({
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': 'performance_test_group',
            'auto.offset.reset': 'earliest'
        })
        
    def consume_events(self, topic: str, timeout: int = 30) -> List[Dict]:
        """Consume events from Kafka topic"""
        self.consumer.subscribe([topic])
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            msg = self.consumer.poll(1.0)
            
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    break
                    
            try:
                event = json.loads(msg.value().decode('utf-8'))
                self.events.append(event)
                logger.info(f"Received event: {event['event_id']}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding message: {e}")
                
        return self.events
    
    def cleanup(self):
        """Cleanup Kafka consumer"""
        if self.consumer:
            self.consumer.close()

def test_kafka_events():
    """Test Kafka events and Fraud Detection Service performance"""
    checker = KafkaEventChecker()
    checker.setup()
    
    try:
        # Consume events from transactions topic
        logger.info("Consuming events from transactions topic...")
        transaction_events = checker.consume_events("transactions")
        
        # Basic assertions
        assert len(transaction_events) > 0, "No transaction events found"
        
        # Analyze events
        logger.info(f"\nFound {len(transaction_events)} transaction events")
        
        # Group events by risk level
        risk_levels = {}
        for event in transaction_events:
            transaction = event.get('transaction', {})
            amount = transaction.get('amount', 0)
            
            # Determine risk level based on amount
            if amount >= 9000:
                risk = "HIGH"
            elif amount >= 5000:
                risk = "MEDIUM"
            else:
                risk = "LOW"
                
            if risk not in risk_levels:
                risk_levels[risk] = []
            risk_levels[risk].append(event)
        
        # Log risk level distribution
        logger.info("\nRisk Level Distribution:")
        for risk, events in risk_levels.items():
            logger.info(f"{risk} Risk: {len(events)} transactions")
            
        # Check processing time
        processing_times = []
        for event in transaction_events:
            transaction = event.get('transaction', {})
            created_at = parse_iso_datetime(transaction.get('created_at'))
            occurred_at = parse_iso_datetime(event.get('occurred_at'))
            
            if created_at and occurred_at:
                processing_time = (created_at - occurred_at).total_seconds()
                processing_times.append(processing_time)
        
        if processing_times:
            avg_processing_time = sum(processing_times) / len(processing_times)
            logger.info(f"\nAverage processing time: {avg_processing_time:.2f} seconds")
            
            # Performance assertions
            assert avg_processing_time < 2.0, "Average processing time too high"
        
        # Log detailed event analysis
        logger.info("\nDetailed Event Analysis:")
        for event in transaction_events:
            transaction = event.get('transaction', {})
            logger.info(f"\nEvent ID: {event.get('event_id')}")
            logger.info(f"Transaction ID: {transaction.get('id')}")
            logger.info(f"Amount: {transaction.get('amount')}")
            logger.info(f"Location: {transaction.get('location', {}).get('country')} ({transaction.get('location', {}).get('city')})")
            logger.info(f"Device: {transaction.get('device_info', {}).get('device_type')}")
            
            created_at = parse_iso_datetime(transaction.get('created_at'))
            occurred_at = parse_iso_datetime(event.get('occurred_at'))
            if created_at and occurred_at:
                processing_time = (created_at - occurred_at).total_seconds()
                logger.info(f"Processing time: {processing_time:.2f} seconds")
            
    finally:
        checker.cleanup()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 