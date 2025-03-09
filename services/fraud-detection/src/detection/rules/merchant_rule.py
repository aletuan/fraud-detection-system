from dataclasses import dataclass
from typing import List, Dict, Optional

from src.core.models import Transaction, RuleResult, ValidationErrorCode
from src.detection.rules.base_rule import BaseRule

@dataclass
class MerchantRules:
    """Configuration for merchant rules"""
    blocked_categories: List[str]
    risk_scores: Dict[str, float]
    country_risk_scores: Dict[str, float]
    default_risk_score: float = 0.8  # High risk for unknown merchants/categories

class MerchantBasedRule(BaseRule):
    """Rule for evaluating merchant-related risks"""

    def __init__(
        self,
        rules: Optional[MerchantRules] = None,
        weight: float = 0.25  # Merchant has 25% weight in risk calculation
    ):
        super().__init__(name="MerchantBasedRule", weight=weight)
        self.rules = rules or MerchantRules(
            blocked_categories=[
                "gambling",
                "adult",
                "weapons"
            ],
            risk_scores={
                "retail": 0.1,      # Low risk
                "travel": 0.3,      # Low-medium risk
                "electronics": 0.4,  # Medium risk
                "gaming": 0.6       # Medium-high risk
            },
            country_risk_scores={
                "US": 0.1,  # Low risk
                "GB": 0.1,  # Low risk
                "DE": 0.2,  # Low risk
                "FR": 0.2,  # Low risk
                "RU": 0.7,  # High risk
                "CN": 0.6   # Medium-high risk
            }
        )

    def evaluate(self, transaction: Transaction) -> RuleResult:
        # Extract merchant info from transaction
        merchant_category = (transaction.metadata or {}).get("merchant_category", "unknown")
        merchant_country = (transaction.metadata or {}).get("merchant_country", "unknown")
        
        # Check for blocked categories
        if merchant_category in self.rules.blocked_categories:
            return self._create_result(
                is_fraudulent=True,
                risk_score=1.0,
                reason=f"Merchant category '{merchant_category}' is blocked",
                metadata={
                    "error_code": ValidationErrorCode.BLOCKED_MERCHANT,
                    "merchant_category": merchant_category
                }
            )

        # Calculate risk score based on merchant category
        category_risk = self.rules.risk_scores.get(
            merchant_category,
            self.rules.default_risk_score
        )

        # Calculate risk score based on merchant country
        country_risk = self.rules.country_risk_scores.get(
            merchant_country,
            self.rules.default_risk_score
        )

        # Combine risk scores (higher weight on category)
        risk_score = (category_risk * 0.7) + (country_risk * 0.3)
        
        # Determine if transaction is fraudulent based on combined risk
        is_fraudulent = risk_score >= 0.8  # High risk threshold
        reason = self._get_reason(merchant_category, merchant_country, risk_score)
        
        metadata = {
            "merchant_category": merchant_category,
            "merchant_country": merchant_country,
            "category_risk_score": category_risk,
            "country_risk_score": country_risk
        }

        if is_fraudulent:
            metadata["error_code"] = ValidationErrorCode.HIGH_RISK_TRANSACTION

        return self._create_result(
            is_fraudulent=is_fraudulent,
            risk_score=risk_score,
            reason=reason,
            metadata=metadata
        )

    def _get_reason(self, category: str, country: str, risk_score: float) -> str:
        if risk_score >= 0.8:
            return f"Very high risk merchant (category: {category}, country: {country})"
        elif risk_score >= 0.6:
            return f"High risk merchant (category: {category}, country: {country})"
        elif risk_score >= 0.3:
            return f"Medium risk merchant (category: {category}, country: {country})"
        else:
            return f"Low risk merchant (category: {category}, country: {country})" 