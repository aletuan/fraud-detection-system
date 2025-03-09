from datetime import datetime
import pytest

from src.core.models import Transaction, TransactionType, TransactionStatus
from src.detection.rules.amount_rule import AmountBasedRule, AmountLimits

@pytest.fixture
def default_rule():
    return AmountBasedRule()

@pytest.fixture
def custom_rule():
    limits = AmountLimits(
        max_amount=5000.0,
        currency="EUR",
        daily_limit=20000.0,
        monthly_limit=100000.0
    )
    return AmountBasedRule(limits=limits, weight=0.4)

def create_transaction(amount: float, currency: str = "USD") -> Transaction:
    return Transaction(
        id="123",
        account_id="ACC123",
        amount=amount,
        currency=currency,
        type=TransactionType.DEBIT,
        status=TransactionStatus.PENDING,
        reference_id="REF123",
        created_at=datetime.utcnow()
    )

def test_evaluate_low_amount(default_rule):
    tx = create_transaction(amount=100.0)
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.01 * 0.3)  # 100/10000 * 0.3 weight
    assert "low risk" in result.reason.lower()
    assert result.metadata["amount_ratio"] == pytest.approx(0.01)

def test_evaluate_medium_amount(default_rule):
    tx = create_transaction(amount=4000.0)
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.4 * 0.3)  # 4000/10000 * 0.3 weight
    assert "medium risk" in result.reason.lower()

def test_evaluate_high_amount(default_rule):
    tx = create_transaction(amount=8000.0)
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.8 * 0.3)  # 8000/10000 * 0.3 weight
    assert "high risk" in result.reason.lower()

def test_evaluate_exceeding_amount(default_rule):
    tx = create_transaction(amount=12000.0)
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.3)  # Capped at 1.0 * 0.3 weight
    assert "very high risk" in result.reason.lower()
    assert result.metadata["error_code"] == "AMOUNT_LIMIT_EXCEEDED"

def test_evaluate_invalid_currency(default_rule):
    tx = create_transaction(amount=1000.0, currency="EUR")
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.3)  # Invalid currency = max risk
    assert "Invalid currency" in result.reason
    assert result.metadata["error_code"] == "INVALID_CURRENCY"

def test_custom_limits(custom_rule):
    # Test with custom currency
    tx = create_transaction(amount=1000.0, currency="EUR")
    result = custom_rule.evaluate(tx)
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.2 * 0.4)  # 1000/5000 * 0.4 weight
    
    # Test exceeding custom limit
    tx = create_transaction(amount=6000.0, currency="EUR")
    result = custom_rule.evaluate(tx)
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.4)  # Capped at 1.0 * 0.4 weight 