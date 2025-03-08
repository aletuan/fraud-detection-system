package mock

import (
	"context"
	"sync"

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