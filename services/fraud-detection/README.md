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

## Docker

Build image:
```bash
docker build -t fraud-detection-service .
```

Chạy container:
```bash
docker run -d \
  --name fraud-detection \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:29092 \
  -e KAFKA_GROUP_ID=fraud-detection-group \
  fraud-detection-service
```

## Cấu hình

Service có thể được cấu hình thông qua các environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka bootstrap servers (mặc định: localhost:9092)
- `KAFKA_GROUP_ID`: Consumer group ID (mặc định: fraud-detection-group)
- `KAFKA_TRANSACTION_TOPIC`: Topic cho transaction events (mặc định: transactions)
- `KAFKA_FRAUD_ALERT_TOPIC`: Topic cho fraud alerts (mặc định: fraud-alerts)
- `LOG_LEVEL`: Logging level (mặc định: INFO)
- `METRICS_PORT`: Port cho metrics endpoint (mặc định: 8000)

## Phát triển

Chạy tests:
```bash
pytest
```

Chạy linting:
```bash
flake8 src tests
black src tests
mypy src tests
```

## Cấu trúc Project

```
src/
├── config/         # Cài đặt cấu hình
├── core/           # Models và types cốt lõi
├── detection/      # Logic phát hiện gian lận
│   └── rules/     # Các rules riêng lẻ
├── kafka/         # Kafka consumer/producer
└── utils/         # Các hàm tiện ích
```

## Thêm Rules Mới

1. Tạo một class rule mới trong `src/detection/rules/`
2. Kế thừa từ `BaseRule`
3. Implement phương thức `evaluate`
4. Thêm rule vào engine trong `src/detection/engine.py` 