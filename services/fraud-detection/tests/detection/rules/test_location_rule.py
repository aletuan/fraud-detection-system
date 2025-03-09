from datetime import datetime
import pytest

from src.core.models import Transaction, TransactionType, TransactionStatus, Location, Coordinates
from src.detection.rules.location_rule import LocationBasedRule, LocationRules

@pytest.fixture
def default_rule():
    return LocationBasedRule()

@pytest.fixture
def custom_rule():
    rules = LocationRules(
        blocked_countries=["SG", "MY"],
        risk_scores={
            "JP": 0.1,
            "KR": 0.3,
            "VN": 0.5
        },
        velocity_limit=500.0,
        default_risk_score=0.9
    )
    return LocationBasedRule(rules=rules, weight=0.35)

def create_transaction(
    country: str = None,
    city: str = None,
    coordinates: tuple = None
) -> Transaction:
    location = None
    if country:
        location = Location(
            country=country,
            city=city
        )
        if coordinates:
            location.coordinates = Coordinates(
                latitude=coordinates[0],
                longitude=coordinates[1]
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
        location=location
    )

def test_evaluate_no_location(default_rule):
    tx = create_transaction()
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.8 * 0.25)  # Default score * weight
    assert "No location information" in result.reason
    assert not result.metadata["location_provided"]

def test_evaluate_low_risk_location(default_rule):
    tx = create_transaction(country="US", city="New York")
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.1 * 0.25)  # US risk score * weight
    assert "low risk location" in result.reason.lower()
    assert "New York" in result.reason
    assert result.metadata["country"] == "US"
    assert result.metadata["city"] == "New York"

def test_evaluate_high_risk_location(default_rule):
    tx = create_transaction(country="RU", city="Moscow")
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(0.7 * 0.25)  # RU risk score * weight
    assert "high risk location" in result.reason.lower()
    assert result.metadata["error_code"] == "HIGH_RISK_TRANSACTION"

def test_evaluate_blocked_country(default_rule):
    tx = create_transaction(country="NK")
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.25)  # Blocked country = max risk
    assert "blocked" in result.reason.lower()
    assert result.metadata["error_code"] == "BLOCKED_LOCATION"

def test_evaluate_unknown_country(default_rule):
    tx = create_transaction(country="XX")
    result = default_rule.evaluate(tx)
    
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(0.8 * 0.25)  # Default risk score * weight
    assert result.metadata["country"] == "XX"

def test_evaluate_with_coordinates(default_rule):
    tx = create_transaction(
        country="US",
        city="New York",
        coordinates=(40.7128, -74.0060)
    )
    result = default_rule.evaluate(tx)
    
    assert not result.is_fraudulent
    assert "coordinates" in result.metadata
    assert result.metadata["coordinates"]["latitude"] == 40.7128
    assert result.metadata["coordinates"]["longitude"] == -74.0060

def test_custom_rules(custom_rule):
    # Test custom blocked country
    tx = create_transaction(country="SG")
    result = custom_rule.evaluate(tx)
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(1.0 * 0.35)
    assert result.metadata["error_code"] == "BLOCKED_LOCATION"
    
    # Test custom risk scores
    tx = create_transaction(country="JP")
    result = custom_rule.evaluate(tx)
    assert not result.is_fraudulent
    assert result.risk_score == pytest.approx(0.1 * 0.35)
    
    # Test custom default score
    tx = create_transaction(country="XX")
    result = custom_rule.evaluate(tx)
    assert result.is_fraudulent
    assert result.risk_score == pytest.approx(0.9 * 0.35) 