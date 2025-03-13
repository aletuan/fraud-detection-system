package mock

import (
	"context"
	"sync"

	"github.com/stretchr/testify/mock"

	"transaction-service/internal/domain"
	"transaction-service/internal/repository"
)

// MockRepository implements TransactionRepository interface for testing
type MockRepository struct {
	transactions map[string]*domain.Transaction
	mu          sync.RWMutex
}

// NewMockRepository creates a new mock repository
func NewMockRepository() *MockRepository {
	return &MockRepository{
		transactions: make(map[string]*domain.Transaction),
	}
}

// MockTransactionRepository is a mock implementation of TransactionRepository
type MockTransactionRepository struct {
	mock.Mock
}

func (m *MockTransactionRepository) Create(ctx context.Context, tx *domain.Transaction) error {
	args := m.Called(ctx, tx)
	return args.Error(0)
}

func (m *MockTransactionRepository) Update(ctx context.Context, tx *domain.Transaction) error {
	args := m.Called(ctx, tx)
	return args.Error(0)
}

func (m *MockTransactionRepository) Delete(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockTransactionRepository) GetByID(ctx context.Context, id string) (*domain.Transaction, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransactionRepository) GetByReferenceID(ctx context.Context, referenceID string) (*domain.Transaction, error) {
	args := m.Called(ctx, referenceID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransactionRepository) List(ctx context.Context, params repository.ListParams) ([]domain.Transaction, int64, error) {
	args := m.Called(ctx, params)
	if args.Get(0) == nil {
		return nil, 0, args.Error(2)
	}
	return args.Get(0).([]domain.Transaction), args.Get(1).(int64), args.Error(2)
}

func (m *MockTransactionRepository) GetByAccountID(ctx context.Context, accountID string, params repository.ListParams) ([]domain.Transaction, int64, error) {
	args := m.Called(ctx, accountID, params)
	if args.Get(0) == nil {
		return nil, 0, args.Error(2)
	}
	return args.Get(0).([]domain.Transaction), args.Get(1).(int64), args.Error(2)
}

func (m *MockRepository) Create(ctx context.Context, tx *domain.Transaction) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if tx.ID.IsZero() {
		return repository.ErrInvalidID
	}

	m.transactions[tx.ID.Hex()] = tx
	return nil
}

func (m *MockRepository) GetByID(ctx context.Context, id string) (*domain.Transaction, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	tx, exists := m.transactions[id]
	if !exists {
		return nil, repository.ErrNotFound
	}
	return tx, nil
}

func (m *MockRepository) Update(ctx context.Context, tx *domain.Transaction) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.transactions[tx.ID.Hex()]; !exists {
		return repository.ErrNotFound
	}

	m.transactions[tx.ID.Hex()] = tx
	return nil
}

func (m *MockRepository) Delete(ctx context.Context, id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.transactions[id]; !exists {
		return repository.ErrNotFound
	}

	delete(m.transactions, id)
	return nil
}

func (m *MockRepository) List(ctx context.Context, params repository.ListParams) ([]domain.Transaction, int64, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	var transactions []domain.Transaction
	for _, tx := range m.transactions {
		transactions = append(transactions, *tx)
	}

	// Simple implementation without actual pagination and filtering
	return transactions, int64(len(transactions)), nil
}

func (m *MockRepository) GetByReferenceID(ctx context.Context, referenceID string) (*domain.Transaction, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	for _, tx := range m.transactions {
		if tx.ReferenceID == referenceID {
			return tx, nil
		}
	}
	return nil, repository.ErrNotFound
}

func (m *MockRepository) GetByAccountID(ctx context.Context, accountID string, params repository.ListParams) ([]domain.Transaction, int64, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	var transactions []domain.Transaction
	for _, tx := range m.transactions {
		if tx.AccountID == accountID {
			transactions = append(transactions, *tx)
		}
	}
	return transactions, int64(len(transactions)), nil
} 