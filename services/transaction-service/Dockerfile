# Build stage
FROM golang:1.21-alpine AS builder

# Add git for fetching dependencies
RUN apk add --no-cache git

# Set working directory
WORKDIR /app

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o transaction-service ./cmd/main.go

# Final stage
FROM alpine:latest

# Add ca-certificates for HTTPS and timezone data
RUN apk --no-cache add ca-certificates tzdata

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/transaction-service .

# Expose port
EXPOSE 8080

# Set environment variables with defaults
ENV MONGO_URI=mongodb://mongodb:27017 \
    DB_NAME=transaction_db \
    PORT=8080

# Run the application
CMD ["./transaction-service"] 