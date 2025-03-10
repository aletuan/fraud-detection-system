import asyncio
import aiohttp
import time
import json
import random
from datetime import datetime
from typing import List, Dict
import logging
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import matplotlib.pyplot as plt
import pytest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8080"
NUM_TRANSACTIONS = 500  # Increased for load testing
CONCURRENT_REQUESTS = 25  # Increased for load testing
TRANSACTION_TYPES = ["SAFE", "MEDIUM_RISK", "HIGH_RISK"]

# Sample data for transactions
MERCHANTS = {
    "SAFE": ["Walmart", "Amazon", "Target", "Costco"],
    "MEDIUM_RISK": ["NewStore", "OnlineShop", "DigitalGoods"],
    "HIGH_RISK": ["CryptoExchange", "GamblingSite", "UnknownMerchant"]
}

LOCATIONS = {
    "SAFE": [
        {"country": "US", "city": "New York"},
        {"country": "GB", "city": "London"},
        {"country": "CA", "city": "Toronto"}
    ],
    "MEDIUM_RISK": [
        {"country": "BR", "city": "Sao Paulo"},
        {"country": "IN", "city": "Mumbai"},
        {"country": "MX", "city": "Mexico City"}
    ],
    "HIGH_RISK": [
        {"country": "RU", "city": "Moscow"},
        {"country": "NG", "city": "Lagos"},
        {"country": "IR", "city": "Tehran"}
    ]
}

DEVICES = {
    "SAFE": [
        {
            "device_type": "mobile",
            "browser_type": "chrome",
            "device_os": "iOS",
            "is_mobile": True
        },
        {
            "device_type": "desktop",
            "browser_type": "firefox",
            "device_os": "Windows",
            "is_mobile": False
        }
    ],
    "MEDIUM_RISK": [
        {
            "device_type": "tablet",
            "browser_type": "opera",
            "device_os": "Android",
            "is_mobile": True
        }
    ],
    "HIGH_RISK": [
        {
            "device_type": "unknown",
            "browser_type": "tor",
            "device_os": "Linux",
            "is_mobile": False
        }
    ]
}

AMOUNTS = {
    "SAFE": (10, 1000),
    "MEDIUM_RISK": (1000, 5000),
    "HIGH_RISK": (5000, 50000)
}

def generate_transaction(risk_type: str) -> Dict:
    """Generate a transaction with specified risk level"""
    amount_range = AMOUNTS[risk_type]
    return {
        "account_id": f"ACC{random.randint(1, 1000)}",
        "amount": round(random.uniform(*amount_range), 2),
        "currency": "USD",
        "type": "DEBIT",
        "reference_id": f"REF{int(time.time() * 1000000)}_{random.randint(1, 1000000)}",
        "merchant_name": random.choice(MERCHANTS[risk_type]),
        "location": random.choice(LOCATIONS[risk_type]),
        "device_info": {
            **random.choice(DEVICES[risk_type]),
            "device_id": f"device{random.randint(1, 1000)}",
            "ip_address": f"192.168.1.{random.randint(1, 255)}"
        }
    }

async def send_transaction(session: aiohttp.ClientSession, transaction: Dict) -> Dict:
    """Send transaction to API and measure response time"""
    start_time = time.time()
    
    try:
        async with session.post(
            f"{BASE_URL}/api/v1/transactions",
            json=transaction
        ) as response:
            response_data = await response.json()
            end_time = time.time()
            
            if response.status in (200, 201):
                return {
                    "transaction_id": response_data.get("id"),
                    "response_time": end_time - start_time,
                    "status": response.status,
                    "risk_score": 0,  # Risk score will be calculated by the fraud detection service
                    "is_fraudulent": False  # This will be determined by the fraud detection service
                }
            else:
                logger.error(f"Error response: {response.status} - {response_data}")
                return {
                    "transaction_id": None,
                    "response_time": end_time - start_time,
                    "status": response.status,
                    "error": str(response_data)
                }
            
    except Exception as e:
        logger.error(f"Error sending transaction: {str(e)}")
        return {
            "transaction_id": None,
            "response_time": time.time() - start_time,
            "status": 500,
            "error": str(e)
        }

async def run_performance_test():
    """Run performance test with concurrent transactions"""
    # Generate mix of transactions
    transactions = []
    for _ in range(NUM_TRANSACTIONS):
        risk_type = random.choices(
            TRANSACTION_TYPES,
            weights=[0.7, 0.2, 0.1]  # 70% safe, 20% medium, 10% high risk
        )[0]
        transactions.append(generate_transaction(risk_type))
    
    results = []
    
    # Send transactions concurrently
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(0, len(transactions), CONCURRENT_REQUESTS):
            batch = transactions[i:i + CONCURRENT_REQUESTS]
            batch_tasks = [
                send_transaction(session, txn)
                for txn in batch
            ]
            
            logger.info(f"Sending batch {i//CONCURRENT_REQUESTS + 1}")
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            
            # Small delay between batches
            await asyncio.sleep(0.1)
    
    return results

def analyze_results(results: List[Dict]) -> Dict:
    """Analyze and visualize test results"""
    df = pd.DataFrame(results)
    
    # Calculate success rate (200 or 201 status codes)
    success_rate = ((df["status"] == 200) | (df["status"] == 201)).mean() * 100
    
    # Basic statistics
    stats = {
        "Total Transactions": len(df),
        "Successful Transactions": len(df[df["status"].isin([200, 201])]),
        "Failed Transactions": len(df[~df["status"].isin([200, 201])]),
        "Success Rate": success_rate,
        "Average Response Time": df["response_time"].mean(),
        "95th Percentile": df["response_time"].quantile(0.95),
        "Max Response Time": df["response_time"].max(),
        "Min Response Time": df["response_time"].min()
    }
    
    logger.info("\nTest Results:")
    for metric, value in stats.items():
        if isinstance(value, float):
            logger.info(f"{metric}: {value:.2f}")
        else:
            logger.info(f"{metric}: {value}")
    
    # Plot response time distribution
    plt.figure(figsize=(10, 6))
    df["response_time"].hist(bins=50)
    plt.title("Response Time Distribution")
    plt.xlabel("Response Time (seconds)")
    plt.ylabel("Count")
    plt.savefig("response_time_distribution.png")
    plt.close()
    
    # Plot concurrent requests over time
    plt.figure(figsize=(10, 6))
    df["timestamp"] = pd.to_datetime(df.index, unit="s")
    df.set_index("timestamp")["response_time"].rolling(window=CONCURRENT_REQUESTS).mean().plot()
    plt.title("Average Response Time Over Time")
    plt.xlabel("Request Sequence")
    plt.ylabel("Response Time (seconds)")
    plt.savefig("response_time_trend.png")
    plt.close()
    
    return stats

@pytest.mark.asyncio
async def test_concurrent_transaction_processing():
    """Test concurrent transaction processing performance"""
    logger.info("Starting performance test...")
    start_time = time.time()
    
    # Run test
    results = await run_performance_test()
    
    # Analyze results
    stats = analyze_results(results)
    
    total_time = time.time() - start_time
    logger.info(f"\nTotal test time: {total_time:.2f} seconds")
    logger.info(f"Average throughput: {NUM_TRANSACTIONS/total_time:.2f} transactions/second")
    
    # Print detailed stats
    logger.info("\nDetailed Statistics:")
    for metric, value in stats.items():
        logger.info(f"{metric}: {value:.2f}")
    
    # Assertions with more lenient thresholds for initial testing
    assert stats["Success Rate"] > 80, "Success rate should be above 80%"
    assert stats["Average Response Time"] < 2.0, "Average response time should be under 2 seconds"
    assert stats["95th Percentile"] < 5.0, "95th percentile response time should be under 5 seconds" 