# Operations Guide

Hướng dẫn vận hành và xử lý sự cố cho Fraud Detection System.

## Build và Khởi động Services

### Build từ Source Code

1. Build Transaction Service:
```bash
cd services/transaction-service
go build -o bin/transaction-service cmd/main.go
```

2. Build Fraud Detection Service:
```bash
cd services/fraud-detection
python -m build
```

### Khởi động Hệ thống

#### Sử dụng Docker Compose (Recommended)

1. Khởi động toàn bộ hệ thống:
```bash
docker-compose up -d
```

2. Khởi động từng service riêng lẻ:
```bash
# Khởi động infrastructure services
docker-compose up -d mongodb kafka zookeeper redis elasticsearch kibana

# Khởi động business services
docker-compose up -d transaction-service fraud-detection-service
```

3. Kiểm tra trạng thái các services:
```bash
docker-compose ps
```

#### Khởi động Manual (Development)

1. Start MongoDB:
```bash
mongod --dbpath ./data/db
```

2. Start Kafka & Zookeeper:
```bash
# Start Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka
bin/kafka-server-start.sh config/server.properties
```

3. Start Transaction Service:
```bash
cd services/transaction-service
./bin/transaction-service
```

4. Start Fraud Detection Service:
```bash
cd services/fraud-detection
python src/main.py
```

## Monitoring và Logging

### Xem Logs

1. Xem logs của tất cả services:
```bash
docker-compose logs -f
```

2. Xem logs của service cụ thể:
```bash
# Transaction Service logs
docker-compose logs -f transaction-service

# Fraud Detection Service logs
docker-compose logs -f fraud-detection-service

# Kafka logs
docker-compose logs -f kafka
```

3. Lọc logs theo thời gian:
```bash
docker-compose logs --since 30m  # Logs trong 30 phút gần nhất
```

### Monitoring

1. Health Checks:
```bash
# Transaction Service
curl http://localhost:8080/health

# Fraud Detection Service
curl http://localhost:8000/health
```

2. Metrics:
```bash
# Transaction Service metrics
curl http://localhost:8080/metrics

# Fraud Detection Service metrics
curl http://localhost:8000/metrics
```

3. Kafka Monitoring:
- Truy cập Kafka UI: http://localhost:8081
- Kiểm tra topics và messages
- Theo dõi consumer groups

4. MongoDB Monitoring:
```bash
# Kết nối MongoDB shell
docker-compose exec mongodb mongosh

# Kiểm tra statistics
db.stats()
```

## Troubleshooting

### Common Issues

1. Service Không Khởi động
- Kiểm tra logs: `docker-compose logs service-name`
- Kiểm tra port conflicts
- Kiểm tra environment variables
- Kiểm tra dependencies health checks

2. Kafka Connection Issues
```bash
# Kiểm tra Kafka brokers
docker-compose exec kafka kafka-broker-list

# Kiểm tra topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Kiểm tra consumer groups
docker-compose exec kafka kafka-consumer-groups --list --bootstrap-server localhost:9092
```

3. MongoDB Connection Issues
```bash
# Kiểm tra MongoDB connection
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

4. API Errors
- Kiểm tra request format
- Kiểm tra response codes
- Xem detailed error logs
- Verify authentication/authorization

### Debug Mode

1. Enable Debug Logging:
```bash
# Transaction Service
export LOG_LEVEL=debug
./bin/transaction-service

# Fraud Detection Service
export LOG_LEVEL=DEBUG
python src/main.py
```

2. Remote Debugging:
- Transaction Service (Delve):
```bash
dlv debug ./cmd/main.go
```

- Fraud Detection Service (pdb):
```bash
python -m pdb src/main.py
```

## Backup và Recovery

### MongoDB Backup
```bash
# Create backup
docker-compose exec mongodb mongodump --out /backup

# Restore from backup
docker-compose exec mongodb mongorestore /backup
```

### Kafka Topics Backup
```bash
# Backup topic data
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic transactions --from-beginning > transactions_backup.json

# Restore topic data
cat transactions_backup.json | docker-compose exec -T kafka kafka-console-producer \
  --bootstrap-server localhost:9092 --topic transactions
```

## Security

### Kiểm tra Security Configuration

1. Kafka Security:
- Verify SSL/TLS configuration
- Check SASL authentication
- Audit ACLs

2. MongoDB Security:
- Verify authentication mechanism
- Check user permissions
- Audit database access

3. API Security:
- Verify JWT tokens
- Check API key validation
- Monitor rate limiting

## Performance Tuning

### Kafka Performance
```bash
# Kiểm tra consumer lag
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group fraud-detection-group

# Kiểm tra topic partitions
docker-compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe --topic transactions
```

### MongoDB Performance
```bash
# Kiểm tra indexes
docker-compose exec mongodb mongosh --eval "db.transactions.getIndexes()"

# Analyze queries
docker-compose exec mongodb mongosh --eval "db.transactions.explain().find({status: 'PENDING'})"
``` 