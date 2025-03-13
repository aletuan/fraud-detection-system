import pytest
from datetime import datetime

from src.core.models import Transaction, Location, DeviceInfo
from src.detection.rules.amount_rule import AmountBasedRule, AmountLimits

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
def custom_limits():
    """Create custom amount limits for testing"""
    return AmountLimits(
        max_amount=5000.0,
        currency="USD",
        daily_limit=10000.0,
        monthly_limit=50000.0
    )

class TestAmountBasedRule:
    """Test cases for AmountBasedRule"""

    def test_low_amount_transaction(self, sample_transaction):
        """Test transaction with low amount (safe case)"""
        rule = AmountBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score < 0.3
        assert "low risk" in result.reason.lower()
        assert result.metadata["amount_ratio"] == pytest.approx(0.01)  # 100/10000

    def test_medium_amount_transaction(self, sample_transaction):
        """Test transaction with medium amount"""
        sample_transaction.amount = 3000.00
        rule = AmountBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.3  # 3000/10000 = 0.3
        assert "medium risk" in result.reason.lower()
        assert result.metadata["amount_ratio"] == pytest.approx(0.3)

    def test_high_amount_transaction(self, sample_transaction):
        """Test transaction with high amount"""
        sample_transaction.amount = 7000.00
        rule = AmountBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.7  # 7000/10000 = 0.7
        assert "medium-high risk" in result.reason.lower()
        assert result.metadata["amount_ratio"] == pytest.approx(0.7)

    def test_very_high_amount_transaction(self, sample_transaction):
        """Test transaction with very high amount (above limit)"""
        sample_transaction.amount = 12000.00
        rule = AmountBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent
        assert result.risk_score == 1.0  # min(12000/10000, 1.0) = 1.0
        assert "very high risk" in result.reason.lower()
        assert result.metadata["amount_ratio"] > 1.0

    def test_invalid_currency(self, sample_transaction):
        """Test transaction with invalid currency"""
        sample_transaction.currency = "EUR"
        rule = AmountBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent
        assert result.risk_score == 1.0
        assert "Invalid currency" in result.reason
        assert result.metadata["error_code"].value == "INVALID_CURRENCY"

    def test_custom_limits(self, sample_transaction, custom_limits):
        """Test rule with custom amount limits"""
        sample_transaction.amount = 4000.00
        rule = AmountBasedRule(limits=custom_limits)
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        assert result.risk_score == 0.8  # 4000/5000 = 0.8
        assert "very high risk" in result.reason.lower()
        assert result.metadata["max_amount"] == 5000.0 