from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

class TransactionType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ValidationErrorCode(str, Enum):
    AMOUNT_LIMIT_EXCEEDED = "AMOUNT_LIMIT_EXCEEDED"
    DAILY_LIMIT_EXCEEDED = "DAILY_LIMIT_EXCEEDED"
    MONTHLY_LIMIT_EXCEEDED = "MONTHLY_LIMIT_EXCEEDED"
    INVALID_CURRENCY = "INVALID_CURRENCY"
    INVALID_TIME = "INVALID_TIME"
    BLOCKED_MERCHANT = "BLOCKED_MERCHANT"
    BLOCKED_LOCATION = "BLOCKED_LOCATION"
    VELOCITY_LIMIT_EXCEEDED = "VELOCITY_LIMIT_EXCEEDED"
    BLOCKED_DEVICE = "BLOCKED_DEVICE"
    DEVICE_LIMIT_EXCEEDED = "DEVICE_LIMIT_EXCEEDED"
    HIGH_RISK_TRANSACTION = "HIGH_RISK_TRANSACTION"

# Risk score thresholds
LOW_RISK_THRESHOLD = 0.3
MEDIUM_RISK_THRESHOLD = 0.6
HIGH_RISK_THRESHOLD = 0.8

@dataclass
class Coordinates:
    latitude: float
    longitude: float

@dataclass
class Location:
    country: str
    city: Optional[str] = None
    postal_code: Optional[str] = None
    coordinates: Optional[Coordinates] = None

@dataclass
class DeviceInfo:
    device_type: str
    browser_type: str
    device_os: str
    is_mobile: bool
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class Transaction:
    id: str
    amount: float
    currency: str
    merchant: str
    location: str
    device_id: str
    timestamp: datetime
    status: str
    user_id: str

@dataclass
class ValidationError:
    field: str
    code: ValidationErrorCode
    message: str
    details: Optional[str] = None

@dataclass
class RuleResult:
    rule_name: str
    is_fraudulent: bool
    risk_score: float
    reason: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class DetectionResult:
    transaction_id: str
    is_fraudulent: bool
    risk_score: float
    triggered_rules: List[RuleResult]
    errors: Optional[List[ValidationError]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.utcnow() 