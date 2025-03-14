# Hệ Thống Phát Hiện Gian Lận

Hệ thống phát hiện gian lận giao dịch theo thời gian thực được xây dựng trên nền tảng Microservices và Event-Driven Architecture.

## Kế Hoạch Triển Khai Chi Tiết

Để hiểu rõ hơn về cách triển khai từng dịch vụ trong hệ thống, chúng tôi đã chuẩn bị các tài liệu chi tiết sau:

- [Dịch Vụ Phát Hiện Gian Lận](docs/implementation-plans/fraud-detection-service.md): Chi tiết về cách triển khai các quy tắc phát hiện gian lận, xử lý luồng sự kiện và tích hợp với các dịch vụ khác.
- [Dịch Vụ Quản Lý Giao Dịch](docs/implementation-plans/transaction-service.md): Mô tả chi tiết về cách xử lý giao dịch, quản lý dữ liệu và tích hợp với Kafka.
- [Dịch Vụ Phân Tích và Bảng Điều Khiển](docs/implementation-plans/dashboard-analytics-service.md): Hướng dẫn triển khai hệ thống phân tích thời gian thực và xây dựng bảng điều khiển.
- [Dịch Vụ Thông Báo Khách Hàng](docs/implementation-plans/customer-notification-service.md): Chi tiết về cách triển khai hệ thống thông báo đa kênh.
- [Dịch Vụ Cảnh Báo Bảo Mật](docs/implementation-plans/security-alert-service.md): Mô tả cách xử lý và quản lý các cảnh báo bảo mật.

Ngoài ra, chúng tôi cũng cung cấp:
- [Hướng Dẫn Vận Hành](docs/operations-guide.md): Hướng dẫn chi tiết về cách vận hành và bảo trì hệ thống.
- [Tính Toán Điểm Rủi Ro](docs/risk_score_calculation.md): Tài liệu chi tiết về cách tính toán điểm rủi ro cho các giao dịch.

## Kiến Trúc Hệ Thống

Hệ thống bao gồm các thành phần chính sau:

### 1. Dịch Vụ Quản Lý Giao Dịch (Transaction Service - Go)
Chịu trách nhiệm xử lý và quản lý toàn bộ vòng đời của giao dịch:

**Chức năng cốt lõi:**
- Các thao tác CRUD với giao dịch trên MongoDB
- Kiểm tra tính hợp lệ của dữ liệu đầu vào
- Quản lý trạng thái giao dịch
- Xử lý trùng lặp thông qua mã tham chiếu
- Phân trang và lọc dữ liệu giao dịch

**Xử lý dữ liệu:**
- Bổ sung và chuẩn hóa dữ liệu
- Quản lý thời gian và metadata
- Chuẩn hóa dữ liệu vị trí
- Kiểm tra và định dạng tiền tệ

**Phát hành sự kiện:**
- Đẩy các sự kiện giao dịch vào Kafka
- Đảm bảo việc gửi sự kiện thành công
- Kiểm tra tính hợp lệ của cấu trúc sự kiện
- Cập nhật trạng thái giao dịch

**Giao diện API:**
- API RESTful cho quản lý giao dịch
- API truy vấn lịch sử giao dịch
- Hỗ trợ xử lý hàng loạt
- Chức năng xuất dữ liệu

### 2. Dịch Vụ Phát Hiện Gian Lận (Fraud Detection Service - Python)
Phân tích và phát hiện gian lận trong thời gian thực:

**Chức năng cốt lõi:**
- Phát hiện gian lận dựa trên ML/AI
- Chấm điểm giao dịch theo thời gian thực
- Nhận diện mẫu gian lận
- Phân tích lịch sử

**Quy tắc phát hiện:**
- Kiểm tra tần suất giao dịch
- Giám sát ngưỡng số tiền
- Phát hiện bất thường về vị trí địa lý
- Nhận dạng thiết bị
- Giám sát danh mục người bán

**Phân tích rủi ro:**
- Hệ thống chấm điểm rủi ro
- Phân tích hành vi
- Lập hồ sơ tài khoản
- Phân tích mạng lưới

**Tích hợp:**
- Nhận sự kiện từ Kafka
- Tạo cảnh báo theo thời gian thực
- Triển khai và cập nhật mô hình ML
- Trích xuất đặc trưng

### 3. Dịch Vụ Cảnh Báo Bảo Mật (Security Alert Service - Kotlin)
Quản lý và xử lý các cảnh báo an ninh:

**Chức năng chính:**
- Quản lý và sắp xếp ưu tiên cảnh báo
- Kết hợp các cảnh báo liên quan
- Tự động hóa quy trình phản hồi
- Theo dõi trạng thái cảnh báo

**Tích hợp:**
- Tiếp nhận cảnh báo từ dịch vụ phát hiện gian lận
- Kết nối với dịch vụ thông báo
- Tích hợp với hệ thống bên ngoài
- Ghi nhật ký kiểm toán

### 4. Dịch Vụ Thông Báo (Notification Service - NodeJS)
Quản lý và gửi thông báo đa kênh:

**Chức năng chính:**
- Gửi thông báo qua nhiều kênh (Email, SMS, Push)
- Quản lý mẫu thông báo
- Tùy chỉnh cài đặt thông báo
- Theo dõi trạng thái gửi

**Tích hợp:**
- Xử lý thông qua hàng đợi
- Cơ chế thử lại
- Tích hợp với nhà cung cấp bên ngoài
- Thống kê thông báo

### 5. Dịch Vụ Phân Tích Thời Gian Thực (Real-time Analytics - Rust)
Xử lý và phân tích dữ liệu theo thời gian thực:

**Chức năng chính:**
- Tính toán chỉ số theo thời gian thực
- Phân tích chuỗi thời gian
- Xử lý tổng hợp dữ liệu
- Xử lý dữ liệu cho bảng điều khiển

**Phân tích:**
- Chỉ số khối lượng giao dịch
- Chỉ số phát hiện gian lận
- Giám sát hiệu suất
- Dữ liệu phân tích kinh doanh

## Luồng Sự Kiện
1. Dịch vụ giao dịch nhận yêu cầu mới
2. Kiểm tra và bổ sung dữ liệu
3. Lưu trữ vào MongoDB
4. Phát hành sự kiện vào Kafka
5. Dịch vụ phát hiện gian lận phân tích giao dịch
6. Khi phát hiện gian lận:
   - Gửi cảnh báo đến dịch vụ bảo mật
   - Dịch vụ bảo mật đánh giá và chuyển thông báo
   - Dịch vụ thông báo gửi cảnh báo đến người dùng
7. Dịch vụ phân tích cập nhật số liệu và báo cáo

## Công Nghệ Sử Dụng

- **Cơ sở dữ liệu:**
  - MongoDB: Lưu trữ giao dịch
  - Redis: Bộ nhớ đệm và giới hạn tần suất
  - Elasticsearch: Tập hợp và tìm kiếm logs

- **Hàng đợi tin nhắn:**
  - Kafka: Luồng sự kiện
  - Kafka Connect: Tích hợp dữ liệu

- **Giám sát và Ghi log:**
  - Elasticsearch + Kibana: Tập trung logs
  - Prometheus + Grafana: Đo lường và giám sát
  - Jaeger: Theo dõi phân tán

- **Hạ tầng:**
  - Docker: Đóng gói ứng dụng
  - Kubernetes: Điều phối container
  - Helm: Quản lý gói

## Yêu Cầu Hệ Thống

### Ngôn Ngữ và Runtime
- Go 1.21+
- Python 3.9+
- Kotlin/JDK 17
- Node.js 18+
- Rust 1.70+

### Container và Orchestration
- Docker và Docker Compose
- Kubernetes (tùy chọn)
- Helm (tùy chọn)

### Monitoring và Logging
- Elasticsearch 8.x
- Logstash 8.x
- Kibana 8.x

### Message Queue
- Apache Kafka 3.x
- Kafka Connect (tùy chọn)

### Databases
- MongoDB 6.x
- Redis 7.x

## Hướng Dẫn Cài Đặt

1. Tải mã nguồn:
```bash
git clone https://github.com/aletuan/fraud-detection-system.git
cd fraud-detection-system
```

2. Khởi động các dịch vụ cơ bản:
```bash
docker-compose up -d
```

3. Cài đặt thư viện cho từng dịch vụ:

Dịch vụ giao dịch:
```bash
cd services/transaction-service
go mod download
```

Dịch vụ phát hiện gian lận:
```bash
cd services/fraud-detection
python -m venv venv
source venv/bin/activate  # hoặc `venv\Scripts\activate` trên Windows
pip install -r requirements.txt
```

Dịch vụ cảnh báo bảo mật:
```bash
cd services/security-alert
./gradlew build
```

Dịch vụ thông báo:
```bash
cd services/notification-service
npm install
```

Dịch vụ phân tích:
```bash
cd services/realtime-processor
cargo build
```

## Cấu Trúc Topic Kafka

- `transactions`: Dữ liệu giao dịch gốc
- `fraud-alerts`: Cảnh báo gian lận
- `notifications`: Hàng đợi thông báo
- `transaction-analytics`: Dữ liệu phân tích

## Giám Sát và Ghi Log

### ELK Stack (Elasticsearch, Logstash, Kibana)

Hệ thống sử dụng ELK Stack để quản lý và phân tích logs tập trung:

**Logstash:**
- Cấu hình riêng cho từng service (fraud-detection.conf, transaction-service.conf)
- Thu thập logs qua TCP với định dạng JSON
- Thêm metadata: timestamp, service name, environment
- Phân loại logs theo giờ
- Gửi logs đến Elasticsearch với index format: {service-name}-YYYY.MM.DD

**Elasticsearch:**
- Lưu trữ và đánh index logs
- Indices theo service và ngày
- Hỗ trợ tìm kiếm full-text và truy vấn có cấu trúc
- Lưu trữ metadata và thông tin chi tiết về giao dịch

**Kibana:**
- Giao diện trực quan để xem và phân tích logs
- Dashboard theo dõi fraud alerts
- Biểu đồ phân tích xu hướng gian lận
- Bộ lọc theo thời gian, loại gian lận, mức độ rủi ro

**Cấu trúc Log:**
- Log levels: INFO, WARNING, ERROR
- Metadata: service, environment, timestamp
- Chi tiết giao dịch: ID, amount, location, device
- Thông tin fraud: risk score, triggered rules

### Các Công Cụ Giám Sát Khác

- Prometheus + Grafana: Giám sát metrics hệ thống
- Kafka UI: Theo dõi message queue và consumer groups
- Jaeger: Distributed tracing

## Tài Liệu API

Mỗi dịch vụ đều cung cấp tài liệu Swagger/OpenAPI tại đường dẫn `/docs` hoặc `/swagger-ui.html`

## Đóng Góp

Vui lòng đọc [CONTRIBUTING.md](CONTRIBUTING.md) để biết thêm chi tiết về quy trình đóng góp mã nguồn.

## Giấy Phép

MIT 