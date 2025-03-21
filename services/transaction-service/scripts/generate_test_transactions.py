#!/usr/bin/env python3
import json
import random
import requests
import time
from datetime import datetime, timedelta
import uuid
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transaction_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('transaction_test')

# Configuration
TRANSACTION_SERVICE_URL = "http://localhost:8080/api/v1/transactions"
TOTAL_TRANSACTIONS = 100
FRAUD_PERCENTAGE = 0.10  # 10% fraud transactions

# Common merchant data
MERCHANTS = [
    {"id": "MERCH001", "name": "Amazon", "category": "ecommerce", "country": "US"},
    {"id": "MERCH002", "name": "Walmart", "category": "retail", "country": "US"},
    {"id": "MERCH003", "name": "Target", "category": "retail", "country": "US"},
    {"id": "MERCH004", "name": "Best Buy", "category": "electronics", "country": "US"},
    {"id": "MERCH005", "name": "Apple Store", "category": "electronics", "country": "US"}
]

# Device types for simulation
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
BROWSERS = ["chrome", "safari", "firefox", "edge"]
OS_TYPES = ["ios", "android", "windows", "macos"]

class TransactionTracker:
    def __init__(self):
        self.transactions: Dict[str, Dict] = {}  # ref_id -> transaction details
        self.fraud_patterns: Dict[str, List[str]] = {}  # ref_id -> list of fraud patterns
        self.sent_transactions = 0
        self.failed_transactions = 0
        
    def add_transaction(self, transaction: Dict, is_fraud: bool, fraud_pattern: str = None):
        ref_id = transaction['reference_id']
        self.transactions[ref_id] = {
            'transaction': transaction,
            'is_fraud': is_fraud,
            'fraud_pattern': fraud_pattern,
            'amount': transaction['amount'],
            'merchant': transaction['merchant_info']['name'],
            'location': f"{transaction['location']['city']}, {transaction['location']['country']}",
            'device': f"{transaction['device_info']['device_type']} ({transaction['device_info']['browser_type']} on {transaction['device_info']['device_os']})"
        }
        
    def log_transaction_result(self, ref_id: str, response: requests.Response):
        if ref_id in self.transactions:
            self.transactions[ref_id]['response'] = {
                'status_code': response.status_code,
                'response_body': response.text if response.status_code != 201 else 'Success'
            }
            
            if response.status_code == 201:
                self.sent_transactions += 1
                status = "SUCCESS"
            else:
                self.failed_transactions += 1
                status = "FAILED"
            
            tx_info = self.transactions[ref_id]
            if tx_info['is_fraud']:
                logger.info(f"[{status}] Fraudulent Transaction {ref_id}:")
                logger.info(f"  - Pattern: {tx_info['fraud_pattern']}")
            else:
                logger.info(f"[{status}] Normal Transaction {ref_id}")
            
            logger.info(f"  - Amount: ${tx_info['amount']:.2f}")
            logger.info(f"  - Merchant: {tx_info['merchant']}")
            logger.info(f"  - Location: {tx_info['location']}")
            logger.info(f"  - Device: {tx_info['device']}")
            
            if response.status_code != 201:
                logger.error(f"  - Error: {response.text}")
    
    def print_summary(self):
        total_fraud = len([tx for tx in self.transactions.values() if tx['is_fraud']])
        total_normal = len(self.transactions) - total_fraud
        
        logger.info("\n=== Test Summary ===")
        logger.info(f"Total Transactions Generated: {len(self.transactions)}")
        logger.info(f"  - Normal Transactions: {total_normal}")
        logger.info(f"  - Fraudulent Transactions: {total_fraud}")
        logger.info(f"\nTransaction Status:")
        logger.info(f"  - Successfully Sent: {self.sent_transactions}")
        logger.info(f"  - Failed: {self.failed_transactions}")
        
        if total_fraud > 0:
            logger.info("\nFraud Patterns Distribution:")
            patterns = {}
            for tx in self.transactions.values():
                if tx['is_fraud']:
                    pattern = tx['fraud_pattern']
                    patterns[pattern] = patterns.get(pattern, 0) + 1
            
            for pattern, count in patterns.items():
                logger.info(f"  - {pattern}: {count} transactions")

def generate_normal_transaction():
    """Generate a normal, non-fraudulent transaction"""
    merchant = random.choice(MERCHANTS)
    amount = round(random.uniform(10, 1000), 2)
    
    return {
        "account_id": f"ACC{random.randint(1000, 9999)}",
        "amount": amount,
        "currency": "USD",
        "type": random.choice(["DEBIT", "CREDIT"]),
        "reference_id": str(uuid.uuid4()),
        "description": f"Purchase at {merchant['name']}",
        "merchant_info": merchant,
        "location": {
            "country": "US",
            "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
            "ip": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
        },
        "device_info": {
            "device_id": f"DEV{random.randint(10000, 99999)}",
            "device_type": random.choice(DEVICE_TYPES),
            "browser_type": random.choice(BROWSERS),
            "device_os": random.choice(OS_TYPES),
            "is_mobile": random.choice([True, False])
        },
        "metadata": {
            "customer_type": random.choice(["regular", "premium", "new"]),
            "transaction_channel": random.choice(["web", "mobile_app", "pos"])
        }
    }

def generate_fraudulent_transaction():
    """Generate a transaction with fraud patterns"""
    # Start with a normal transaction base
    transaction = generate_normal_transaction()
    
    # Apply one or more fraud patterns
    fraud_pattern = random.choice([
        "high_amount",
        "unusual_location",
        "multiple_countries",
        "suspicious_device",
        "rapid_transactions"
    ])
    
    if fraud_pattern == "high_amount":
        # Unusually high transaction amount
        transaction["amount"] = round(random.uniform(5000, 50000), 2)
    
    elif fraud_pattern == "unusual_location":
        # Transaction from a high-risk country
        high_risk_countries = ["NG", "RU", "CN", "BR"]
        transaction["location"]["country"] = random.choice(high_risk_countries)
        transaction["location"]["city"] = "Unknown"
        transaction["location"]["ip"] = f"103.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    elif fraud_pattern == "multiple_countries":
        # Different countries for merchant and transaction
        transaction["merchant_info"]["country"] = "US"
        transaction["location"]["country"] = random.choice(["GB", "FR", "DE", "JP"])
    
    elif fraud_pattern == "suspicious_device":
        # Suspicious device information
        transaction["device_info"]["device_id"] = f"DEV{random.randint(1, 9999)}"
        transaction["device_info"]["device_type"] = "unknown"
        transaction["device_info"]["browser_type"] = "unknown"
        transaction["device_info"]["device_os"] = "custom"
    
    elif fraud_pattern == "rapid_transactions":
        # Add metadata indicating rapid successive transactions
        transaction["metadata"]["previous_transaction_time"] = (datetime.now() - timedelta(seconds=random.randint(1, 30))).isoformat()
        transaction["metadata"]["transaction_velocity"] = "high"
    
    # Add fraud pattern to metadata for verification
    transaction["metadata"]["fraud_pattern"] = fraud_pattern
    return transaction, fraud_pattern

def send_transaction(transaction: Dict, tracker: TransactionTracker):
    """Send transaction to the transaction service"""
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(TRANSACTION_SERVICE_URL, json=transaction, headers=headers)
        tracker.log_transaction_result(transaction['reference_id'], response)
    except Exception as e:
        logger.error(f"Error sending transaction {transaction['reference_id']}: {str(e)}")
        tracker.failed_transactions += 1

def main():
    logger.info(f"Starting to generate {TOTAL_TRANSACTIONS} transactions ({FRAUD_PERCENTAGE*100}% fraudulent)")
    
    # Initialize transaction tracker
    tracker = TransactionTracker()
    
    # Calculate number of fraudulent transactions
    fraud_count = int(TOTAL_TRANSACTIONS * FRAUD_PERCENTAGE)
    normal_count = TOTAL_TRANSACTIONS - fraud_count
    
    # Generate transactions
    transactions = []
    
    # Generate normal transactions
    for _ in range(normal_count):
        tx = generate_normal_transaction()
        tracker.add_transaction(tx, is_fraud=False)
        transactions.append(tx)
    
    # Generate fraudulent transactions
    for _ in range(fraud_count):
        tx, pattern = generate_fraudulent_transaction()
        tracker.add_transaction(tx, is_fraud=True, fraud_pattern=pattern)
        transactions.append(tx)
    
    # Shuffle transactions to mix fraudulent and normal ones
    random.shuffle(transactions)
    
    # Send transactions with a small delay
    for tx in transactions:
        send_transaction(tx, tracker)
        time.sleep(0.1)  # 100ms delay between transactions
    
    # Print summary
    tracker.print_summary()

if __name__ == "__main__":
    main() 