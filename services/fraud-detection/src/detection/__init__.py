"""
Fraud Detection Module

Core fraud detection functionality including:
- Detection Engine: Main engine for evaluating transactions
- Detection Rules: Set of rules for risk assessment
  - Amount-based rules
  - Device-based rules
  - Location-based rules
  - Merchant-based rules
"""

from .rules.base_rule import BaseRule, RuleResult
from .rules.amount_rule import AmountBasedRule
from .rules.device_rule import DeviceBasedRule
from .rules.location_rule import LocationBasedRule
from .rules.merchant_rule import MerchantBasedRule
from .engine import FraudDetectionEngine, DetectionResult

__all__ = [
    'FraudDetectionEngine',
    'DetectionResult',
    'BaseRule',
    'RuleResult',
    'AmountBasedRule',
    'DeviceBasedRule',
    'LocationBasedRule',
    'MerchantBasedRule'
]

# Default risk thresholds
DEFAULT_FRAUD_THRESHOLD = 0.7
DEFAULT_HIGH_RISK_THRESHOLD = 0.5 