"""
Core Module

Core components and models for the fraud detection service:
- Transaction: Main transaction model
- Location: Location information model
- DeviceInfo: Device information model
- TransactionType: Transaction type enumeration
- TransactionStatus: Transaction status enumeration
"""

from .models import (
    Transaction,
    Location,
    DeviceInfo,
    TransactionType,
    TransactionStatus,
    Coordinates
)

__all__ = [
    'Transaction',
    'Location',
    'DeviceInfo',
    'TransactionType',
    'TransactionStatus',
    'Coordinates'
]

# Default model configurations
DEFAULT_CURRENCY = 'USD'
DEFAULT_STATUS = TransactionStatus.PENDING
DEFAULT_TRANSACTION_TYPE = TransactionType.DEBIT 