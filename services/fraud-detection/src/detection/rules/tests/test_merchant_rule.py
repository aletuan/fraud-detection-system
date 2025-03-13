import pytest
from datetime import datetime

from src.core.models import Transaction, Location, DeviceInfo, ValidationErrorCode
from src.detection.rules.merchant_rule import MerchantBasedRule, MerchantRules

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
        ),
        metadata={
            "merchant_category": "retail",
            "merchant_country": "US"
        }
    )

@pytest.fixture
def custom_rules():
    """Create custom merchant rules for testing"""
    return MerchantRules(
        blocked_categories=[
            "gambling",
            "adult",
            "weapons",
            "crypto"  # Added crypto
        ],
        risk_scores={
            "retail": 0.1,      # Low risk
            "travel": 0.4,      # Medium risk
            "electronics": 0.5,  # Medium risk
            "gaming": 0.7,      # High risk
            "forex": 0.8        # Very high risk
        },
        country_risk_scores={
            "US": 0.1,  # Low risk
            "GB": 0.2,  # Low risk
            "VN": 0.3,  # Low-medium risk
            "RU": 0.8,  # High risk
            "IR": 0.9   # Very high risk
        },
        default_risk_score=0.7,
        high_risk_threshold=0.65
    )

class TestMerchantBasedRule:
    """Test cases for MerchantBasedRule"""

    def test_safe_merchant(self, sample_transaction):
        """Test transaction with safe merchant (retail in US)"""
        rule = MerchantBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        # Risk score = (0.1 * 0.7) + (0.1 * 0.3) = 0.1
        assert pytest.approx(result.risk_score) == 0.1
        assert "Low risk merchant" in result.reason
        assert "retail" in result.reason
        assert "US" in result.reason
        assert result.metadata["merchant_category"] == "retail"
        assert result.metadata["merchant_country"] == "US"
        assert result.metadata["category_risk_score"] == 0.1
        assert result.metadata["country_risk_score"] == 0.1

    def test_medium_risk_merchant(self, sample_transaction):
        """Test transaction with medium risk merchant"""
        sample_transaction.metadata["merchant_category"] = "electronics"
        sample_transaction.metadata["merchant_country"] = "DE"
        rule = MerchantBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert not result.is_fraudulent
        # Risk score = (0.4 * 0.7) + (0.2 * 0.3) = 0.34
        assert pytest.approx(result.risk_score) == 0.34
        assert "Medium risk merchant" in result.reason
        assert "electronics" in result.reason
        assert "DE" in result.reason

    def test_high_risk_merchant(self, sample_transaction):
        """Test transaction with high risk merchant"""
        sample_transaction.metadata["merchant_category"] = "gaming"
        sample_transaction.metadata["merchant_country"] = "RU"
        rule = MerchantBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent  # risk_score >= 0.6
        # Risk score = (0.6 * 0.7) + (0.7 * 0.3) = 0.63
        assert pytest.approx(result.risk_score) == 0.63
        assert "High risk merchant" in result.reason
        assert "gaming" in result.reason
        assert "RU" in result.reason
        assert result.metadata["error_code"] == ValidationErrorCode.HIGH_RISK_TRANSACTION

    def test_blocked_category(self, sample_transaction):
        """Test transaction with blocked merchant category"""
        sample_transaction.metadata["merchant_category"] = "gambling"
        rule = MerchantBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent
        assert result.risk_score == 1.0
        assert "blocked" in result.reason.lower()
        assert result.metadata["error_code"] == ValidationErrorCode.BLOCKED_MERCHANT
        assert result.metadata["merchant_category"] == "gambling"

    def test_unknown_merchant(self, sample_transaction):
        """Test transaction with unknown merchant category and country"""
        sample_transaction.metadata["merchant_category"] = "unknown"
        sample_transaction.metadata["merchant_country"] = "unknown"
        rule = MerchantBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent  # default_risk_score >= 0.6
        # Risk score = (0.8 * 0.7) + (0.8 * 0.3) = 0.8
        assert pytest.approx(result.risk_score) == 0.8
        assert "High risk merchant" in result.reason
        assert result.metadata["error_code"] == ValidationErrorCode.HIGH_RISK_TRANSACTION

    def test_missing_metadata(self, sample_transaction):
        """Test transaction with no merchant metadata"""
        sample_transaction.metadata = None
        rule = MerchantBasedRule()
        result = rule.evaluate(sample_transaction)
        
        assert result.is_fraudulent  # default_risk_score >= 0.6
        assert pytest.approx(result.risk_score) == 0.8
        assert "High risk merchant" in result.reason
        assert result.metadata["merchant_category"] == "unknown"
        assert result.metadata["merchant_country"] == "unknown"

    def test_custom_rules(self, sample_transaction, custom_rules):
        """Test rule with custom merchant rules"""
        sample_transaction.metadata["merchant_category"] = "forex"
        sample_transaction.metadata["merchant_country"] = "VN"
        rule = MerchantBasedRule(rules=custom_rules)
        result = rule.evaluate(sample_transaction)
        
        # Risk score = (0.8 * 0.7) + (0.3 * 0.3) = 0.65
        assert pytest.approx(result.risk_score) == 0.65
        # Since risk_score = high_risk_threshold, it should not be fraudulent
        assert not result.is_fraudulent
        assert "High risk merchant" in result.reason
        assert result.metadata["merchant_category"] == "forex"
        assert result.metadata["merchant_country"] == "VN" 