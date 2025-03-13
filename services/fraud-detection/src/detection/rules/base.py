from abc import ABC, abstractmethod
from typing import Dict, Any

from src.core.models import Transaction, RuleResult

class BaseRule(ABC):
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight

    @abstractmethod
    async def evaluate(self, transaction: Transaction) -> RuleResult:
        """
        Evaluate a transaction and return a RuleResult.
        
        Args:
            transaction: The transaction to evaluate
            
        Returns:
            RuleResult containing the evaluation results
        """
        pass

    def _create_result(
        self,
        is_fraudulent: bool,
        risk_score: float,
        reason: str,
        metadata: Dict[str, Any] = None
    ) -> RuleResult:
        return RuleResult(
            rule_name=self.name,
            is_fraudulent=is_fraudulent,
            risk_score=risk_score * self.weight,
            reason=reason,
            metadata=metadata or {}
        ) 