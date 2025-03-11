#!/bin/bash

echo "=== Starting Fraud Detection System Test Suite ==="

# Function to check if a service is healthy
check_service_health() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    echo "Checking health of $service..."
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy"; then
            echo "$service is healthy!"
            return 0
        fi
        echo "Waiting for $service to be healthy... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "Error: $service failed to become healthy"
    return 1
}

# Step 1: Build services
echo "=== Building services ==="
docker-compose build

# Step 2: Stop existing services
echo "=== Stopping existing services ==="
docker-compose down

# Step 3: Start services
echo "=== Starting services ==="
docker-compose up -d

# Step 4: Wait for services to be healthy
echo "=== Waiting for services to be healthy ==="
check_service_health "elasticsearch" || exit 1
check_service_health "kafka" || exit 1
check_service_health "zookeeper" || exit 1
check_service_health "mongodb" || exit 1
check_service_health "redis" || exit 1
check_service_health "fraud-detection" || exit 1
check_service_health "transaction-service" || exit 1

# Step 5: Run unit tests
echo "=== Running unit tests ==="
cd services/fraud-detection
python -m pytest src/detection/rules/tests/ src/detection/tests/ src/core/tests/ -v --cov=src

# Step 6: Run performance tests
echo "=== Running performance tests ==="
cd services/fraud-detection 2>/dev/null || true  # Try to cd again, ignore if already there
python src/tests/performance/run_performance_tests.py

echo "=== Test Suite Completed ===" 