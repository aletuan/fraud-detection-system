from dataclasses import dataclass
from typing import Dict, Optional

from src.core.models import Transaction, RuleResult, ValidationErrorCode
from src.detection.rules.base_rule import BaseRule

@dataclass
class AmountLimits:
    """Configuration for amount limits"""
    max_amount: float
    currency: str
    daily_limit: float
    monthly_limit: float

class AmountBasedRule(BaseRule):
    """Rule for evaluating transaction amounts"""

    def __init__(
        self,
        limits: Optional[AmountLimits] = None,
        weight: float = 0.3  # Amount has 30% weight in risk calculation
    ):
        super().__init__(name="AmountBasedRule", weight=weight)
        self.limits = limits or AmountLimits(
            max_amount=10000.0,
            currency="USD",
            daily_limit=50000.0,
            monthly_limit=200000.0
        )

    def evaluate(self, transaction: Transaction) -> RuleResult:
        if transaction.currency != self.limits.currency:
            return self._create_result(
                is_fraudulent=True,
                risk_score=1.0,
                reason=f"Invalid currency {transaction.currency}. Expected {self.limits.currency}",
                metadata={
                    "error_code": ValidationErrorCode.INVALID_CURRENCY,
                    "expected_currency": self.limits.currency
                }
            )

        # Calculate risk score based on amount ratio
        amount_ratio = transaction.amount / self.limits.max_amount
        risk_score = min(1.0, amount_ratio)

        # Determine if transaction is fraudulent based on amount
        is_fraudulent = transaction.amount > self.limits.max_amount
        reason = self._get_reason(transaction.amount, risk_score)
        
        metadata = {
            "amount_ratio": amount_ratio,
            "max_amount": self.limits.max_amount,
            "currency": self.limits.currency
        }

        if is_fraudulent:
            metadata["error_code"] = ValidationErrorCode.AMOUNT_LIMIT_EXCEEDED

        return self._create_result(
            is_fraudulent=is_fraudulent,
            risk_score=risk_score,
            reason=reason,
            metadata=metadata
        )

    def _get_reason(self, amount: float, risk_score: float) -> str:
        if risk_score >= 0.8:
            return f"Amount {amount} is very high risk"
        elif risk_score >= 0.6:
            return f"Amount {amount} is medium-high risk"
        elif risk_score >= 0.3:
            return f"Amount {amount} is medium risk"
        else:
            return f"Amount {amount} is low risk" 