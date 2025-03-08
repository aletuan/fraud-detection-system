# Hệ Thống Phát Hiện Gian Lận

Hệ thống phát hiện gian lận giao dịch theo thời gian thực được xây dựng trên nền tảng Microservices và Event-Driven Architecture.

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

- Docker và Docker Compose
- Go 1.21+
- Python 3.9+
- Kotlin/JDK 17
- Node.js 18+
- Rust 1.70+

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

- Elasticsearch + Kibana: Quản lý log tập trung
- Prometheus + Grafana: Giám sát hệ thống
- Kafka UI: Theo dõi message queue

## Tài Liệu API

Mỗi dịch vụ đều cung cấp tài liệu Swagger/OpenAPI tại đường dẫn `/docs` hoặc `/swagger-ui.html`

## Đóng Góp

Vui lòng đọc [CONTRIBUTING.md](CONTRIBUTING.md) để biết thêm chi tiết về quy trình đóng góp mã nguồn.

## Giấy Phép

MIT 