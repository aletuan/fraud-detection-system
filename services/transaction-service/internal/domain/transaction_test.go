package domain

import (
	"testing"
	"time"

	"github.com/go-playground/validator/v10"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

func TestTransaction_Validation(t *testing.T) {
	validate := validator.New()

	tests := []struct {
		name    string
		tx      Transaction
		wantErr bool
	}{
		{
			name: "valid transaction",
			tx: Transaction{
				ID:        primitive.NewObjectID(),
				AccountID: "ACC123",
				Amount:    100.50,
				Currency:  "USD",
				Type:      TypeDebit,
				Status:    StatusPending,
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
			},
			wantErr: false,
		},
		{
			name: "invalid - missing account_id",
			tx: Transaction{
				ID:       primitive.NewObjectID(),
				Amount:   100.50,
				Currency: "USD",
				Type:     TypeDebit,
				Status:   StatusPending,
			},
			wantErr: true,
		},
		{
			name: "invalid - zero amount",
			tx: Transaction{
				ID:        primitive.NewObjectID(),
				AccountID: "ACC123",
				Amount:    0,
				Currency:  "USD",
				Type:      TypeDebit,
				Status:    StatusPending,
			},
			wantErr: true,
		},
		{
			name: "invalid - wrong currency length",
			tx: Transaction{
				ID:        primitive.NewObjectID(),
				AccountID: "ACC123",
				Amount:    100.50,
				Currency:  "USDD",
				Type:      TypeDebit,
				Status:    StatusPending,
			},
			wantErr: true,
		},
		{
			name: "invalid - wrong transaction type",
			tx: Transaction{
				ID:        primitive.NewObjectID(),
				AccountID: "ACC123",
				Amount:    100.50,
				Currency:  "USD",
				Type:      "invalid",
				Status:    StatusPending,
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validate.Struct(tt.tx)
			if (err != nil) != tt.wantErr {
				t.Errorf("Transaction.Validate() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
} 