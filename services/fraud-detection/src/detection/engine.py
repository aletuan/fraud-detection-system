from dataclasses import dataclass
from typing import List
from core.models import Transaction, RuleResult
from detection.rules.merchant_rule import MerchantBasedRule
from detection.rules.device_rule import DeviceBasedRule
from detection.rules.amount_rule import AmountBasedRule
from detection.rules.location_rule import LocationBasedRule
import logging

logger = logging.getLogger(__name__)

@dataclass
class DetectionResult:
    risk_score: float
    is_fraudulent: bool
    rules_triggered: List[str]

class FraudDetectionEngine:
    def __init__(self):
        """Initialize fraud detection engine with rules"""
        self.rules = [
            MerchantBasedRule(weight=0.25),  # 25% weight
            DeviceBasedRule(weight=0.25),    # 25% weight
            AmountBasedRule(weight=0.25),    # 25% weight
            LocationBasedRule(weight=0.25)    # 25% weight
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
                f"Rule {rule.name} evaluation:\n"
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
                f"Rule {rule.name} weighted calculation:\n"
                f"- Original risk score: {original_risk_score}\n"
                f"- Weight: {rule.weight}\n"
                f"- Weighted score: {weighted_score}\n"
                f"- Running total: {total_risk_score}"
            )
            
            if result.is_fraudulent:
                is_fraudulent = True
                triggered_rules.append(f"{rule.name}: {result.reason}")
        
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