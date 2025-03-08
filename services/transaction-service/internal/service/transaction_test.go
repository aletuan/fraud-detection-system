package service

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"go.mongodb.org/mongo-driver/bson/primitive"

	"transaction-service/internal/domain"
	"transaction-service/internal/repository"
	repoMock "transaction-service/internal/repository/mock"
)

func TestTransactionService_CreateTransaction(t *testing.T) {
	ctx := context.Background()

	t.Run("Success", func(t *testing.T) {
		mockRepo := new(repoMock.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		input := CreateTransactionInput{
			AccountID:   "acc123",
			Amount:      100.50,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Description: "Test transaction",
			ReferenceID: "REF123",
			MerchantInfo: &MerchantInfo{
				ID:       "merch123",
				Name:     "Test Merchant",
				Category: "retail",
				Country:  "US",
			},
		}

		mockRepo.On("GetByReferenceID", ctx, input.ReferenceID).Return(nil, repository.ErrNotFound)
		mockRepo.On("Create", ctx, mock.AnythingOfType("*domain.Transaction")).Return(nil)

		tx, err := service.CreateTransaction(ctx, input)

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
		assert.Contains(t, tx.Metadata, "merchant_category")
		assert.Contains(t, tx.Metadata, "merchant_country")

		mockRepo.AssertExpectations(t)
	})

	t.Run("Duplicate_Transaction", func(t *testing.T) {
		mockRepo := new(repoMock.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		input := CreateTransactionInput{
			AccountID:   "acc123",
			Amount:      100.50,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			ReferenceID: "REF123",
		}

		existingTx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			ReferenceID: input.ReferenceID,
		}

		mockRepo.On("GetByReferenceID", ctx, input.ReferenceID).Return(existingTx, nil)

		tx, err := service.CreateTransaction(ctx, input)

		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.ErrorIs(t, err, ErrDuplicateTransaction)

		mockRepo.AssertExpectations(t)
	})

	t.Run("Invalid_Input", func(t *testing.T) {
		mockRepo := new(repoMock.MockTransactionRepository)
		service := NewTransactionService(mockRepo)

		input := CreateTransactionInput{
			// Missing required fields
			Description: "Test transaction",
		}

		tx, err := service.CreateTransaction(ctx, input)

		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.ErrorIs(t, err, ErrInvalidInput)
	})
}

func TestTransactionService_UpdateTransaction(t *testing.T) {
	mockRepo := new(repoMock.MockTransactionRepository)
	service := NewTransactionService(mockRepo)
	ctx := context.Background()

	t.Run("Success", func(t *testing.T) {
		id := primitive.NewObjectID()
		existingTx := &domain.Transaction{
			ID:     id,
			Status: domain.StatusPending,
		}

		input := UpdateTransactionInput{
			Status:      domain.StatusCompleted,
			Description: "Updated description",
			Metadata: map[string]interface{}{
				"reason": "test",
			},
		}

		mockRepo.On("GetByID", ctx, id.Hex()).Return(existingTx, nil)
		mockRepo.On("Update", ctx, mock.AnythingOfType("*domain.Transaction")).Return(nil)

		tx, err := service.UpdateTransaction(ctx, id.Hex(), input)

		assert.NoError(t, err)
		assert.NotNil(t, tx)
		assert.Equal(t, input.Status, tx.Status)
		assert.Equal(t, input.Description, tx.Description)
		assert.Contains(t, tx.Metadata, "reason")
	})

	t.Run("Invalid_Status_Transition", func(t *testing.T) {
		id := primitive.NewObjectID()
		existingTx := &domain.Transaction{
			ID:     id,
			Status: domain.StatusCompleted,
		}

		input := UpdateTransactionInput{
			Status: domain.StatusFailed,
		}

		mockRepo.On("GetByID", ctx, id.Hex()).Return(existingTx, nil)

		tx, err := service.UpdateTransaction(ctx, id.Hex(), input)

		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.ErrorIs(t, err, ErrInvalidStatus)
	})

	t.Run("Transaction_Not_Found", func(t *testing.T) {
		id := primitive.NewObjectID()
		input := UpdateTransactionInput{
			Status: domain.StatusCompleted,
		}

		mockRepo.On("GetByID", ctx, id.Hex()).Return(nil, repository.ErrNotFound)

		tx, err := service.UpdateTransaction(ctx, id.Hex(), input)

		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.ErrorIs(t, err, ErrTransactionNotFound)
	})
}

func TestTransactionService_ListTransactions(t *testing.T) {
	mockRepo := new(repoMock.MockTransactionRepository)
	service := NewTransactionService(mockRepo)
	ctx := context.Background()

	t.Run("Success", func(t *testing.T) {
		params := ListTransactionsParams{
			AccountID:  "acc123",
			Status:     string(domain.StatusPending),
			StartDate:  time.Now().Add(-24 * time.Hour),
			EndDate:    time.Now(),
			MinAmount:  ptr(100.0),
			MaxAmount:  ptr(1000.0),
			Page:       1,
			PageSize:   10,
			SortBy:     "created_at",
			SortDesc:   true,
		}

		expectedTxs := []domain.Transaction{
			{
				ID:        primitive.NewObjectID(),
				AccountID: "acc123",
				Amount:    500.0,
				Status:    domain.StatusPending,
			},
		}
		expectedTotal := int64(1)

		mockRepo.On("List", ctx, mock.AnythingOfType("repository.ListParams")).Return(expectedTxs, expectedTotal, nil)

		txs, total, err := service.ListTransactions(ctx, params)

		assert.NoError(t, err)
		assert.Equal(t, expectedTxs, txs)
		assert.Equal(t, expectedTotal, total)
	})

	t.Run("Invalid_Params", func(t *testing.T) {
		params := ListTransactionsParams{
			// Invalid page number
			Page:     0,
			PageSize: 10,
		}

		txs, total, err := service.ListTransactions(ctx, params)

		assert.Error(t, err)
		assert.Nil(t, txs)
		assert.Zero(t, total)
		assert.ErrorIs(t, err, ErrInvalidInput)
	})
}

func TestTransactionService_GetTransaction(t *testing.T) {
	mockRepo := new(repoMock.MockTransactionRepository)
	service := NewTransactionService(mockRepo)
	ctx := context.Background()

	t.Run("Success", func(t *testing.T) {
		id := primitive.NewObjectID()
		expectedTx := &domain.Transaction{
			ID:     id,
			Amount: 100.0,
		}

		mockRepo.On("GetByID", ctx, id.Hex()).Return(expectedTx, nil)

		tx, err := service.GetTransaction(ctx, id.Hex())

		assert.NoError(t, err)
		assert.Equal(t, expectedTx, tx)
	})

	t.Run("Not_Found", func(t *testing.T) {
		id := primitive.NewObjectID()

		mockRepo.On("GetByID", ctx, id.Hex()).Return(nil, repository.ErrNotFound)

		tx, err := service.GetTransaction(ctx, id.Hex())

		assert.Error(t, err)
		assert.Nil(t, tx)
		assert.ErrorIs(t, err, ErrTransactionNotFound)
	})
}

// Helper function to create pointer to float64
func ptr(v float64) *float64 {
	return &v
} 