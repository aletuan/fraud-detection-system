# Fraud Detection System

Hệ thống phát hiện gian lận giao dịch theo thời gian thực sử dụng kiến trúc Microservices và Event-Driven.

## Kiến trúc hệ thống

Hệ thống bao gồm các thành phần chính sau:

1. **Transaction Service** (Go)
   - Thu thập và xử lý các sự kiện giao dịch
   - Gửi dữ liệu vào Kafka

2. **Fraud Detection Service** (Python)
   - Sử dụng ML/AI để phát hiện gian lận
   - Xử lý dữ liệu từ Kafka
   - Phân tích theo thời gian thực

3. **Security Alert Service** (Kotlin)
   - Xử lý cảnh báo bảo mật
   - Quản lý các quy tắc phát hiện gian lận
   - Tích hợp với notification service

4. **Notification Service** (NodeJS)
   - Gửi thông báo qua email/SMS
   - Quản lý template thông báo
   - Theo dõi trạng thái gửi thông báo

5. **Realtime Processor** (Rust)
   - Xử lý dữ liệu theo thời gian thực
   - Tối ưu hiệu suất xử lý
   - Tích hợp với dashboard

## Yêu cầu hệ thống

- Docker và Docker Compose
- Go 1.21+
- Python 3.9+
- Kotlin/JDK 17
- Node.js 18+
- Rust 1.70+

## Cài đặt và Chạy

1. Clone repository:
```bash
git clone https://github.com/your-org/fraud-detection-system.git
cd fraud-detection-system
```

2. Khởi động các services cơ bản:
```bash
docker-compose up -d
```

3. Cài đặt dependencies cho từng service:

Transaction Service:
```bash
cd services/transaction-service
go mod download
```

Fraud Detection Service:
```bash
cd services/fraud-detection
python -m venv venv
source venv/bin/activate  # hoặc `venv\Scripts\activate` trên Windows
pip install -r requirements.txt
```

Security Alert Service:
```bash
cd services/security-alert
./gradlew build
```

Notification Service:
```bash
cd services/notification-service
npm install
```

Realtime Processor:
```bash
cd services/realtime-processor
cargo build
```

## Cấu trúc Kafka Topics

- `transactions`: Dữ liệu giao dịch thô
- `fraud-alerts`: Cảnh báo gian lận
- `notifications`: Hàng đợi thông báo
- `transaction-analytics`: Dữ liệu phân tích

## Monitoring và Logging

- Elasticsearch + Kibana cho logging tập trung
- Prometheus + Grafana cho monitoring
- Kafka UI cho việc theo dõi message queue

## API Documentation

Mỗi service đều cung cấp Swagger/OpenAPI documentation tại endpoint `/docs` hoặc `/swagger-ui.html`

## Contributing

Vui lòng đọc [CONTRIBUTING.md](CONTRIBUTING.md) để biết chi tiết về quy trình đóng góp code.

## License

MIT 