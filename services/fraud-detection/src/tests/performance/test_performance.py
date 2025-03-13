import pytest
import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Dict
import logging
import uuid
import statistics
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionGenerator:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.transactions = []
        
    def generate_transaction(self, index: int) -> Dict:
        """Generate a transaction with varying risk levels"""
        # Vary amount to test different risk levels
        amount = 1000 + (index % 5) * 2000  # 1000, 3000, 5000, 7000, 9000
        
        # Vary device types and locations
        device_types = ["MOBILE", "DESKTOP", "TABLET"]
        locations = [
            {"country": "US", "city": "New York"},
            {"country": "US", "city": "Los Angeles"},
            {"country": "UK", "city": "London"},
            {"country": "FR", "city": "Paris"}
        ]
        
        # Generate unique reference ID
        unique_id = str(uuid.uuid4())
        
        return {
            "account_id": f"test_account_{index}",
            "amount": amount,
            "currency": "USD",
            "type": "DEBIT",
            "reference_id": f"REF_PERF_{unique_id}",
            "merchant_info": {
                "id": f"SHOP_{index}",
                "name": f"Test Shop {index}",
                "category": "RETAIL",
                "country": locations[index % len(locations)]["country"]
            },
            "location": locations[index % len(locations)],
            "device_info": {
                "device_id": f"DEV_{index}",
                "device_type": device_types[index % len(device_types)],
                "browser_type": "CHROME",
                "device_os": "ANDROID" if device_types[index % len(device_types)] == "MOBILE" else "WINDOWS",
                "is_mobile": device_types[index % len(device_types)] == "MOBILE",
                "ip_address": f"192.168.1.{index}",
                "user_agent": "Mozilla/5.0"
            }
        }
    
    def send_transaction(self, transaction: Dict) -> Dict:
        """Send a single transaction to the API"""
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/transactions",
                json=transaction,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            processing_time = time.time() - start_time
            return {
                "success": True,
                "data": response.json(),
                "processing_time": processing_time,
                "amount": transaction["amount"],
                "device_type": transaction["device_info"]["device_type"],
                "location": transaction["location"]["country"]
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending transaction {transaction['reference_id']}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "amount": transaction["amount"],
                "device_type": transaction["device_info"]["device_type"],
                "location": transaction["location"]["country"]
            }

class PerformanceTest:
    def __init__(self, num_transactions: int = 1000, max_workers: int = 50):
        self.num_transactions = num_transactions
        self.max_workers = max_workers
        self.generator = TransactionGenerator()
        self.start_time = None
        self.end_time = None
        self.results = []
        
    def analyze_results(self):
        """Analyze test results and generate detailed metrics"""
        successful = [r for r in self.results if r["success"]]
        failed = [r for r in self.results if not r["success"]]
        
        # Calculate processing times
        processing_times = [r["processing_time"] for r in successful]
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        p95_processing_time = statistics.quantiles(processing_times, n=20)[-1] if processing_times else 0
        
        # Group by amount ranges
        amount_ranges = defaultdict(int)
        for r in successful:
            amount = r["amount"]
            if amount < 3000:
                amount_ranges["0-3000"] += 1
            elif amount < 5000:
                amount_ranges["3000-5000"] += 1
            elif amount < 7000:
                amount_ranges["5000-7000"] += 1
            else:
                amount_ranges["7000+"] += 1
        
        # Group by device type
        device_stats = defaultdict(int)
        for r in successful:
            device_stats[r["device_type"]] += 1
            
        # Group by location
        location_stats = defaultdict(int)
        for r in successful:
            location_stats[r["location"]] += 1
        
        return {
            "total_transactions": self.num_transactions,
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / self.num_transactions * 100,
            "avg_processing_time": avg_processing_time,
            "p95_processing_time": p95_processing_time,
            "amount_distribution": dict(amount_ranges),
            "device_distribution": dict(device_stats),
            "location_distribution": dict(location_stats)
        }
        
    def run(self):
        """Run the performance test"""
        logger.info(f"Starting performance test with {self.num_transactions} transactions")
        self.start_time = time.time()
        
        # Generate transactions
        transactions = [
            self.generator.generate_transaction(i)
            for i in range(self.num_transactions)
        ]
        
        # Send transactions concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            self.results = list(executor.map(self.generator.send_transaction, transactions))
        
        self.end_time = time.time()
        
        # Calculate metrics
        duration = self.end_time - self.start_time
        metrics = self.analyze_results()
        
        # Log results
        logger.info("\nPerformance Test Results:")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Transactions per second: {self.num_transactions/duration:.2f}")
        logger.info(f"Success rate: {metrics['success_rate']:.2f}%")
        logger.info(f"Average processing time: {metrics['avg_processing_time']*1000:.2f}ms")
        logger.info(f"P95 processing time: {metrics['p95_processing_time']*1000:.2f}ms")
        
        logger.info("\nAmount Distribution:")
        for range_name, count in metrics['amount_distribution'].items():
            logger.info(f"{range_name} USD: {count} transactions")
            
        logger.info("\nDevice Distribution:")
        for device, count in metrics['device_distribution'].items():
            logger.info(f"{device}: {count} transactions")
            
        logger.info("\nLocation Distribution:")
        for location, count in metrics['location_distribution'].items():
            logger.info(f"{location}: {count} transactions")
        
        return metrics

def test_performance():
    """Test the system performance with high load"""
    # Run test with 1000 transactions and 50 concurrent workers
    test = PerformanceTest(num_transactions=1000, max_workers=50)
    results = test.run()
    
    # Basic assertions
    assert results["success_rate"] > 95, "Success rate too low"
    assert results["avg_processing_time"] < 1.0, "Average processing time too high"
    assert results["p95_processing_time"] < 2.0, "P95 processing time too high"
    
    # Check transaction distribution
    total_transactions = sum(results["amount_distribution"].values())
    assert total_transactions == results["successful"], "Transaction count mismatch"
    
    # Log detailed results
    logger.info("\nDetailed Results:")
    logger.info(f"Total transactions: {results['total_transactions']}")
    logger.info(f"Successful: {results['successful']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info(f"Success rate: {results['success_rate']:.2f}%")
    logger.info(f"Average processing time: {results['avg_processing_time']*1000:.2f}ms")
    logger.info(f"P95 processing time: {results['p95_processing_time']*1000:.2f}ms")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 