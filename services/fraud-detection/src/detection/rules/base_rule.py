from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from src.core.models import Transaction, RuleResult

class BaseRule(ABC):
    """Base class for all fraud detection rules"""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight

    @abstractmethod
    def evaluate(self, transaction: Transaction) -> RuleResult:
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
        metadata: Optional[Dict[str, Any]] = None
    ) -> RuleResult:
        """
        Create a RuleResult with the given parameters.
        
        Args:
            is_fraudulent: Whether the transaction is considered fraudulent
            risk_score: The risk score (0.0 to 1.0)
            reason: The reason for the result
            metadata: Additional metadata about the evaluation
            
        Returns:
            RuleResult instance
        """
        return RuleResult(
            rule_name=self.name,
            is_fraudulent=is_fraudulent,
            risk_score=risk_score * self.weight,
            reason=reason,
            metadata=metadata
        ) 