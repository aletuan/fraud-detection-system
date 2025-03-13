.PHONY: build run test clean docker-build docker-run docker-stop

# Go commands
build:
	go build -o bin/transaction-service ./cmd/main.go

run:
	go run ./cmd/main.go

test:
	go test -v ./...

clean:
	rm -rf bin/

# Docker commands
docker-build:
	docker-compose build

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Development helpers
dev: docker-build docker-run

restart: docker-stop docker-run

# Database commands
db-shell:
	docker-compose exec mongodb mongo

kafka-topics:
	docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Testing helpers
test-coverage:
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out

# Linting and formatting
lint:
	golangci-lint run

fmt:
	go fmt ./...

# Help command
help:
	@echo "Available commands:"
	@echo "  build          - Build the application"
	@echo "  run           - Run the application locally"
	@echo "  test          - Run tests"
	@echo "  clean         - Clean build artifacts"
	@echo "  docker-build  - Build Docker images"
	@echo "  docker-run    - Start all containers"
	@echo "  docker-stop   - Stop all containers"
	@echo "  docker-logs   - View container logs"
	@echo "  dev           - Build and start containers"
	@echo "  restart       - Restart all containers"
	@echo "  db-shell      - Open MongoDB shell"
	@echo "  kafka-topics  - List Kafka topics"
	@echo "  test-coverage - Run tests with coverage"
	@echo "  lint          - Run linter"
	@echo "  fmt           - Format code" 