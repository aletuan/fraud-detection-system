package main

import (
	"context"
	"log"
	"os"
	"strconv"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"transaction-service/internal/api"
	"transaction-service/internal/repository/mongodb"
	"transaction-service/internal/service"
)

func main() {
	// Get environment variables
	mongoURI := getEnv("MONGO_URI", "mongodb://localhost:27017")
	dbName := getEnv("DB_NAME", "transaction_db")
	port := getEnvAsInt("PORT", 8080)

	// Initialize MongoDB client
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(mongoURI))
	if err != nil {
		log.Fatalf("Failed to connect to MongoDB: %v", err)
	}
	defer client.Disconnect(ctx)

	// Initialize MongoDB repository
	db := client.Database(dbName)
	repo := mongodb.NewMongoRepository(db)

	// Initialize transaction service
	txService := service.NewTransactionService(repo)

	// Initialize and start HTTP server
	server := api.NewServer(txService, port)
	if err := server.Start(); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

// getEnvAsInt gets an environment variable as integer or returns a default value
func getEnvAsInt(key string, defaultValue int) int {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	
	intValue, err := strconv.Atoi(value)
	if err != nil {
		return defaultValue
	}
	return intValue
} 