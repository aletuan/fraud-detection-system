import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.core.models import Transaction, Location, DeviceInfo
from src.detection.engine import FraudDetectionEngine, DetectionResult
from src.detection.rules.base_rule import RuleResult
from src.detection.rules import DEFAULT_RULE_WEIGHTS

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
def engine():
    """Create FraudDetectionEngine instance"""
    return FraudDetectionEngine()

class TestFraudDetectionEngine:
    """Test cases for FraudDetectionEngine"""

    def test_initialization(self, engine):
        """Test engine initialization with default rules"""
        assert len(engine.rules) == 4
        rule_types = [type(rule).__name__ for rule in engine.rules]
        assert "MerchantBasedRule" in rule_types
        assert "DeviceBasedRule" in rule_types
        assert "AmountBasedRule" in rule_types
        assert "LocationBasedRule" in rule_types

        # Verify rule weights
        for rule in engine.rules:
            rule_name = rule.__class__.__name__.lower().replace('basedrule', '')
            assert rule.weight == DEFAULT_RULE_WEIGHTS[rule_name]

    def test_safe_transaction(self, engine, sample_transaction):
        """Test evaluation of a safe transaction"""
        result = engine.evaluate_transaction(sample_transaction)
        
        assert isinstance(result, DetectionResult)
        assert not result.is_fraudulent
        assert 0 <= result.risk_score <= 1
        assert len(result.rules_triggered) == 0

    def test_high_risk_transaction(self, engine, sample_transaction):
        """Test evaluation of a high-risk transaction"""
        # Modify transaction to be high risk
        sample_transaction.amount = 50000.00  # High amount
        sample_transaction.metadata["merchant_category"] = "gambling"  # High risk merchant
        sample_transaction.location.country = "RU"  # High risk country
        sample_transaction.device_info.browser_type = "tor"  # Suspicious browser
        
        result = engine.evaluate_transaction(sample_transaction)
        
        assert result.is_fraudulent
        assert result.risk_score > 0.6
        assert len(result.rules_triggered) > 0
        # Check if specific rules were triggered
        assert any("AmountBasedRule" in rule for rule in result.rules_triggered)
        assert any("MerchantBasedRule" in rule for rule in result.rules_triggered)
        assert any("LocationBasedRule" in rule for rule in result.rules_triggered)
        assert any("DeviceBasedRule" in rule for rule in result.rules_triggered)

    def test_single_rule_trigger(self, engine, sample_transaction):
        """Test when only one rule triggers fraud detection"""
        # Only modify device info to trigger DeviceBasedRule
        sample_transaction.device_info.browser_type = "tor"
        
        result = engine.evaluate_transaction(sample_transaction)
        
        assert result.is_fraudulent
        assert len(result.rules_triggered) == 1
        assert "DeviceBasedRule" in result.rules_triggered[0]
        assert "tor" in result.rules_triggered[0].lower()

    def test_weighted_risk_calculation(self, engine, sample_transaction):
        """Test weighted risk score calculation"""
        # Create mock rules with known risk scores
        mock_rule1 = Mock(
            weight=0.4,
            __class__=Mock(__name__="Rule1"),
            evaluate=Mock(return_value=RuleResult(
                risk_score=0.5,
                is_fraudulent=False,
                reason="Test rule 1",
                metadata={"original_risk_score": 0.5}
            ))
        )
        mock_rule2 = Mock(
            weight=0.6,
            __class__=Mock(__name__="Rule2"),
            evaluate=Mock(return_value=RuleResult(
                risk_score=0.8,
                is_fraudulent=True,
                reason="Test rule 2",
                metadata={"original_risk_score": 0.8}
            ))
        )
        
        engine.rules = [mock_rule1, mock_rule2]
        result = engine.evaluate_transaction(sample_transaction)
        
        # Expected weighted risk score: (0.5 * 0.4) + (0.8 * 0.6) = 0.2 + 0.48 = 0.68
        assert result.risk_score == pytest.approx(0.68, abs=1e-2)
        assert result.is_fraudulent
        assert len(result.rules_triggered) == 1
        assert "Rule2: Test rule 2" in result.rules_triggered

    def test_missing_metadata(self, engine, sample_transaction):
        """Test handling of transaction with missing metadata"""
        sample_transaction.metadata = None
        
        result = engine.evaluate_transaction(sample_transaction)
        
        assert isinstance(result, DetectionResult)
        # Should not raise any exceptions
        assert result.risk_score >= 0
        assert isinstance(result.is_fraudulent, bool)
        assert isinstance(result.rules_triggered, list)

    def test_invalid_transaction(self, engine):
        """Test handling of invalid transaction object"""
        with pytest.raises(AttributeError):
            engine.evaluate_transaction(None)
        
        with pytest.raises(AttributeError):
            engine.evaluate_transaction({})

    @patch('logging.Logger.info')
    def test_logging(self, mock_logger, engine, sample_transaction):
        """Test logging of rule evaluation"""
        engine.evaluate_transaction(sample_transaction)
        
        # Verify logging calls
        assert mock_logger.call_count > 0
        # Check if important information is logged
        log_messages = [call.args[0] for call in mock_logger.call_args_list]
        assert any("Rule" in msg for msg in log_messages)
        assert any("Risk score" in msg for msg in log_messages)
        assert any("Final evaluation" in msg for msg in log_messages)

    def test_edge_cases(self, engine, sample_transaction):
        """Test edge cases for transaction evaluation"""
        # Test with minimum amount
        sample_transaction.amount = 0.01
        result = engine.evaluate_transaction(sample_transaction)
        assert not result.is_fraudulent
        
        # Test with very large amount
        sample_transaction.amount = 1000000.00
        result = engine.evaluate_transaction(sample_transaction)
        assert result.is_fraudulent
        
        # Test with empty strings
        sample_transaction.merchant = ""
        sample_transaction.location.city = ""
        result = engine.evaluate_transaction(sample_transaction)
        assert isinstance(result, DetectionResult)

    def test_rule_independence(self, engine, sample_transaction):
        """Test that rules operate independently"""
        # Store original values
        original_result = engine.evaluate_transaction(sample_transaction)
        
        # Modify transaction to trigger each rule individually
        modifications = [
            (lambda t: setattr(t, 'amount', 50000.00), "AmountBasedRule"),
            (lambda t: setattr(t.device_info, 'browser_type', 'tor'), "DeviceBasedRule"),
            (lambda t: setattr(t.location, 'country', 'RU'), "LocationBasedRule"),
            (lambda t: t.metadata.update({'merchant_category': 'gambling'}), "MerchantBasedRule")
        ]
        
        for modify, rule_name in modifications:
            # Create a fresh transaction
            test_transaction = sample_transaction
            # Apply single modification
            modify(test_transaction)
            result = engine.evaluate_transaction(test_transaction)
            
            # Verify only the modified rule was triggered
            triggered_rules = [rule for rule in result.rules_triggered if rule_name in rule]
            assert len(triggered_rules) == 1 