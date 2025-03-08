package domain

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

// TransactionType represents the type of transaction
type TransactionType string

const (
	TransactionTypeDebit  TransactionType = "debit"
	TransactionTypeCredit TransactionType = "credit"
)

// TransactionStatus represents the status of transaction
type TransactionStatus string

const (
	StatusPending   TransactionStatus = "pending"
	StatusCompleted TransactionStatus = "completed"
	StatusFailed    TransactionStatus = "failed"
)

// Transaction represents a financial transaction
type Transaction struct {
	ID              primitive.ObjectID `json:"id" bson:"_id,omitempty"`
	AccountID       string            `json:"account_id" bson:"account_id" validate:"required"`
	Amount          float64           `json:"amount" bson:"amount" validate:"required,gt=0"`
	Currency        string            `json:"currency" bson:"currency" validate:"required,len=3"`
	Type            TransactionType   `json:"type" bson:"type" validate:"required,oneof=debit credit"`
	Status          TransactionStatus `json:"status" bson:"status" validate:"required"`
	Description     string            `json:"description" bson:"description"`
	MerchantID      string            `json:"merchant_id" bson:"merchant_id"`
	MerchantName    string            `json:"merchant_name" bson:"merchant_name"`
	Location        *Location         `json:"location,omitempty" bson:"location,omitempty"`
	DeviceInfo      *DeviceInfo       `json:"device_info,omitempty" bson:"device_info,omitempty"`
	ReferenceID     string            `json:"reference_id" bson:"reference_id" validate:"required"`
	Metadata        map[string]interface{} `bson:"metadata,omitempty" json:"metadata,omitempty"`
	CreatedAt       time.Time         `json:"created_at" bson:"created_at"`
	UpdatedAt       time.Time         `json:"updated_at" bson:"updated_at"`
}

// Location represents the geographical location of the transaction
type Location struct {
	Latitude  float64 `json:"latitude" bson:"latitude"`
	Longitude float64 `json:"longitude" bson:"longitude"`
	City      string  `json:"city" bson:"city"`
	Country   string  `json:"country" bson:"country"`
	IP        string  `json:"ip" bson:"ip"`
}

// DeviceInfo represents information about the device used for the transaction
type DeviceInfo struct {
	DeviceID     string `json:"device_id" bson:"device_id"`
	DeviceType   string `json:"device_type" bson:"device_type"`
	DeviceOS     string `json:"device_os" bson:"device_os"`
	DeviceBrand  string `json:"device_brand" bson:"device_brand"`
	BrowserType  string `json:"browser_type" bson:"browser_type"`
	IsMobile     bool   `json:"is_mobile" bson:"is_mobile"`
} 