package service

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
	"go.mongodb.org/mongo-driver/bson/primitive"

	"transaction-service/internal/domain"
)

func TestTransactionValidator_ValidateTransaction(t *testing.T) {
	validator := NewTransactionValidator()
	ctx := context.Background()

	t.Run("Valid_Transaction", func(t *testing.T) {
		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      1000.0,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF123",
			MerchantID:  "merch123",
			Metadata: map[string]interface{}{
				"merchant_category": "retail",
			},
			Location: &domain.Location{
				Country: "US",
			},
			DeviceInfo: &domain.DeviceInfo{
				DeviceType:  "mobile",
				BrowserType: "chrome",
				DeviceOS:    "ios",
				IsMobile:    true,
			},
		}

		result, err := validator.ValidateTransaction(ctx, tx)
		assert.NoError(t, err)
		assert.True(t, result.IsValid)
		assert.Empty(t, result.Errors)
		assert.Less(t, result.RiskScore, domain.HighRiskThreshold)
	})

	t.Run("Invalid_Currency", func(t *testing.T) {
		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      1000.0,
			Currency:    "EUR", // Not supported
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF123",
		}

		result, err := validator.ValidateTransaction(ctx, tx)
		assert.NoError(t, err)
		assert.False(t, result.IsValid)
		assert.NotEmpty(t, result.Errors)
		assert.Equal(t, domain.ErrCodeInvalidCurrency, result.Errors[0].Code)
	})

	t.Run("Amount_Limit_Exceeded", func(t *testing.T) {
		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      20000.0, // Exceeds limit
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF123",
		}

		result, err := validator.ValidateTransaction(ctx, tx)
		assert.NoError(t, err)
		assert.False(t, result.IsValid)
		assert.NotEmpty(t, result.Errors)
		assert.Equal(t, domain.ErrCodeAmountLimit, result.Errors[0].Code)
	})

	t.Run("Blocked_Merchant_Category", func(t *testing.T) {
		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      1000.0,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF123",
			MerchantID:  "merch123",
			Metadata: map[string]interface{}{
				"merchant_category": "gambling", // Blocked category
			},
		}

		result, err := validator.ValidateTransaction(ctx, tx)
		assert.NoError(t, err)
		assert.False(t, result.IsValid)
		assert.NotEmpty(t, result.Errors)
		assert.Equal(t, domain.ErrCodeBlockedMerchant, result.Errors[0].Code)
	})

	t.Run("Blocked_Country", func(t *testing.T) {
		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      1000.0,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF123",
			Location: &domain.Location{
				Country: "NK", // Blocked country
			},
		}

		result, err := validator.ValidateTransaction(ctx, tx)
		assert.NoError(t, err)
		assert.False(t, result.IsValid)
		assert.NotEmpty(t, result.Errors)
		assert.Equal(t, domain.ErrCodeBlockedLocation, result.Errors[0].Code)
	})

	t.Run("Blocked_Browser", func(t *testing.T) {
		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      1000.0,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF123",
			DeviceInfo: &domain.DeviceInfo{
				DeviceType:  "desktop",
				BrowserType: "tor", // Blocked browser
				DeviceOS:    "linux",
			},
		}

		result, err := validator.ValidateTransaction(ctx, tx)
		assert.NoError(t, err)
		assert.False(t, result.IsValid)
		assert.NotEmpty(t, result.Errors)
		assert.Equal(t, domain.ErrCodeBlockedDevice, result.Errors[0].Code)
	})

	t.Run("High_Risk_Score", func(t *testing.T) {
		tx := &domain.Transaction{
			ID:          primitive.NewObjectID(),
			AccountID:   "acc123",
			Amount:      9500.0,
			Currency:    "USD",
			Type:        domain.TransactionTypeDebit,
			Status:      domain.StatusPending,
			ReferenceID: "REF123",
			DeviceInfo: &domain.DeviceInfo{
				DeviceType:  "unknown", // Device type không xác định
				BrowserType: "chrome",  // Browser hợp lệ
				DeviceOS:    "unknown", // OS không xác định
			},
		}

		result, err := validator.ValidateTransaction(ctx, tx)
		assert.NoError(t, err)
		assert.False(t, result.IsValid)
		assert.NotEmpty(t, result.Errors)
		assert.Equal(t, domain.ErrCodeHighRisk, result.Errors[0].Code)
		assert.GreaterOrEqual(t, result.RiskScore, domain.HighRiskThreshold)
	})
} 