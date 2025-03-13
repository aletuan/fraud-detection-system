import pytest
from metrics import (
    REQUESTS, PROCESSING_TIME,
    TRANSACTIONS_PROCESSED, FRAUD_DETECTED, RISK_SCORE
)

def test_request_counter():
    """Test request counter increments correctly"""
    initial_count = REQUESTS.collect()[0].samples[0].value
    REQUESTS.inc()
    final_count = REQUESTS.collect()[0].samples[0].value
    assert final_count == initial_count + 1

    # Test increment with specific value
    REQUESTS.inc(2)
    final_count = REQUESTS.collect()[0].samples[0].value
    assert final_count == initial_count + 3

def test_processing_time_histogram():
    """Test processing time histogram records values correctly"""
    initial_count = _get_histogram_count(PROCESSING_TIME)
    initial_sum = _get_histogram_sum(PROCESSING_TIME)
    
    # Observe some processing times
    PROCESSING_TIME.observe(0.5)  # 500ms
    PROCESSING_TIME.observe(1.0)  # 1s
    
    final_count = _get_histogram_count(PROCESSING_TIME)
    final_sum = _get_histogram_sum(PROCESSING_TIME)
    
    assert final_count == initial_count + 2
    assert final_sum == initial_sum + 1.5

def test_transactions_processed_counter():
    """Test transactions processed counter increments correctly"""
    initial_count = TRANSACTIONS_PROCESSED.collect()[0].samples[0].value
    TRANSACTIONS_PROCESSED.inc()
    final_count = TRANSACTIONS_PROCESSED.collect()[0].samples[0].value
    assert final_count == initial_count + 1

def test_fraud_detected_counter():
    """Test fraud detected counter increments correctly"""
    initial_count = FRAUD_DETECTED.collect()[0].samples[0].value
    FRAUD_DETECTED.inc()
    final_count = FRAUD_DETECTED.collect()[0].samples[0].value
    assert final_count == initial_count + 1

def test_risk_score_histogram():
    """Test risk score histogram records values correctly"""
    initial_count = _get_histogram_count(RISK_SCORE)
    initial_sum = _get_histogram_sum(RISK_SCORE)
    
    # Observe some risk scores
    RISK_SCORE.observe(0.3)  # Low risk
    RISK_SCORE.observe(0.7)  # Medium risk
    RISK_SCORE.observe(0.9)  # High risk
    
    final_count = _get_histogram_count(RISK_SCORE)
    final_sum = _get_histogram_sum(RISK_SCORE)
    
    assert final_count == initial_count + 3
    assert final_sum == initial_sum + 1.9

def _get_histogram_count(histogram):
    """Helper function to get total count from histogram"""
    return sum(sample.value for sample in histogram.collect()[0].samples
              if sample.name.endswith('_count'))

def _get_histogram_sum(histogram):
    """Helper function to get total sum from histogram"""
    return sum(sample.value for sample in histogram.collect()[0].samples
              if sample.name.endswith('_sum')) 