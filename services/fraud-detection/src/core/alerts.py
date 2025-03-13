from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import Transaction

@dataclass
class FraudAlert:
    """Fraud alert data model"""
    transaction_id: str
    user_id: str
    risk_score: float
    rules_triggered: List[str]
    transaction_amount: float
    transaction_currency: str
    merchant: str
    location: Dict[str, str]
    device_info: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_transaction(cls, transaction: Transaction, risk_score: float, rules_triggered: List[str]):
        """Create fraud alert from transaction data"""
        return cls(
            transaction_id=transaction.id,
            user_id=transaction.user_id,
            risk_score=risk_score,
            rules_triggered=rules_triggered,
            transaction_amount=transaction.amount,
            transaction_currency=transaction.currency,
            merchant=transaction.merchant,
            location={
                'country': transaction.location.country,
                'city': transaction.location.city
            },
            device_info={
                'device_type': transaction.device_info.device_type,
                'browser_type': transaction.device_info.browser_type,
                'device_os': transaction.device_info.device_os,
                'is_mobile': transaction.device_info.is_mobile,
                'device_id': transaction.device_info.device_id,
                'ip_address': transaction.device_info.ip_address
            },
            timestamp=transaction.timestamp,
            metadata=transaction.metadata
        ) 