# Transaction Service

Dịch vụ quản lý giao dịch, xử lý và theo dõi các giao dịch tài chính với khả năng tích hợp với các dịch vụ khác thông qua Kafka events.

## Tính năng

- CRUD operations cho giao dịch
- Validation cơ bản cho dữ liệu đầu vào
- Tích hợp với Kafka để gửi transaction events
- Tích hợp với Fraud Detection Service để đánh giá rủi ro
- API RESTful với đầy đủ documentation
- Monitoring và health checks

## API Endpoints

### Create Transaction
```bash
curl -X POST http://localhost:8080/api/v1/transactions \
-H "Content-Type: application/json" \
-d '{
  "account_id": "test123",
  "amount": 1000.00,
  "currency": "USD",
  "type": "DEBIT",
  "reference_id": "TEST_REF_001",
  "description": "Test transaction",
  "merchant_info": {
    "id": "MERCH001",
    "name": "Test Merchant",
    "category": "retail",
    "country": "US"
  },
  "location": {
    "country": "US",
    "city": "New York",
    "ip": "192.168.1.1"
  },
  "device_info": {
    "device_id": "device123",
    "device_type": "mobile",
    "browser_type": "chrome",
    "device_os": "ios",
    "is_mobile": true
  }
}'
```

### Update Transaction Status
```bash
curl -X PUT http://localhost:8080/api/v1/transactions/{id} \
-H "Content-Type: application/json" \
-d '{
  "status": "COMPLETED",
  "description": "Updated description",
  "metadata": {
    "completion_time": "2025-03-09T04:17:02Z"
  }
}'
```

### Get Transaction
```bash
curl http://localhost:8080/api/v1/transactions/{id}
```

### List Transactions
```bash
curl "http://localhost:8080/api/v1/transactions?account_id=test123&status=PENDING&page=1&page_size=10"
```

## Cài đặt

### Yêu cầu
- Go 1.21+
- MongoDB
- Apache Kafka
- Docker và Docker Compose

### Chạy với Docker Compose

1. Clone repository:
```bash
git clone https://github.com/your-repo/fraud-detection-system.git
cd fraud-detection-system
```

2. Start các services:
```bash
docker-compose up -d
```

3. Kiểm tra service đã hoạt động:
```bash
curl http://localhost:8080/health
```

## Testing

### Unit Tests
```bash
cd services/transaction-service
go test ./... -v
```

### Integration Tests với Kafka

1. Tạo một transaction mới:
```bash
curl -X POST http://localhost:8080/api/v1/transactions \
-H "Content-Type: application/json" \
-d '{
  "account_id": "test123",
  "amount": 1000.00,
  "currency": "USD",
  "type": "DEBIT",
  "reference_id": "TEST_REF_001",
  "description": "Test transaction",
  "merchant_info": {
    "id": "MERCH001",
    "name": "Test Merchant",
    "category": "retail",
    "country": "US"
  }
}'
```

2. Kiểm tra event trong Kafka:
```bash
# Sử dụng Kafka Console Consumer
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic transactions \
  --from-beginning \
  --max-messages 1

# Hoặc truy cập Kafka UI: http://localhost:8081
```

## Cấu hình

Service có thể được cấu hình thông qua các environment variables:

- `MONGO_URI`: MongoDB connection string (mặc định: mongodb://localhost:27017)
- `DB_NAME`: Tên database (mặc định: transaction_db)
- `PORT`: Port cho HTTP server (mặc định: 8080)
- `KAFKA_BROKERS`: Kafka bootstrap servers (mặc định: localhost:9092)
- `KAFKA_TOPIC`: Topic cho transaction events (mặc định: transactions)

## Cấu trúc Project

```
services/transaction-service/
├── cmd/                    # Entry points
│   └── main.go            # Main application
├── internal/              # Internal packages
│   ├── api/              # HTTP handlers và middleware
│   ├── domain/           # Domain models và interfaces
│   ├── messaging/        # Kafka integration
│   ├── repository/       # Data access layer
│   └── service/          # Business logic
├── docs/                 # Documentation
└── README.md            # Service documentation
```

## Tài liệu

- [Implementation Plan](../../docs/implementation-plans/transaction-service.md)
- [API Documentation](docs/api.md)
- [Event Schema](docs/events.md)
- [Operations Guide](../../docs/operations-guide.md) - Hướng dẫn vận hành, troubleshooting và bảo trì hệ thống

## Monitoring

### Health Check
```bash
curl http://localhost:8080/health
```

### Metrics
```bash
curl http://localhost:8080/metrics
```

## Development

### Linting và Formatting
```bash
go fmt ./...
go vet ./...
golangci-lint run
```

### Debugging
1. Set up delve debugger
2. Configure IDE (VS Code/GoLand) for debugging
3. Use environment variables for local development

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Create pull request

## License

MIT 