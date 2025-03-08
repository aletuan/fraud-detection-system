package service

import (
	"context"
	"errors"
	"time"

	"transaction-service/internal/domain"
)

// TransactionService định nghĩa các business operations cho giao dịch
type TransactionService interface {
	// Core operations
	CreateTransaction(ctx context.Context, input CreateTransactionInput) (*domain.Transaction, error)
	UpdateTransaction(ctx context.Context, id string, input UpdateTransactionInput) (*domain.Transaction, error)
	GetTransaction(ctx context.Context, id string) (*domain.Transaction, error)
	ListTransactions(ctx context.Context, params ListTransactionsParams) ([]domain.Transaction, int64, error)

	// Business operations
	ProcessTransaction(ctx context.Context, tx *domain.Transaction) error
	ValidateTransaction(ctx context.Context, tx *domain.Transaction) error
	EnrichTransactionData(ctx context.Context, tx *domain.Transaction) error

	// Event publishing
	PublishTransactionEvent(ctx context.Context, tx *domain.Transaction, eventType EventType) error
}

// CreateTransactionInput đại diện cho dữ liệu đầu vào khi tạo giao dịch mới
type CreateTransactionInput struct {
	AccountID    string                 `json:"account_id" validate:"required"`
	Amount       float64                `json:"amount" validate:"required,gt=0"`
	Currency     string                 `json:"currency" validate:"required,len=3"`
	Type         domain.TransactionType `json:"type" validate:"required,oneof=debit credit"`
	Description  string                 `json:"description"`
	MerchantInfo *MerchantInfo         `json:"merchant_info"`
	Location     *domain.Location      `json:"location"`
	DeviceInfo   *domain.DeviceInfo    `json:"device_info"`
	ReferenceID  string                `json:"reference_id" validate:"required"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// UpdateTransactionInput đại diện cho dữ liệu cập nhật giao dịch
type UpdateTransactionInput struct {
	Status      domain.TransactionStatus `json:"status" validate:"required,oneof=pending completed failed"`
	Description string                   `json:"description"`
	Metadata    map[string]interface{}   `json:"metadata"`
}

// ListTransactionsParams định nghĩa các tham số để lọc và phân trang
type ListTransactionsParams struct {
	AccountID  string    `json:"account_id"`
	Status     string    `json:"status"`
	Type       string    `json:"type"`
	StartDate  time.Time `json:"start_date"`
	EndDate    time.Time `json:"end_date"`
	MinAmount  *float64  `json:"min_amount"`
	MaxAmount  *float64  `json:"max_amount"`
	SortBy     string    `json:"sort_by" validate:"oneof=created_at amount status"`
	SortDesc   bool      `json:"sort_desc"`
	Page       int       `json:"page" validate:"required,min=1"`
	PageSize   int       `json:"page_size" validate:"required,min=1,max=100"`
}

// MerchantInfo chứa thông tin về người bán
type MerchantInfo struct {
	ID       string `json:"id" validate:"required"`
	Name     string `json:"name" validate:"required"`
	Category string `json:"category"`
	Country  string `json:"country" validate:"len=2"`
}

// EventType định nghĩa các loại sự kiện giao dịch
type EventType string

const (
	EventTypeCreated   EventType = "transaction.created"
	EventTypeUpdated   EventType = "transaction.updated"
	EventTypeCompleted EventType = "transaction.completed"
	EventTypeFailed    EventType = "transaction.failed"
)

// Service errors
var (
	ErrInvalidInput          = errors.New("invalid input data")
	ErrTransactionNotFound   = errors.New("transaction not found")
	ErrDuplicateTransaction  = errors.New("duplicate transaction")
	ErrInvalidStatus         = errors.New("invalid status transition")
	ErrPublishEventFailed    = errors.New("failed to publish event")
	ErrProcessingFailed      = errors.New("transaction processing failed")
) 