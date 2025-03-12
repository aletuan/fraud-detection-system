# Fraud Detection Service

Dịch vụ phát hiện gian lận theo thời gian thực, phân tích các giao dịch và phát hiện các hành vi gian lận tiềm ẩn bằng cách sử dụng phương pháp rule-based và machine learning.

## Tính năng

- Phân tích giao dịch theo thời gian thực
- Phát hiện gian lận dựa trên rules
- Tích hợp Kafka để xử lý events
- Rule engine có khả năng mở rộng
- Metrics và monitoring
- Structured logging

## Cài đặt

### Yêu cầu
- Python 3.8+
- Apache Kafka
- Redis
- Docker và Docker Compose

### Sử dụng Docker Compose (Recommended)

1. Clone repository:
```bash
git clone https://github.com/your-repo/fraud-detection-system.git
cd fraud-detection-system
```

2. Start services:
```bash
docker-compose up -d
```

3. Kiểm tra service đã hoạt động:
```bash
curl http://localhost:8000/health
```

### Development Setup

1. Tạo Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # hoặc `venv\Scripts\activate` trên Windows
```

2. Cài đặt các dependencies:
```bash
pip install -r requirements.txt
```

3. Chạy service:
```bash
python src/main.py
```

## API Endpoints

### Validate Transaction
```bash
curl -X POST http://localhost:8000/api/v1/validate \
-H "Content-Type: application/json" \
-d '{
  "transaction_id": "123",
  "account_id": "ACC123",
  "amount": 1000.00,
  "currency": "USD",
  "merchant_info": {
    "id": "MERCH001",
    "category": "retail"
  },
  "location": {
    "country": "US",
    "city": "New York"
  },
  "device_info": {
    "type": "mobile",
    "browser": "chrome"
  }
}'
```

### Get Risk Score
```bash
curl http://localhost:8000/api/v1/risk-score/{transaction_id}
```

## Cấu hình

Service có thể được cấu hình thông qua các environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka bootstrap servers (mặc định: localhost:9092)
- `KAFKA_GROUP_ID`: Consumer group ID (mặc định: fraud-detection-group)
- `KAFKA_TRANSACTION_TOPIC`: Topic cho transaction events (mặc định: transactions)
- `KAFKA_FRAUD_ALERT_TOPIC`: Topic cho fraud alerts (mặc định: fraud-alerts)
- `REDIS_HOST`: Redis host (mặc định: localhost)
- `REDIS_PORT`: Redis port (mặc định: 6379)
- `LOG_LEVEL`: Logging level (mặc định: INFO)
- `METRICS_PORT`: Port cho metrics endpoint (mặc định: 8000)

## Cấu trúc Project

```
src/
├── config/         # Cài đặt cấu hình
├── core/           # Models và types cốt lõi
├── detection/      # Logic phát hiện gian lận
│   └── rules/     # Các rules riêng lẻ
├── kafka/         # Kafka consumer/producer
└── utils/         # Các hàm tiện ích

docs/              # Tài liệu của service
└── implementation_plan.md  # Kế hoạch triển khai
```

## Tài liệu

- [Risk Score Calculation](../../docs/risk_score_calculation.md) - Chi tiết về cách tính điểm rủi ro
- [Implementation Plan](docs/implementation_plan.md) - Kế hoạch triển khai và roadmap
- [Operations Guide](../../docs/operations-guide.md) - Hướng dẫn vận hành, troubleshooting và bảo trì hệ thống

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics
```bash
curl http://localhost:8000/metrics
```

## Development

### Testing
```bash
# Run test cases for engine
PYTHONPATH=src python -m pytest src/detection/tests/test_engine.py -v

# Run test cases for engine's rules
PYTHONPATH=src python -m pytest src/detection/rules/tests/ -v

# Core and kafka test
PYTHONPATH=src python -m pytest src/core/tests/ src/kafka/tests/ -v

# Health test
PYTHONPATH=src python -m pytest src/tests/test_api.py -v

# Metric test
PYTHONPATH=src python -m pytest src/tests/test_metrics.py -v

```

### Linting và Formatting
```bash
# Linting
flake8 src tests
mypy src tests

# Formatting
black src tests
```

### Thêm Rules Mới

1. Tạo một class rule mới trong `src/detection/rules/`
2. Kế thừa từ `BaseRule`
3. Implement phương thức `evaluate`
4. Thêm rule vào engine trong `src/detection/engine.py`
5. Tham khảo [Risk Score Calculation](../../docs/risk_score_calculation.md)

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Create pull request

## License

MIT 