from dataclasses import dataclass
from typing import List, Dict, Optional

from src.core.models import Transaction, RuleResult, ValidationErrorCode, DeviceInfo
from src.detection.rules.base_rule import BaseRule

@dataclass
class DeviceRules:
    """Configuration for device rules"""
    blocked_devices: List[str]
    blocked_browsers: List[str]
    blocked_os: List[str]
    risk_scores: Dict[str, float]
    max_devices_per_day: int
    require_mfa: bool = True
    default_risk_score: float = 0.8  # High risk for unknown devices

class DeviceBasedRule(BaseRule):
    """Rule for evaluating device-related risks"""

    def __init__(
        self,
        rules: Optional[DeviceRules] = None,
        weight: float = 0.25  # Device has 25% weight in risk calculation
    ):
        super().__init__(name="DeviceBasedRule", weight=weight)
        self.rules = rules or DeviceRules(
            blocked_devices=[],
            blocked_browsers=[
                "unknown",
                "tor"
            ],
            blocked_os=[
                "unknown"
            ],
            risk_scores={
                "mobile": 0.2,    # Low-medium risk
                "tablet": 0.3,    # Medium risk
                "desktop": 0.1,   # Low risk
                "unknown": 0.9,   # High risk
            },
            max_devices_per_day=3
        )

    def evaluate(self, transaction: Transaction) -> RuleResult:
        # Handle missing device info
        if not transaction.device_info:
            return self._create_result(
                is_fraudulent=False,
                risk_score=self.rules.default_risk_score,
                reason="No device information provided",
                metadata={
                    "device_provided": False,
                    "default_risk_score": self.rules.default_risk_score
                }
            )

        # Check for blocked browser
        if transaction.device_info.browser_type in self.rules.blocked_browsers:
            return self._create_result(
                is_fraudulent=True,
                risk_score=1.0,
                reason=f"Browser type '{transaction.device_info.browser_type}' is blocked",
                metadata={
                    "error_code": ValidationErrorCode.BLOCKED_DEVICE,
                    "browser_type": transaction.device_info.browser_type
                }
            )

        # Check for blocked OS
        if transaction.device_info.device_os in self.rules.blocked_os:
            return self._create_result(
                is_fraudulent=True,
                risk_score=1.0,
                reason=f"Operating system '{transaction.device_info.device_os}' is blocked",
                metadata={
                    "error_code": ValidationErrorCode.BLOCKED_DEVICE,
                    "device_os": transaction.device_info.device_os
                }
            )

        # Calculate device risk score
        device_type = "unknown"
        if transaction.device_info.is_mobile:
            device_type = "mobile"
        elif transaction.device_info.device_type == "tablet":
            device_type = "tablet"
        elif transaction.device_info.device_type == "desktop":
            device_type = "desktop"

        risk_score = self.rules.risk_scores.get(
            device_type,
            self.rules.default_risk_score
        )

        # TODO: Implement device limit per day check
        # This would require checking the number of unique devices used by the account today

        # Determine if transaction is fraudulent based on risk score
        is_fraudulent = risk_score >= 0.8  # High risk threshold
        reason = self._get_reason(transaction.device_info, risk_score)
        
        metadata = {
            "device_type": device_type,
            "browser_type": transaction.device_info.browser_type,
            "device_os": transaction.device_info.device_os,
            "is_mobile": transaction.device_info.is_mobile,
            "risk_score": risk_score
        }

        if transaction.device_info.device_id:
            metadata["device_id"] = transaction.device_info.device_id
        if transaction.device_info.ip_address:
            metadata["ip_address"] = transaction.device_info.ip_address

        if is_fraudulent:
            metadata["error_code"] = ValidationErrorCode.HIGH_RISK_TRANSACTION

        return self._create_result(
            is_fraudulent=is_fraudulent,
            risk_score=risk_score,
            reason=reason,
            metadata=metadata
        )

    def _get_reason(self, device: DeviceInfo, risk_score: float) -> str:
        device_desc = f"{device.device_type} device"
        if device.browser_type and device.device_os:
            device_desc += f" ({device.browser_type} on {device.device_os})"

        if risk_score >= 0.8:
            return f"Very high risk {device_desc}"
        elif risk_score >= 0.6:
            return f"High risk {device_desc}"
        elif risk_score >= 0.3:
            return f"Medium risk {device_desc}"
        else:
            return f"Low risk {device_desc}" 