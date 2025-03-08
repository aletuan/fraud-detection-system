package repository

import (
	"context"
	"errors"

	"transaction-service/internal/domain"
)

// TransactionRepository defines the interface for transaction storage operations
type TransactionRepository interface {
	// Create stores a new transaction
	Create(ctx context.Context, transaction *domain.Transaction) error

	// GetByID retrieves a transaction by its ID
	GetByID(ctx context.Context, id string) (*domain.Transaction, error)

	// Update modifies an existing transaction
	Update(ctx context.Context, transaction *domain.Transaction) error

	// Delete removes a transaction
	Delete(ctx context.Context, id string) error

	// List retrieves transactions with pagination and filters
	List(ctx context.Context, params ListParams) ([]domain.Transaction, int64, error)

	// GetByReferenceID finds a transaction by its reference ID
	GetByReferenceID(ctx context.Context, referenceID string) (*domain.Transaction, error)

	// GetByAccountID retrieves all transactions for an account
	GetByAccountID(ctx context.Context, accountID string, params ListParams) ([]domain.Transaction, int64, error)
}

// ListParams defines parameters for listing transactions
type ListParams struct {
	Page     int
	PageSize int
	SortBy   string
	SortDesc bool
	Filters  map[string]interface{}
}

// NewListParams creates a new ListParams with default values
func NewListParams() ListParams {
	return ListParams{
		Page:     1,
		PageSize: 10,
		SortBy:   "created_at",
		SortDesc: true,
		Filters:  make(map[string]interface{}),
	}
}

// Repository errors
var (
	ErrNotFound          = errors.New("transaction not found")
	ErrDuplicateKey     = errors.New("duplicate key error")
	ErrInvalidID        = errors.New("invalid id format")
	ErrConnectionFailed = errors.New("database connection failed")
) 