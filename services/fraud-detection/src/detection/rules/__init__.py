"""
Detection Rules Module

Collection of rules for fraud detection:
- Base Rule: Abstract base class for all rules
- Amount Rule: Transaction amount validation
- Device Rule: Device-based risk assessment
- Location Rule: Geographic risk assessment
- Merchant Rule: Merchant-based risk assessment
"""

# Rule weights configuration
DEFAULT_RULE_WEIGHTS = {
    'amount': 0.25,
    'device': 0.25,
    'location': 0.25,
    'merchant': 0.25
} 