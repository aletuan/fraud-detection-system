import pytest
from datetime import datetime
from src.core.models import (
    TransactionType, TransactionStatus, ValidationErrorCode,
    Coordinates, Location, DeviceInfo, Transaction,
    ValidationError, RuleResult, DetectionResult,
    LOW_RISK_THRESHOLD, MEDIUM_RISK_THRESHOLD, HIGH_RISK_THRESHOLD
)

def test_transaction_type_enum():
    assert TransactionType.DEBIT == "DEBIT"
    assert TransactionType.CREDIT == "CREDIT"
    assert len(TransactionType) == 2

def test_transaction_status_enum():
    assert TransactionStatus.PENDING == "PENDING"
    assert TransactionStatus.COMPLETED == "COMPLETED"
    assert TransactionStatus.FAILED == "FAILED"
    assert len(TransactionStatus) == 3

def test_validation_error_code_enum():
    assert ValidationErrorCode.AMOUNT_LIMIT_EXCEEDED == "AMOUNT_LIMIT_EXCEEDED"
    assert ValidationErrorCode.DAILY_LIMIT_EXCEEDED == "DAILY_LIMIT_EXCEEDED"
    assert ValidationErrorCode.MONTHLY_LIMIT_EXCEEDED == "MONTHLY_LIMIT_EXCEEDED"
    assert ValidationErrorCode.INVALID_CURRENCY == "INVALID_CURRENCY"
    assert ValidationErrorCode.INVALID_TIME == "INVALID_TIME"
    assert ValidationErrorCode.BLOCKED_MERCHANT == "BLOCKED_MERCHANT"
    assert ValidationErrorCode.BLOCKED_LOCATION == "BLOCKED_LOCATION"
    assert ValidationErrorCode.VELOCITY_LIMIT_EXCEEDED == "VELOCITY_LIMIT_EXCEEDED"
    assert ValidationErrorCode.BLOCKED_DEVICE == "BLOCKED_DEVICE"
    assert ValidationErrorCode.DEVICE_LIMIT_EXCEEDED == "DEVICE_LIMIT_EXCEEDED"
    assert ValidationErrorCode.HIGH_RISK_TRANSACTION == "HIGH_RISK_TRANSACTION"
    assert len(ValidationErrorCode) == 11

def test_coordinates():
    coords = Coordinates(latitude=40.7128, longitude=-74.0060)
    assert coords.latitude == 40.7128
    assert coords.longitude == -74.0060

def test_location():
    # Test with all fields
    coords = Coordinates(latitude=40.7128, longitude=-74.0060)
    location = Location(
        country="US",
        city="New York",
        postal_code="10001",
        coordinates=coords
    )
    assert location.country == "US"
    assert location.city == "New York"
    assert location.postal_code == "10001"
    assert location.coordinates == coords

    # Test with minimal fields
    location_minimal = Location(country="US")
    assert location_minimal.country == "US"
    assert location_minimal.city is None
    assert location_minimal.postal_code is None
    assert location_minimal.coordinates is None

def test_device_info():
    # Test with all fields
    device_info = DeviceInfo(
        device_type="MOBILE",
        browser_type="Chrome",
        device_os="iOS",
        is_mobile=True,
        device_id="device123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0"
    )
    assert device_info.device_type == "MOBILE"
    assert device_info.browser_type == "Chrome"
    assert device_info.device_os == "iOS"
    assert device_info.is_mobile is True
    assert device_info.device_id == "device123"
    assert device_info.ip_address == "192.168.1.1"
    assert device_info.user_agent == "Mozilla/5.0"

    # Test with minimal fields
    device_info_minimal = DeviceInfo(
        device_type="DESKTOP",
        browser_type="Firefox",
        device_os="Windows",
        is_mobile=False
    )
    assert device_info_minimal.device_type == "DESKTOP"
    assert device_info_minimal.device_id is None
    assert device_info_minimal.ip_address is None
    assert device_info_minimal.user_agent is None

def test_transaction():
    # Create test data
    timestamp = datetime.utcnow()
    location = Location(country="US", city="New York")
    device_info = DeviceInfo(
        device_type="MOBILE",
        browser_type="Chrome",
        device_os="iOS",
        is_mobile=True
    )
    metadata = {"source": "web"}

    # Test with all fields
    transaction = Transaction(
        id="trans123",
        amount=100.0,
        currency="USD",
        merchant="Test Merchant",
        location=location,
        device_id="device123",
        timestamp=timestamp,
        status=TransactionStatus.PENDING,
        user_id="user123",
        device_info=device_info,
        metadata=metadata
    )

    assert transaction.id == "trans123"
    assert transaction.amount == 100.0
    assert transaction.currency == "USD"
    assert transaction.merchant == "Test Merchant"
    assert transaction.location == location
    assert transaction.device_id == "device123"
    assert transaction.timestamp == timestamp
    assert transaction.status == TransactionStatus.PENDING
    assert transaction.user_id == "user123"
    assert transaction.device_info == device_info
    assert transaction.metadata == metadata

    # Test with minimal fields
    transaction_minimal = Transaction(
        id="trans456",
        amount=200.0,
        currency="EUR",
        merchant="Another Merchant",
        location=location,
        device_id="device456",
        timestamp=timestamp,
        status=TransactionStatus.COMPLETED,
        user_id="user456"
    )

    assert transaction_minimal.device_info is None
    assert transaction_minimal.metadata is None

def test_validation_error():
    error = ValidationError(
        field="amount",
        code=ValidationErrorCode.AMOUNT_LIMIT_EXCEEDED,
        message="Amount exceeds limit",
        details="Maximum amount is 1000"
    )

    assert error.field == "amount"
    assert error.code == ValidationErrorCode.AMOUNT_LIMIT_EXCEEDED
    assert error.message == "Amount exceeds limit"
    assert error.details == "Maximum amount is 1000"

def test_rule_result():
    metadata = {"threshold": 1000}
    result = RuleResult(
        rule_name="AmountRule",
        is_fraudulent=True,
        risk_score=0.85,
        reason="Amount exceeds threshold",
        metadata=metadata
    )

    assert result.rule_name == "AmountRule"
    assert result.is_fraudulent is True
    assert result.risk_score == 0.85
    assert result.reason == "Amount exceeds threshold"
    assert result.metadata == metadata

def test_detection_result():
    # Create test data
    rule_result = RuleResult(
        rule_name="AmountRule",
        is_fraudulent=True,
        risk_score=0.85,
        reason="Amount exceeds threshold"
    )
    validation_error = ValidationError(
        field="amount",
        code=ValidationErrorCode.AMOUNT_LIMIT_EXCEEDED,
        message="Amount exceeds limit"
    )
    metadata = {"processing_time": 0.5}
    created_at = datetime.utcnow()

    # Test with all fields
    result = DetectionResult(
        transaction_id="trans123",
        is_fraudulent=True,
        risk_score=0.85,
        triggered_rules=[rule_result],
        errors=[validation_error],
        metadata=metadata,
        created_at=created_at
    )

    assert result.transaction_id == "trans123"
    assert result.is_fraudulent is True
    assert result.risk_score == 0.85
    assert result.triggered_rules == [rule_result]
    assert result.errors == [validation_error]
    assert result.metadata == metadata
    assert result.created_at == created_at

    # Test with minimal fields
    result_minimal = DetectionResult(
        transaction_id="trans456",
        is_fraudulent=False,
        risk_score=0.2,
        triggered_rules=[]
    )

    assert result_minimal.errors is None
    assert result_minimal.metadata is None
    assert isinstance(result_minimal.created_at, datetime)

def test_risk_thresholds():
    assert LOW_RISK_THRESHOLD == 0.3
    assert MEDIUM_RISK_THRESHOLD == 0.6
    assert HIGH_RISK_THRESHOLD == 0.8
    assert LOW_RISK_THRESHOLD < MEDIUM_RISK_THRESHOLD < HIGH_RISK_THRESHOLD 