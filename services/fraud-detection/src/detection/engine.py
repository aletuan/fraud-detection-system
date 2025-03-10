from dataclasses import dataclass
from typing import List
from core.models import Transaction
from .rules.base_rule import BaseRule
from .rules.amount_rule import AmountBasedRule
from .rules.device_rule import DeviceBasedRule
from .rules.location_rule import LocationBasedRule
from .rules.merchant_rule import MerchantBasedRule
from .rules import DEFAULT_RULE_WEIGHTS
import logging

logger = logging.getLogger(__name__)

@dataclass
class DetectionResult:
    """Result of fraud detection evaluation
    
    Attributes:
        risk_score: Calculated risk score between 0 and 1
        is_fraudulent: Whether the transaction is considered fraudulent
        rules_triggered: List of rules that flagged the transaction
    """
    risk_score: float
    is_fraudulent: bool
    rules_triggered: List[str]

class FraudDetectionEngine:
    def __init__(self):
        """Initialize fraud detection engine with rules"""
        self.rules = [
            MerchantBasedRule(weight=DEFAULT_RULE_WEIGHTS['merchant']),
            DeviceBasedRule(weight=DEFAULT_RULE_WEIGHTS['device']),
            AmountBasedRule(weight=DEFAULT_RULE_WEIGHTS['amount']),
            LocationBasedRule(weight=DEFAULT_RULE_WEIGHTS['location'])
        ]
    
    def evaluate_transaction(self, transaction: Transaction) -> DetectionResult:
        """Evaluate a transaction for potential fraud
        
        Args:
            transaction: Transaction to evaluate
            
        Returns:
            DetectionResult with risk score and triggered rules
        """
        total_risk_score = 0.0
        triggered_rules = []
        is_fraudulent = False
        
        # Evaluate each rule
        for rule in self.rules:
            result = rule.evaluate(transaction)
            logger.info(
                f"Rule {rule.__class__.__name__} evaluation:\n"
                f"- Risk score: {result.risk_score}\n"
                f"- Original risk score: {result.metadata.get('original_risk_score', result.risk_score)}\n"
                f"- Weight: {rule.weight}\n"
                f"- Is fraudulent: {result.is_fraudulent}\n"
                f"- Reason: {result.reason}\n"
                f"- Metadata: {result.metadata}"
            )
            # Get original risk score before weight was applied
            original_risk_score = result.metadata.get("original_risk_score", result.risk_score)
            # Apply weight here instead of in the rule
            weighted_score = original_risk_score * rule.weight
            total_risk_score += weighted_score
            
            logger.info(
                f"Rule {rule.__class__.__name__} weighted calculation:\n"
                f"- Original risk score: {original_risk_score}\n"
                f"- Weight: {rule.weight}\n"
                f"- Weighted score: {weighted_score}\n"
                f"- Running total: {total_risk_score}"
            )
            
            if result.is_fraudulent:
                is_fraudulent = True
                triggered_rules.append(f"{rule.__class__.__name__}: {result.reason}")
        
        # Calculate final risk score (already weighted)
        final_risk_score = total_risk_score
        
        logger.info(
            f"Final evaluation:\n"
            f"- Total risk score: {final_risk_score}\n"
            f"- Is fraudulent: {is_fraudulent}\n"
            f"- Rules triggered: {triggered_rules}"
        )
        
        return DetectionResult(
            risk_score=final_risk_score,
            is_fraudulent=is_fraudulent,
            rules_triggered=triggered_rules
        ) 