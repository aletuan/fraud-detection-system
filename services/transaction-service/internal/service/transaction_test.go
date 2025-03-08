package service

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"go.mongodb.org/mongo-driver/bson/primitive"

	"transaction-service/internal/domain"
	mockRepo "transaction-service/internal/repository/mock"
	"transaction-service/internal/repository"
)

func TestTransactionService_CreateTransaction(t *testing.T) {
	t.Run("Success", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test input
		input := CreateTransactionInput{
			AccountID:   "acc123",
			Amount:      1000.0,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			ReferenceID: "REF123",
			Description: "Test transaction",
			MerchantInfo: &MerchantInfo{
				ID:       "merch123",
				Name:     "Test Merchant",
				Category: "retail",
				Country:  "US",
			},
			Location: &domain.Location{
				Country: "US",
				City:    "New York",
				Coordinates: &domain.Coordinates{
					Latitude:  40.7128,
					Longitude: -74.0060,
				},
			},
			DeviceInfo: &domain.DeviceInfo{
				DeviceType:  "mobile",
				BrowserType: "chrome",
				DeviceOS:    "ios",
				IsMobile:    true,
				IPAddress:   "192.168.1.1",
				UserAgent:   "Mozilla/5.0",
			},
		}

		// Setup mock expectations
		mockRepo.On("GetByReferenceID", mock.Anything, input.ReferenceID).Return(nil, repository.ErrNotFound)
		mockRepo.On("Create", mock.Anything, mock.AnythingOfType("*domain.Transaction")).Return(nil)

		// Execute test
		tx, err := service.CreateTransaction(context.Background(), input)
		assert.NoError(t, err)
		assert.NotNil(t, tx)
		assert.Equal(t, input.AccountID, tx.AccountID)
		assert.Equal(t, input.Amount, tx.Amount)
		assert.Equal(t, input.Currency, tx.Currency)
		assert.Equal(t, input.Type, tx.Type)
		assert.Equal(t, domain.StatusPending, tx.Status)
		assert.Equal(t, input.ReferenceID, tx.ReferenceID)
		assert.Equal(t, input.MerchantInfo.ID, tx.MerchantID)
		assert.Equal(t, input.MerchantInfo.Name, tx.MerchantName)

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})

	t.Run("Duplicate_Transaction", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test input
		input := CreateTransactionInput{
			AccountID:   "acc123",
			Amount:      1000.0,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			ReferenceID: "REF123",
		}

		// Setup mock expectations
		existingTx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			ReferenceID: input.ReferenceID,
			CreatedAt:   time.Now(),
		}
		mockRepo.On("GetByReferenceID", mock.Anything, input.ReferenceID).Return(existingTx, nil)

		// Execute test
		tx, err := service.CreateTransaction(context.Background(), input)
		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.Equal(t, ErrDuplicateTransaction, err)

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})

	t.Run("Invalid_Input", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test input with missing required fields
		input := CreateTransactionInput{
			AccountID: "acc123",
			// Missing amount, currency, type, reference_id
		}

		// Execute test
		tx, err := service.CreateTransaction(context.Background(), input)
		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.Contains(t, err.Error(), ErrInvalidInput.Error())

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})
}

func TestTransactionService_UpdateTransaction(t *testing.T) {
	t.Run("Success", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test data
		txID := primitive.NewObjectID()
		existingTx := &domain.Transaction{
			ID:          txID,
			AccountID:   "acc123",
			Amount:      1000.0,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF123",
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}

		input := UpdateTransactionInput{
			Status:      domain.StatusCompleted,
			Description: "Updated description",
			Metadata: map[string]interface{}{
				"updated_by": "test",
			},
		}

		// Setup mock expectations
		mockRepo.On("GetByID", mock.Anything, txID.Hex()).Return(existingTx, nil)
		mockRepo.On("Update", mock.Anything, mock.AnythingOfType("*domain.Transaction")).Return(nil)

		// Execute test
		tx, err := service.UpdateTransaction(context.Background(), txID.Hex(), input)
		assert.NoError(t, err)
		assert.NotNil(t, tx)
		assert.Equal(t, input.Status, tx.Status)
		assert.Equal(t, input.Description, tx.Description)
		assert.Equal(t, input.Metadata["updated_by"], tx.Metadata["updated_by"])

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})

	t.Run("Invalid_Status_Transition", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test data
		txID := primitive.NewObjectID()
		existingTx := &domain.Transaction{
			ID:          txID,
			Status:      domain.StatusCompleted, // Already completed
			ReferenceID: "REF123",
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}

		input := UpdateTransactionInput{
			Status: domain.StatusFailed, // Try to change to failed
		}

		// Setup mock expectations
		mockRepo.On("GetByID", mock.Anything, txID.Hex()).Return(existingTx, nil)

		// Execute test
		tx, err := service.UpdateTransaction(context.Background(), txID.Hex(), input)
		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.Contains(t, err.Error(), ErrInvalidStatus.Error())

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})

	t.Run("Transaction_Not_Found", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test data
		txID := primitive.NewObjectID()
		input := UpdateTransactionInput{
			Status: domain.StatusCompleted,
		}

		// Setup mock expectations
		mockRepo.On("GetByID", mock.Anything, txID.Hex()).Return(nil, repository.ErrNotFound)

		// Execute test
		tx, err := service.UpdateTransaction(context.Background(), txID.Hex(), input)
		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.Equal(t, ErrTransactionNotFound, err)

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})
}

func TestTransactionService_ListTransactions(t *testing.T) {
	t.Run("Success", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test data
		params := ListTransactionsParams{
			AccountID: "acc123",
			Status:    string(domain.StatusPending),
			Page:      1,
			PageSize:  10,
			SortBy:    "created_at", // Valid sort field
		}

		expectedTxs := []domain.Transaction{
			{
				ID:          primitive.NewObjectID(),
				AccountID:   "acc123",
				Status:      domain.StatusPending,
				ReferenceID: "REF123",
				CreatedAt:   time.Now(),
			},
		}
		expectedTotal := int64(1)

		// Setup mock expectations with correct repository.ListParams
		mockRepo.On("List", mock.Anything, mock.MatchedBy(func(p repository.ListParams) bool {
			return p.Page == params.Page &&
				p.PageSize == params.PageSize &&
				p.SortBy == params.SortBy &&
				p.Filters["account_id"] == params.AccountID &&
				p.Filters["status"] == params.Status
		})).Return(expectedTxs, expectedTotal, nil)

		// Execute test
		txs, total, err := service.ListTransactions(context.Background(), params)
		assert.NoError(t, err)
		assert.Equal(t, expectedTxs, txs)
		assert.Equal(t, expectedTotal, total)

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})

	t.Run("Invalid_Params", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test data with invalid params
		params := ListTransactionsParams{
			Page:     0, // Invalid page number
			PageSize: 0, // Invalid page size
		}

		// Execute test
		txs, total, err := service.ListTransactions(context.Background(), params)
		assert.Error(t, err)
		assert.Empty(t, txs)
		assert.Zero(t, total)
		assert.Contains(t, err.Error(), ErrInvalidInput.Error())

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})
}

func TestTransactionService_GetTransaction(t *testing.T) {
	t.Run("Success", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test data
		txID := primitive.NewObjectID()
		expectedTx := &domain.Transaction{
			ID:          txID,
			AccountID:   "acc123",
			Status:      domain.StatusPending,
			ReferenceID: "REF123",
			CreatedAt:   time.Now(),
		}

		// Setup mock expectations
		mockRepo.On("GetByID", mock.Anything, txID.Hex()).Return(expectedTx, nil)

		// Execute test
		tx, err := service.GetTransaction(context.Background(), txID.Hex())
		assert.NoError(t, err)
		assert.Equal(t, expectedTx, tx)

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})

	t.Run("Not_Found", func(t *testing.T) {
		// Setup mock repository
		mockRepo := new(mockRepo.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		// Create test data
		txID := primitive.NewObjectID()

		// Setup mock expectations
		mockRepo.On("GetByID", mock.Anything, txID.Hex()).Return(nil, repository.ErrNotFound)

		// Execute test
		tx, err := service.GetTransaction(context.Background(), txID.Hex())
		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.Equal(t, ErrTransactionNotFound, err)

		// Verify mock expectations
		mockRepo.AssertExpectations(t)
	})
} 