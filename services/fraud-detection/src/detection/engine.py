from dataclasses import dataclass
from typing import List
from ..core.models import Transaction

@dataclass
class DetectionResult:
    risk_score: float
    is_fraudulent: bool
    rules_triggered: List[str]

class FraudDetectionEngine:
    def evaluate_transaction(self, transaction: Transaction) -> DetectionResult:
        """Evaluate a transaction for potential fraud
        
        Args:
            transaction: Transaction to evaluate
            
        Returns:
            DetectionResult with risk score and triggered rules
        """
        # TODO: Implement actual fraud detection logic
        return DetectionResult(
            risk_score=0.1,
            is_fraudulent=False,
            rules_triggered=[]
        ) 