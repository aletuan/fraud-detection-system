from dataclasses import dataclass
from typing import List, Dict, Optional

from src.core.models import Transaction, RuleResult, ValidationErrorCode, Location
from src.detection.rules.base_rule import BaseRule
import logging

logger = logging.getLogger(__name__)

@dataclass
class LocationRules:
    """Configuration for location rules"""
    blocked_countries: List[str]
    risk_scores: Dict[str, float]
    velocity_limit: float  # km/h
    default_risk_score: float = 0.8  # High risk for unknown locations
    high_risk_threshold: float = 0.7  # Mark as fraudulent if risk score >= 0.7

class LocationBasedRule(BaseRule):
    """Rule for evaluating location-related risks"""

    def __init__(
        self,
        rules: Optional[LocationRules] = None,
        weight: float = 0.25  # Location has 25% weight in risk calculation
    ):
        super().__init__(name="LocationBasedRule", weight=weight)
        self.rules = rules or LocationRules(
            blocked_countries=[
                "NK",  # North Korea
                "IR",  # Iran
                "CU",  # Cuba
            ],
            risk_scores={
                "US": 0.1,  # USA - Low risk
                "GB": 0.1,  # UK - Low risk
                "DE": 0.2,  # Germany - Low risk
                "FR": 0.2,  # France - Low risk
                "RU": 0.7,  # Russia - High risk
                "CN": 0.6,  # China - Medium-high risk
            },
            velocity_limit=800.0  # km/h
        )

    def evaluate(self, transaction: Transaction) -> RuleResult:
        # Handle missing location
        if not transaction.location:
            logger.warning(f"No location information provided for transaction {transaction.id}")
            return self._create_result(
                is_fraudulent=False,
                risk_score=self.rules.default_risk_score,
                reason="No location information provided",
                metadata={
                    "location_provided": False,
                    "default_risk_score": self.rules.default_risk_score
                }
            )

        logger.info(
            f"Evaluating location for transaction {transaction.id}: "
            f"country={transaction.location.country}, city={transaction.location.city}"
        )

        # Check for blocked countries
        if transaction.location.country in self.rules.blocked_countries:
            logger.warning(
                f"Blocked country detected for transaction {transaction.id}: "
                f"country={transaction.location.country}"
            )
            return self._create_result(
                is_fraudulent=True,
                risk_score=1.0,
                reason=f"Country '{transaction.location.country}' is blocked",
                metadata={
                    "error_code": ValidationErrorCode.BLOCKED_LOCATION,
                    "country": transaction.location.country
                }
            )

        # Calculate location risk score
        risk_score = self.rules.risk_scores.get(
            transaction.location.country,
            self.rules.default_risk_score
        )
        logger.info(
            f"Location risk score for transaction {transaction.id}: {risk_score} "
            f"(country={transaction.location.country})"
        )

        # TODO: Implement velocity check when previous transaction data is available
        # This would require checking the time and distance between consecutive transactions

        # Determine if transaction is fraudulent based on risk score
        is_fraudulent = risk_score >= self.rules.high_risk_threshold
        reason = self._get_reason(transaction.location, risk_score)
        
        metadata = {
            "country": transaction.location.country,
            "city": transaction.location.city,
            "risk_score": risk_score
        }

        if transaction.location.coordinates:
            metadata["coordinates"] = {
                "latitude": transaction.location.coordinates.latitude,
                "longitude": transaction.location.coordinates.longitude
            }

        if is_fraudulent:
            metadata["error_code"] = ValidationErrorCode.HIGH_RISK_TRANSACTION
            logger.warning(
                f"High risk location detected for transaction {transaction.id}: "
                f"country={transaction.location.country}, risk_score={risk_score}"
            )

        return self._create_result(
            is_fraudulent=is_fraudulent,
            risk_score=risk_score,
            reason=reason,
            metadata=metadata
        )

    def _get_reason(self, location: Location, risk_score: float) -> str:
        country_desc = f"{location.country}"
        if location.city:
            country_desc += f" ({location.city})"

        if risk_score >= 0.8:
            return f"Very high risk location: {country_desc}"
        elif risk_score >= 0.6:
            return f"High risk location: {country_desc}"
        elif risk_score >= 0.3:
            return f"Medium risk location: {country_desc}"
        else:
            return f"Low risk location: {country_desc}" 