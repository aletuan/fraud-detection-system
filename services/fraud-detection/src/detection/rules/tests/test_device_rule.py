import pytest
from datetime import datetime

from src.core.models import Transaction, Location, DeviceInfo, ValidationErrorCode
from src.detection.rules.device_rule import DeviceBasedRule, DeviceRules

@pytest.fixture
def sample_transaction():
    """Create a sample transaction for testing"""
    return Transaction(
        id="test_id",
        amount=100.00,
        currency="USD",
        merchant="Test Store",
        location=Location(country="US", city="New York"),
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
    """Create custom device rules for testing"""
    return DeviceRules(
        blocked_devices=["blacklisted_device"],
        blocked_browsers=["tor", "unknown", "opera"],
        blocked_os=["unknown", "linux"],
        risk_scores={
            "mobile": 0.3,    # Medium risk
            "tablet": 0.4,    # Medium risk
            "desktop": 0.2,   # Low risk
            "unknown": 0.9,   # High risk
        },
        max_devices_per_day=2,
        require_mfa=True,
        default_risk_score=0.8
    )

class TestDeviceBasedRule:
    """Test cases for DeviceBasedRule"""

    def test_safe_mobile_device(self, sample_transaction):
        """Test transaction from a safe mobile device"""
        rule = DeviceBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.2  # Default mobile risk score
        assert "Low risk" in result.reason
        assert "mobile device" in result.reason.lower()
        assert "(chrome on ios)" in result.reason.lower()
        assert result.metadata["device_type"] == "mobile"
        assert result.metadata["browser_type"] == "chrome"
        assert result.metadata["device_os"] == "iOS"

    def test_desktop_device(self, sample_transaction):
        """Test transaction from a desktop device"""
        sample_transaction.device_info.device_type = "desktop"
        sample_transaction.device_info.is_mobile = False
        rule = DeviceBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.1  # Default desktop risk score
        assert "Low risk" in result.reason
        assert "desktop device" in result.reason.lower()

    def test_tablet_device(self, sample_transaction):
        """Test transaction from a tablet device"""
        sample_transaction.device_info.device_type = "tablet"
        sample_transaction.device_info.is_mobile = False
        rule = DeviceBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.3  # Default tablet risk score
        assert "Medium risk" in result.reason
        assert "tablet device" in result.reason.lower()

    def test_blocked_browser(self, sample_transaction):
        """Test transaction with blocked browser (Tor)"""
        sample_transaction.device_info.browser_type = "tor"
        rule = DeviceBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent
        assert result.risk_score == 1.0
        assert "blocked" in result.reason.lower()
        assert result.metadata["error_code"] == ValidationErrorCode.BLOCKED_DEVICE
        assert result.metadata["browser_type"] == "tor"

    def test_blocked_os(self, sample_transaction):
        """Test transaction with blocked OS"""
        sample_transaction.device_info.device_os = "unknown"
        rule = DeviceBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent
        assert result.risk_score == 1.0
        assert "blocked" in result.reason.lower()
        assert result.metadata["error_code"] == ValidationErrorCode.BLOCKED_DEVICE
        assert result.metadata["device_os"] == "unknown"

    def test_unknown_device_type(self, sample_transaction):
        """Test transaction with unknown device type"""
        sample_transaction.device_info.device_type = "unknown"
        sample_transaction.device_info.is_mobile = False
        rule = DeviceBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent  # risk_score >= 0.8
        assert result.risk_score == 0.9  # Default unknown device risk score
        assert "Very high risk" in result.reason
        assert result.metadata["error_code"] == ValidationErrorCode.HIGH_RISK_TRANSACTION

    def test_missing_device_info(self, sample_transaction):
        """Test transaction with no device information"""
        sample_transaction.device_info = None
        rule = DeviceBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.8  # Default risk score
        assert "No device information" in result.reason
        assert not result.metadata["device_provided"]
        assert result.metadata["default_risk_score"] == 0.8

    def test_custom_rules(self, sample_transaction, custom_rules):
        """Test rule with custom device rules"""
        rule = DeviceBasedRule(rules=custom_rules)
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.3  # Custom mobile risk score
        assert "Medium risk" in result.reason
        assert result.metadata["device_type"] == "mobile" 