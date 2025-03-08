package kafka

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"go.mongodb.org/mongo-driver/bson/primitive"

	"transaction-service/internal/domain"
)

func TestNewProducer(t *testing.T) {
	t.Run("Valid_Config", func(t *testing.T) {
		config := DefaultConfig()
		producer, err := NewProducer(config)
		assert.Error(t, err) // Should fail because Kafka is not running
		assert.Nil(t, producer)
	})

	t.Run("Invalid_Config", func(t *testing.T) {
		config := Config{} // Empty config
		producer, err := NewProducer(config)
		assert.Error(t, err)
		assert.Nil(t, producer)
	})
}

func TestTransactionEvent_ToJSON(t *testing.T) {
	t.Run("Valid_Event", func(t *testing.T) {
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
				"risk_score":       0.3,
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
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		event := NewTransactionEvent(EventTypeCreated, tx, EventMetadata{
			Source:        "test",
			CorrelationID: "corr123",
			UserID:        "user123",
		})

		jsonData, err := event.ToJSON()
		assert.NoError(t, err)
		assert.NotEmpty(t, jsonData)

		// Test deserialization
		decodedEvent, err := FromJSON(jsonData)
		assert.NoError(t, err)
		assert.Equal(t, event.EventType, decodedEvent.EventType)
		assert.Equal(t, event.Transaction.ID, decodedEvent.Transaction.ID)
		assert.Equal(t, event.Transaction.Amount, decodedEvent.Transaction.Amount)
		assert.Equal(t, event.Metadata.CorrelationID, decodedEvent.Metadata.CorrelationID)
	})
}

func TestTransactionEvent_FromJSON(t *testing.T) {
	t.Run("Invalid_JSON", func(t *testing.T) {
		invalidJSON := []byte(`{"invalid json"}`)
		event, err := FromJSON(invalidJSON)
		assert.Error(t, err)
		assert.Nil(t, event)
	})

	t.Run("Empty_JSON", func(t *testing.T) {
		emptyJSON := []byte(`{}`)
		event, err := FromJSON(emptyJSON)
		assert.NoError(t, err)
		assert.NotNil(t, event)
	})
}

func TestConfig_Validate(t *testing.T) {
	tests := []struct {
		name    string
		config  Config
		wantErr bool
	}{
		{
			name:    "Valid_Default_Config",
			config:  DefaultConfig(),
			wantErr: false,
		},
		{
			name:    "Empty_Config",
			config:  Config{},
			wantErr: true,
		},
		{
			name: "Invalid_TLS_Config",
			config: Config{
				Brokers:  []string{"localhost:9092"},
				Topic:    "test",
				ClientID: "test",
				TLS: struct {
					Enabled             bool
					CertFile           string
					KeyFile            string
					CAFile             string
					VerifySSL          bool
					InsecureSkipVerify bool
				}{
					Enabled:   true,
					CertFile: "", // Missing required field
				},
			},
			wantErr: true,
		},
		{
			name: "Invalid_SASL_Config",
			config: Config{
				Brokers:  []string{"localhost:9092"},
				Topic:    "test",
				ClientID: "test",
				SASL: struct {
					Enabled    bool
					Mechanism  string
					Username   string
					Password   string
				}{
					Enabled: true,
					// Missing required fields
				},
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := tt.config.Validate()
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
} 