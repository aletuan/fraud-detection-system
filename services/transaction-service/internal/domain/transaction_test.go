package domain

import (
	"testing"
	"time"

	"github.com/go-playground/validator/v10"
	"github.com/stretchr/testify/assert"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

func TestTransaction_Validation(t *testing.T) {
	validate := validator.New()

	t.Run("valid_transaction", func(t *testing.T) {
		tx := &Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      100.0,
			Currency:    "USD",
			Type:        TransactionTypeDebit,
			Status:      StatusPending,
			ReferenceID: "REF123",
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}

		err := validate.Struct(tx)
		assert.NoError(t, err)
	})

	t.Run("invalid_-_missing_account_id", func(t *testing.T) {
		tx := &Transaction{
			ID:          primitive.NewObjectID(),
			Amount:      100.0,
			Currency:    "USD",
			Type:        TransactionTypeDebit,
			Status:      StatusPending,
			ReferenceID: "REF123",
		}

		err := validate.Struct(tx)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "AccountID")
	})

	t.Run("invalid_-_zero_amount", func(t *testing.T) {
		tx := &Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      0,
			Currency:    "USD",
			Type:        TransactionTypeDebit,
			Status:      StatusPending,
			ReferenceID: "REF123",
		}

		err := validate.Struct(tx)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "Amount")
	})

	t.Run("invalid_-_wrong_currency_length", func(t *testing.T) {
		tx := &Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      100.0,
			Currency:    "USDD",
			Type:        TransactionTypeDebit,
			Status:      StatusPending,
			ReferenceID: "REF123",
		}

		err := validate.Struct(tx)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "Currency")
	})

	t.Run("invalid_-_wrong_transaction_type", func(t *testing.T) {
		tx := &Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      100.0,
			Currency:    "USD",
			Type:        "invalid",
			Status:      StatusPending,
			ReferenceID: "REF123",
		}

		err := validate.Struct(tx)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "Type")
	})
} 