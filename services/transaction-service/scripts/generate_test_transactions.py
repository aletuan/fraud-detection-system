#!/usr/bin/env python3
import json
import random
import requests
import time
from datetime import datetime, timedelta
import uuid

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
    return transaction

def send_transaction(transaction):
    """Send transaction to the transaction service"""
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(TRANSACTION_SERVICE_URL, json=transaction, headers=headers)
        if response.status_code == 201:
            print(f"Transaction sent successfully: {transaction['reference_id']}")
        else:
            print(f"Failed to send transaction: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending transaction: {str(e)}")

def main():
    print(f"Starting to generate {TOTAL_TRANSACTIONS} transactions ({FRAUD_PERCENTAGE*100}% fraudulent)")
    
    # Calculate number of fraudulent transactions
    fraud_count = int(TOTAL_TRANSACTIONS * FRAUD_PERCENTAGE)
    normal_count = TOTAL_TRANSACTIONS - fraud_count
    
    # Generate and send transactions
    transactions = []
    
    # Generate normal transactions
    for _ in range(normal_count):
        transactions.append(generate_normal_transaction())
    
    # Generate fraudulent transactions
    for _ in range(fraud_count):
        transactions.append(generate_fraudulent_transaction())
    
    # Shuffle transactions to mix fraudulent and normal ones
    random.shuffle(transactions)
    
    # Send transactions with a small delay to avoid overwhelming the service
    for tx in transactions:
        send_transaction(tx)
        time.sleep(0.1)  # 100ms delay between transactions
    
    print(f"\nCompleted sending {TOTAL_TRANSACTIONS} transactions")
    print(f"Normal transactions: {normal_count}")
    print(f"Fraudulent transactions: {fraud_count}")

if __name__ == "__main__":
    main() 