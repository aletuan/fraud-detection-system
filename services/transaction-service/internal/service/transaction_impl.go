package service

import (
	"context"
	"errors"
	"fmt"
	"log"
	"time"

	"github.com/go-playground/validator/v10"
	"go.mongodb.org/mongo-driver/bson/primitive"

	"transaction-service/internal/domain"
	"transaction-service/internal/repository"
	"transaction-service/internal/messaging/kafka"
)

type transactionService struct {
	repo      repository.TransactionRepository
	validator *validator.Validate
	producer  kafka.Producer
}

// NewTransactionService tạo một instance mới của TransactionService
func NewTransactionService(repo repository.TransactionRepository, producer kafka.Producer) TransactionService {
	if producer == nil {
		// Create default Kafka producer if none provided
		kafkaConfig := kafka.DefaultConfig()
		var err error
		producer, err = kafka.NewProducer(kafkaConfig)
		if err != nil {
			log.Printf("Failed to create Kafka producer: %v", err)
		}
	}

	return &transactionService{
		repo:      repo,
		validator: validator.New(),
		producer:  producer,
	}
}

// CreateTransaction tạo một giao dịch mới
func (s *transactionService) CreateTransaction(ctx context.Context, input CreateTransactionInput) (*domain.Transaction, error) {
	if err := s.validator.Struct(input); err != nil {
		log.Printf("Invalid input data: %v", err)
		return nil, fmt.Errorf("%w: %v", ErrInvalidInput, err)
	}

	// Kiểm tra giao dịch trùng lặp
	existing, err := s.repo.GetByReferenceID(ctx, input.ReferenceID)
	if err != nil && !errors.Is(err, repository.ErrNotFound) {
		log.Printf("Failed to check duplicate transaction: %v", err)
		return nil, fmt.Errorf("failed to check duplicate transaction: %w", err)
	}
	if existing != nil {
		log.Printf("Duplicate transaction found with reference ID: %s", input.ReferenceID)
		return nil, ErrDuplicateTransaction
	}

	// Tạo transaction mới
	tx := &domain.Transaction{
		ID:          primitive.NewObjectID(),
		AccountID:   input.AccountID,
		Amount:      input.Amount,
		Currency:    input.Currency,
		Type:        input.Type,
		Status:      domain.StatusPending,
		Description: input.Description,
		ReferenceID: input.ReferenceID,
		Location:    input.Location,
		DeviceInfo:  input.DeviceInfo,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Thêm merchant info nếu có
	if input.MerchantInfo != nil {
		tx.MerchantID = input.MerchantInfo.ID
		tx.MerchantName = input.MerchantInfo.Name
		if tx.Metadata == nil {
			tx.Metadata = make(map[string]interface{})
		}
		tx.Metadata["merchant_category"] = input.MerchantInfo.Category
		tx.Metadata["merchant_country"] = input.MerchantInfo.Country
	}

	// Bổ sung metadata
	if input.Metadata != nil {
		if tx.Metadata == nil {
			tx.Metadata = make(map[string]interface{})
		}
		for k, v := range input.Metadata {
			tx.Metadata[k] = v
		}
	}

	// Validate basic transaction data
	if err := s.ValidateTransaction(ctx, tx); err != nil {
		log.Printf("Transaction validation failed: %v", err)
		return nil, err
	}

	// Lưu transaction vào database
	if err := s.repo.Create(ctx, tx); err != nil {
		log.Printf("Failed to create transaction: %v", err)
		return nil, fmt.Errorf("failed to create transaction: %w", err)
	}

	// Publish event
	if err := s.PublishTransactionEvent(ctx, tx, EventTypeCreated); err != nil {
		log.Printf("Failed to publish transaction created event: %v", err)
	}

	return tx, nil
}

// UpdateTransaction cập nhật trạng thái giao dịch
func (s *transactionService) UpdateTransaction(ctx context.Context, id string, input UpdateTransactionInput) (*domain.Transaction, error) {
	if err := s.validator.Struct(input); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrInvalidInput, err)
	}

	// Lấy transaction hiện tại
	tx, err := s.repo.GetByID(ctx, id)
	if err != nil {
		if errors.Is(err, repository.ErrNotFound) {
			return nil, ErrTransactionNotFound
		}
		return nil, fmt.Errorf("failed to get transaction: %w", err)
	}

	// Kiểm tra trạng thái chuyển đổi
	if !isValidStatusTransition(tx.Status, input.Status) {
		return nil, ErrInvalidStatus
	}

	// Cập nhật thông tin
	tx.Status = input.Status
	if input.Description != "" {
		tx.Description = input.Description
	}
	if input.Metadata != nil {
		if tx.Metadata == nil {
			tx.Metadata = make(map[string]interface{})
		}
		for k, v := range input.Metadata {
			tx.Metadata[k] = v
		}
	}
	tx.UpdatedAt = time.Now()

	// Lưu thay đổi
	if err := s.repo.Update(ctx, tx); err != nil {
		return nil, fmt.Errorf("failed to update transaction: %w", err)
	}

	// Xác định loại event
	var eventType EventType
	switch input.Status {
	case domain.StatusCompleted:
		eventType = EventTypeCompleted
	case domain.StatusFailed:
		eventType = EventTypeFailed
	default:
		eventType = EventTypeUpdated
	}

	// Publish event
	if err := s.PublishTransactionEvent(ctx, tx, eventType); err != nil {
		log.Printf("Failed to publish transaction update event: %v", err)
	}

	return tx, nil
}

// GetTransaction lấy thông tin một giao dịch
func (s *transactionService) GetTransaction(ctx context.Context, id string) (*domain.Transaction, error) {
	tx, err := s.repo.GetByID(ctx, id)
	if err != nil {
		if errors.Is(err, repository.ErrNotFound) {
			return nil, ErrTransactionNotFound
		}
		return nil, fmt.Errorf("failed to get transaction: %w", err)
	}
	return tx, nil
}

// ListTransactions lấy danh sách giao dịch theo điều kiện
func (s *transactionService) ListTransactions(ctx context.Context, params ListTransactionsParams) ([]domain.Transaction, int64, error) {
	if err := s.validator.Struct(params); err != nil {
		return nil, 0, fmt.Errorf("%w: %v", ErrInvalidInput, err)
	}

	// Chuyển đổi params thành filters
	filters := make(map[string]interface{})
	if params.AccountID != "" {
		filters["account_id"] = params.AccountID
	}
	if params.Status != "" {
		filters["status"] = params.Status
	}
	if params.Type != "" {
		filters["type"] = params.Type
	}
	if !params.StartDate.IsZero() {
		filters["created_at"] = map[string]interface{}{"$gte": params.StartDate}
	}
	if !params.EndDate.IsZero() {
		if _, ok := filters["created_at"]; !ok {
			filters["created_at"] = make(map[string]interface{})
		}
		filters["created_at"].(map[string]interface{})["$lte"] = params.EndDate
	}
	if params.MinAmount != nil {
		filters["amount"] = map[string]interface{}{"$gte": *params.MinAmount}
	}
	if params.MaxAmount != nil {
		if _, ok := filters["amount"]; !ok {
			filters["amount"] = make(map[string]interface{})
		}
		filters["amount"].(map[string]interface{})["$lte"] = *params.MaxAmount
	}

	// Tạo repository params
	repoParams := repository.ListParams{
		Page:     params.Page,
		PageSize: params.PageSize,
		SortBy:   params.SortBy,
		SortDesc: params.SortDesc,
		Filters:  filters,
	}

	return s.repo.List(ctx, repoParams)
}

// ProcessTransaction xử lý giao dịch
func (s *transactionService) ProcessTransaction(ctx context.Context, tx *domain.Transaction) error {
	// TODO: Implement business logic for processing transaction
	return nil
}

// ValidateTransaction kiểm tra tính hợp lệ của giao dịch
func (s *transactionService) ValidateTransaction(ctx context.Context, tx *domain.Transaction) error {
	// Validate required fields
	if err := s.validator.Struct(tx); err != nil {
		return fmt.Errorf("%w: %v", ErrInvalidInput, err)
	}
	return nil
}

// EnrichTransactionData bổ sung thông tin cho giao dịch
func (s *transactionService) EnrichTransactionData(ctx context.Context, tx *domain.Transaction) error {
	// TODO: Implement data enrichment logic
	return nil
}

// PublishTransactionEvent publish event cho Kafka
func (s *transactionService) PublishTransactionEvent(ctx context.Context, tx *domain.Transaction, eventType EventType) error {
	if s.producer == nil {
		log.Printf("Kafka producer not initialized")
		return nil // Skip publishing if producer is not available
	}

	// Create event metadata
	metadata := kafka.EventMetadata{
		Source: "transaction-service",
	}

	// Add correlation ID from context if available
	if corrID, ok := ctx.Value("correlation_id").(string); ok {
		metadata.CorrelationID = corrID
	}

	// Add user ID from context if available  
	if userID, ok := ctx.Value("user_id").(string); ok {
		metadata.UserID = userID
	}

	// Create Kafka event
	event := kafka.NewTransactionEvent(kafka.EventType(eventType), tx, metadata)

	// Publish event
	if err := s.producer.PublishEvent(ctx, event); err != nil {
		log.Printf("Failed to publish transaction event: %v", err)
		return fmt.Errorf("%w: %v", ErrPublishEventFailed, err)
	}

	log.Printf("Published transaction event - Type: %s, ID: %s", eventType, tx.ID.Hex())
	return nil
}

// isValidStatusTransition kiểm tra tính hợp lệ của việc chuyển trạng thái
func isValidStatusTransition(from, to domain.TransactionStatus) bool {
	switch from {
	case domain.StatusPending:
		return to == domain.StatusCompleted || to == domain.StatusFailed
	case domain.StatusCompleted, domain.StatusFailed:
		return false // Không cho phép thay đổi trạng thái sau khi đã hoàn thành hoặc thất bại
	default:
		return false
	}
} 