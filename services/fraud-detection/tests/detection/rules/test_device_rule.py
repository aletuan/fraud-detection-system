from datetime import datetime
import pytest

from src.core.models import Transaction, TransactionType, TransactionStatus, DeviceInfo
from src.detection.rules.device_rule import DeviceBasedRule, DeviceRules

@pytest.fixture
def default_rule():
    return DeviceBasedRule()

@pytest.fixture
def custom_rule():
    rules = DeviceRules(
        blocked_devices=["test_device"],
        blocked_browsers=["firefox", "safari"],
        blocked_os=["linux"],
        risk_scores={
            "mobile": 0.3,
            "desktop": 0.2,
            "tablet": 0.4
        },
        max_devices_per_day=5,
        default_risk_score=0.9
    )
    return DeviceBasedRule(rules=rules, weight=0.35)

def create_transaction(
    device_type: str = None,
    browser_type: str = None,
    device_os: str = None,
    is_mobile: bool = False,
    device_id: str = None,
    ip_address: str = None
) -> Transaction:
    device_info = None
    if device_type or browser_type or device_os:
        device_info = DeviceInfo(
            device_type=device_type or "unknown",
            browser_type=browser_type or "unknown",
            device_os=device_os or "unknown",
            is_mobile=is_mobile,
            device_id=device_id,
            ip_address=ip_address
        )

    return Transaction(
        id="123",
        account_id="ACC123",
        amount=1000.0,
        currency="USD",
        type=TransactionType.DEBIT,
        status=TransactionStatus.PENDING,
        reference_id="REF123",
        created_at=datetime.utcnow(),
        device_info=device_info
    )

def test_evaluate_no_device(default_rule):
    tx = create_transaction()
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.8 * 0.25)  # Default score * weight
    assert "No device information" in result.reason
    assert not result.metadata["device_provided"]

def test_evaluate_low_risk_device(default_rule):
    tx = create_transaction(
        device_type="desktop",
        browser_type="chrome",
        device_os="windows",
        is_mobile=False
    )
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.1 * 0.25)  # Desktop risk score * weight
    assert "low risk" in result.reason.lower()
    assert result.metadata["device_type"] == "desktop"
    assert result.metadata["browser_type"] == "chrome"
    assert result.metadata["device_os"] == "windows"

def test_evaluate_mobile_device(default_rule):
    tx = create_transaction(
        device_type="mobile",
        browser_type="chrome",
        device_os="ios",
        is_mobile=True
    )
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.2 * 0.25)  # Mobile risk score * weight
    assert "mobile device" in result.reason.lower()

def test_evaluate_blocked_browser(default_rule):
    tx = create_transaction(
        device_type="desktop",
        browser_type="tor",
        device_os="linux"
    )
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.25)  # Blocked browser = max risk
    assert "blocked" in result.reason.lower()
    assert result.metadata["error_code"] == "BLOCKED_DEVICE"

def test_evaluate_blocked_os(default_rule):
    tx = create_transaction(
        device_type="desktop",
        browser_type="chrome",
        device_os="unknown"
    )
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.25)  # Blocked OS = max risk
    assert "blocked" in result.reason.lower()
    assert result.metadata["error_code"] == "BLOCKED_DEVICE"

def test_evaluate_unknown_device(default_rule):
    tx = create_transaction(
        device_type="unknown",
        browser_type="chrome",
        device_os="windows"
    )
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(0.9 * 0.25)  # Unknown device risk score * weight
    assert result.metadata["device_type"] == "unknown"

def test_evaluate_with_device_details(default_rule):
    tx = create_transaction(
        device_type="mobile",
        browser_type="chrome",
        device_os="ios",
        is_mobile=True,
        device_id="device123",
        ip_address="192.168.1.1"
    )
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert "device_id" in result.metadata
    assert result.metadata["device_id"] == "device123"
    assert result.metadata["ip_address"] == "192.168.1.1"

def test_custom_rules(custom_rule):
    # Test custom blocked browser
    tx = create_transaction(
        device_type="desktop",
        browser_type="firefox",
        device_os="windows"
    )
    result = custom_rule.evaluate(tx)
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.35)
    assert result.metadata["error_code"] == "BLOCKED_DEVICE"
    
    # Test custom risk scores
    tx = create_transaction(
        device_type="mobile",
        browser_type="chrome",
        device_os="android",
        is_mobile=True
    )
    result = custom_rule.evaluate(tx)
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.3 * 0.35)
    
    # Test custom default score
    tx = create_transaction(
        device_type="unknown",
        browser_type="chrome",
        device_os="windows"
    )
    result = custom_rule.evaluate(tx)
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(0.9 * 0.35) 