import pytest
from datetime import datetime

from src.core.models import Transaction, Location, DeviceInfo, ValidationErrorCode, Coordinates
from src.detection.rules.location_rule import LocationBasedRule, LocationRules

@pytest.fixture
def sample_transaction():
    """Create a sample transaction for testing"""
    return Transaction(
        id="test_id",
        amount=100.00,
        currency="USD",
        merchant="Test Store",
        location=Location(
            country="US",
            city="New York",
            coordinates=Coordinates(
                latitude=40.7128,
                longitude=-74.0060
            )
        ),
        device_id="device123",
        timestamp=datetime.now(),
        status="PENDING",
        user_id="USER123",
        device_info=DeviceInfo(
            device_type="mobile",
            browser_type="chrome",
            device_os="iOS",
            is_mobile=True,
            device_id="device123",
            ip_address="192.168.1.1"
        )
    )

@pytest.fixture
def custom_rules():
    """Create custom location rules for testing"""
    return LocationRules(
        blocked_countries=["NK", "IR", "CU", "SY"],  # Added Syria
        risk_scores={
            "US": 0.1,  # Low risk
            "GB": 0.2,  # Low risk
            "RU": 0.8,  # Very high risk
            "CN": 0.6,  # Medium-high risk
            "VN": 0.3,  # Medium risk
        },
        velocity_limit=1000.0,
        default_risk_score=0.7,
        high_risk_threshold=0.75
    )

class TestLocationBasedRule:
    """Test cases for LocationBasedRule"""

    def test_safe_location(self, sample_transaction):
        """Test transaction from a safe location (US)"""
        rule = LocationBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.1  # US risk score
        assert "Low risk location" in result.reason
        assert "US (New York)" in result.reason
        assert result.metadata["country"] == "US"
        assert result.metadata["city"] == "New York"
        assert "coordinates" in result.metadata

    def test_medium_risk_location(self, sample_transaction):
        """Test transaction from a medium risk location"""
        sample_transaction.location.country = "DE"  # Germany
        rule = LocationBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.2  # Germany risk score
        assert "Low risk location" in result.reason
        assert "DE" in result.reason

    def test_high_risk_location(self, sample_transaction):
        """Test transaction from a high risk location (Russia)"""
        sample_transaction.location.country = "RU"
        sample_transaction.location.city = "Moscow"
        rule = LocationBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent  # risk_score >= 0.7
        assert result.risk_score == 0.7  # Russia risk score
        assert "High risk location" in result.reason
        assert "RU (Moscow)" in result.reason
        assert result.metadata["error_code"] == ValidationErrorCode.HIGH_RISK_TRANSACTION

    def test_blocked_country(self, sample_transaction):
        """Test transaction from a blocked country"""
        sample_transaction.location.country = "NK"  # North Korea
        rule = LocationBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent
        assert result.risk_score == 1.0
        assert "blocked" in result.reason.lower()
        assert result.metadata["error_code"] == ValidationErrorCode.BLOCKED_LOCATION
        assert result.metadata["country"] == "NK"

    def test_unknown_country(self, sample_transaction):
        """Test transaction from an unknown country"""
        sample_transaction.location.country = "ZZ"  # Non-existent country
        rule = LocationBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent  # default_risk_score >= 0.7
        assert result.risk_score == 0.8  # Default risk score
        assert "Very high risk location" in result.reason
        assert "ZZ" in result.reason
        assert result.metadata["error_code"] == ValidationErrorCode.HIGH_RISK_TRANSACTION

    def test_missing_location(self, sample_transaction):
        """Test transaction with no location information"""
        sample_transaction.location = None
        rule = LocationBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.8  # Default risk score
        assert "No location information" in result.reason
        assert not result.metadata["location_provided"]
        assert result.metadata["default_risk_score"] == 0.8

    def test_missing_city(self, sample_transaction):
        """Test transaction with no city information"""
        sample_transaction.location.city = None
        rule = LocationBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.1  # US risk score
        assert "Low risk location" in result.reason
        assert "US" in result.reason
        assert "city" in result.metadata
        assert result.metadata["city"] is None

    def test_custom_rules(self, sample_transaction, custom_rules):
        """Test rule with custom location rules"""
        sample_transaction.location.country = "VN"  # Vietnam
        rule = LocationBasedRule(rules=custom_rules)
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent  # 0.3 < high_risk_threshold (0.75)
        assert result.risk_score == 0.3  # Custom Vietnam risk score
        assert "Medium risk location" in result.reason
        assert result.metadata["country"] == "VN" 