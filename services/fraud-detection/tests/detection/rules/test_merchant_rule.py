from datetime import datetime
import pytest

from src.core.models import Transaction, TransactionType, TransactionStatus
from src.detection.rules.merchant_rule import MerchantBasedRule, MerchantRules

@pytest.fixture
def default_rule():
    return MerchantBasedRule()

@pytest.fixture
def custom_rule():
    rules = MerchantRules(
        blocked_categories=["crypto", "betting"],
        risk_scores={
            "food": 0.1,
            "entertainment": 0.4
        },
        country_risk_scores={
            "SG": 0.1,
            "HK": 0.3
        },
        default_risk_score=0.9
    )
    return MerchantBasedRule(rules=rules, weight=0.35)

def create_transaction(
    merchant_category: str = None,
    merchant_country: str = None
) -> Transaction:
    metadata = {}
    if merchant_category:
        metadata["merchant_category"] = merchant_category
    if merchant_country:
        metadata["merchant_country"] = merchant_country

    return Transaction(
        id="123",
        account_id="ACC123",
        amount=1000.0,
        currency="USD",
        type=TransactionType.DEBIT,
        status=TransactionStatus.PENDING,
        reference_id="REF123",
        created_at=datetime.utcnow(),
        metadata=metadata
    )

def test_evaluate_low_risk_merchant(default_rule):
    tx = create_transaction(merchant_category="retail", merchant_country="US")
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    # (0.1 * 0.7 + 0.1 * 0.3) * 0.25 weight
    assert result.risk_score == pytest.approx(0.1 * 0.25)
    assert "low risk merchant" in result.reason.lower()
    assert result.metadata["category_risk_score"] == 0.1
    assert result.metadata["country_risk_score"] == 0.1

def test_evaluate_medium_risk_merchant(default_rule):
    tx = create_transaction(merchant_category="electronics", merchant_country="FR")
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    # (0.4 * 0.7 + 0.2 * 0.3) * 0.25 weight
    assert result.risk_score == pytest.approx(0.34 * 0.25)
    assert "medium risk merchant" in result.reason.lower()

def test_evaluate_high_risk_merchant(default_rule):
    tx = create_transaction(merchant_category="gaming", merchant_country="RU")
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    # (0.6 * 0.7 + 0.7 * 0.3) * 0.25 weight = 0.83
    assert result.risk_score == pytest.approx(0.83 * 0.25)
    assert "high risk merchant" in result.reason.lower()
    assert result.metadata["error_code"] == "HIGH_RISK_TRANSACTION"

def test_evaluate_blocked_category(default_rule):
    tx = create_transaction(merchant_category="gambling", merchant_country="US")
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.25)
    assert "blocked" in result.reason.lower()
    assert result.metadata["error_code"] == "BLOCKED_MERCHANT"

def test_evaluate_unknown_merchant(default_rule):
    tx = create_transaction()  # No merchant info
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    # (0.8 * 0.7 + 0.8 * 0.3) * 0.25 weight
    assert result.risk_score == pytest.approx(0.8 * 0.25)
    assert result.metadata["merchant_category"] == "unknown"
    assert result.metadata["merchant_country"] == "unknown"

def test_custom_rules(custom_rule):
    # Test custom blocked category
    tx = create_transaction(merchant_category="crypto", merchant_country="SG")
    result = custom_rule.evaluate(tx)
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.35)
    assert result.metadata["error_code"] == "BLOCKED_MERCHANT"
    
    # Test custom risk scores
    tx = create_transaction(merchant_category="food", merchant_country="HK")
    result = custom_rule.evaluate(tx)
    assert not result.is_fraudulent
    # (0.1 * 0.7 + 0.3 * 0.3) * 0.35 weight
    assert result.risk_score == pytest.approx(0.16 * 0.35)
    
    # Test custom default score
    tx = create_transaction(merchant_category="unknown", merchant_country="unknown")
    result = custom_rule.evaluate(tx)
    assert result.is_fraudulent
    # (0.9 * 0.7 + 0.9 * 0.3) * 0.35 weight
    assert result.risk_score == pytest.approx(0.9 * 0.35) 