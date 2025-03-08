package kafka

import (
	"encoding/json"
	"time"

	"transaction-service/internal/domain"
)

// EventType defines the type of transaction event
type EventType string

const (
	// Event types
	EventTypeCreated   EventType = "TRANSACTION.CREATED"
	EventTypeUpdated   EventType = "TRANSACTION.UPDATED"
	EventTypeCompleted EventType = "TRANSACTION.COMPLETED"
	EventTypeFailed    EventType = "TRANSACTION.FAILED"
	EventTypeRejected  EventType = "TRANSACTION.REJECTED"
)

// TransactionEvent represents a transaction event to be published to Kafka
type TransactionEvent struct {
	EventID     string          `json:"event_id"`
	EventType   EventType       `json:"event_type"`
	Version     string          `json:"version"`
	OccurredAt  time.Time      `json:"occurred_at"`
	Transaction TransactionData `json:"transaction"`
	Metadata    EventMetadata   `json:"metadata,omitempty"`
}

// TransactionData contains the transaction information
type TransactionData struct {
	ID            string                 `json:"id"`
	AccountID     string                 `json:"account_id"`
	Amount        float64               `json:"amount"`
	Currency      string                `json:"currency"`
	Type          string                `json:"type"`
	Status        string                `json:"status"`
	ReferenceID   string                `json:"reference_id"`
	Description   string                `json:"description,omitempty"`
	MerchantID    string                `json:"merchant_id,omitempty"`
	MerchantName  string                `json:"merchant_name,omitempty"`
	Location      *LocationData         `json:"location,omitempty"`
	DeviceInfo    *DeviceData           `json:"device_info,omitempty"`
	RiskScore     float64               `json:"risk_score,omitempty"`
	ValidationErrors []ValidationError   `json:"validation_errors,omitempty"`
	CreatedAt     time.Time             `json:"created_at"`
	UpdatedAt     time.Time             `json:"updated_at"`
}

// LocationData contains location information
type LocationData struct {
	Country     string  `json:"country"`
	City        string  `json:"city,omitempty"`
	PostalCode  string  `json:"postal_code,omitempty"`
	Coordinates struct {
		Latitude  float64 `json:"latitude,omitempty"`
		Longitude float64 `json:"longitude,omitempty"`
	} `json:"coordinates,omitempty"`
}

// DeviceData contains device information
type DeviceData struct {
	DeviceID    string `json:"device_id,omitempty"`
	DeviceType  string `json:"device_type"`
	BrowserType string `json:"browser_type"`
	DeviceOS    string `json:"device_os"`
	IsMobile    bool   `json:"is_mobile"`
	IPAddress   string `json:"ip_address,omitempty"`
	UserAgent   string `json:"user_agent,omitempty"`
}

// ValidationError represents a validation error
type ValidationError struct {
	Field   string `json:"field"`
	Code    string `json:"code"`
	Message string `json:"message"`
}

// EventMetadata contains additional event metadata
type EventMetadata struct {
	Source        string                 `json:"source"`
	CorrelationID string                 `json:"correlation_id,omitempty"`
	UserID        string                 `json:"user_id,omitempty"`
	Additional    map[string]interface{} `json:"additional,omitempty"`
}

// NewTransactionEvent creates a new transaction event
func NewTransactionEvent(eventType EventType, tx *domain.Transaction, metadata EventMetadata) *TransactionEvent {
	event := &TransactionEvent{
		EventID:    tx.ID.Hex(), // Use transaction ID as event ID
		EventType:  eventType,
		Version:    "1.0",
		OccurredAt: time.Now(),
		Metadata:   metadata,
	}

	// Convert domain.Transaction to TransactionData
	event.Transaction = TransactionData{
		ID:          tx.ID.Hex(),
		AccountID:   tx.AccountID,
		Amount:      tx.Amount,
		Currency:    tx.Currency,
		Type:        string(tx.Type),
		Status:      string(tx.Status),
		ReferenceID: tx.ReferenceID,
		Description: tx.Description,
		MerchantID:  tx.MerchantID,
		MerchantName: tx.MerchantName,
		CreatedAt:   tx.CreatedAt,
		UpdatedAt:   tx.UpdatedAt,
	}

	// Convert Location if exists
	if tx.Location != nil {
		event.Transaction.Location = &LocationData{
			Country: tx.Location.Country,
			City:    tx.Location.City,
		}
		if tx.Location.Coordinates != nil {
			event.Transaction.Location.Coordinates.Latitude = tx.Location.Coordinates.Latitude
			event.Transaction.Location.Coordinates.Longitude = tx.Location.Coordinates.Longitude
		}
	}

	// Convert DeviceInfo if exists
	if tx.DeviceInfo != nil {
		event.Transaction.DeviceInfo = &DeviceData{
			DeviceType:  tx.DeviceInfo.DeviceType,
			BrowserType: tx.DeviceInfo.BrowserType,
			DeviceOS:    tx.DeviceInfo.DeviceOS,
			IsMobile:    tx.DeviceInfo.IsMobile,
			IPAddress:   tx.DeviceInfo.IPAddress,
			UserAgent:   tx.DeviceInfo.UserAgent,
		}
	}

	// Add risk score and validation errors if available
	if tx.Metadata != nil {
		if score, ok := tx.Metadata["risk_score"].(float64); ok {
			event.Transaction.RiskScore = score
		}
		if errors, ok := tx.Metadata["validation_errors"].([]domain.ValidationError); ok {
			for _, err := range errors {
				event.Transaction.ValidationErrors = append(event.Transaction.ValidationErrors, ValidationError{
					Field:   err.Field,
					Code:    err.Code,
					Message: err.Message,
				})
			}
		}
	}

	return event
}

// ToJSON converts the event to JSON bytes
func (e *TransactionEvent) ToJSON() ([]byte, error) {
	return json.Marshal(e)
}

// FromJSON creates an event from JSON bytes
func FromJSON(data []byte) (*TransactionEvent, error) {
	var event TransactionEvent
	if err := json.Unmarshal(data, &event); err != nil {
		return nil, err
	}
	return &event, nil
} 