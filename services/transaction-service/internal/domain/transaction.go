package domain

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

// TransactionType định nghĩa loại giao dịch
type TransactionType string

const (
	TransactionTypeDebit  TransactionType = "DEBIT"
	TransactionTypeCredit TransactionType = "CREDIT"
)

// TransactionStatus định nghĩa trạng thái giao dịch
type TransactionStatus string

const (
	StatusPending   TransactionStatus = "PENDING"
	StatusCompleted TransactionStatus = "COMPLETED"
	StatusFailed    TransactionStatus = "FAILED"
)

// Transaction đại diện cho một giao dịch
type Transaction struct {
	ID            primitive.ObjectID     `bson:"_id" json:"id"`
	AccountID     string                `bson:"account_id" json:"account_id" validate:"required"`
	Amount        float64               `bson:"amount" json:"amount" validate:"required,gt=0"`
	Currency      string                `bson:"currency" json:"currency" validate:"required,len=3"`
	Type          TransactionType       `bson:"type" json:"type" validate:"required,oneof=DEBIT CREDIT"`
	Status        TransactionStatus     `bson:"status" json:"status"`
	ReferenceID   string                `bson:"reference_id" json:"reference_id" validate:"required"`
	Description   string                `bson:"description,omitempty" json:"description,omitempty"`
	MerchantID    string                `bson:"merchant_id,omitempty" json:"merchant_id,omitempty"`
	MerchantName  string                `bson:"merchant_name,omitempty" json:"merchant_name,omitempty"`
	Location      *Location             `bson:"location,omitempty" json:"location,omitempty"`
	DeviceInfo    *DeviceInfo           `bson:"device_info,omitempty" json:"device_info,omitempty"`
	Metadata      map[string]interface{} `bson:"metadata,omitempty" json:"metadata,omitempty"`
	CreatedAt     time.Time             `bson:"created_at" json:"created_at"`
	UpdatedAt     time.Time             `bson:"updated_at" json:"updated_at"`
}

// Location chứa thông tin về vị trí giao dịch
type Location struct {
	Country     string  `bson:"country" json:"country"`
	City        string  `bson:"city,omitempty" json:"city,omitempty"`
	PostalCode  string  `bson:"postal_code,omitempty" json:"postal_code,omitempty"`
	Coordinates *Coordinates `bson:"coordinates,omitempty" json:"coordinates,omitempty"`
}

// Coordinates chứa thông tin về tọa độ
type Coordinates struct {
	Latitude  float64 `bson:"latitude" json:"latitude"`
	Longitude float64 `bson:"longitude" json:"longitude"`
}

// DeviceInfo chứa thông tin về thiết bị thực hiện giao dịch
type DeviceInfo struct {
	DeviceID    string `bson:"device_id,omitempty" json:"device_id,omitempty"`
	DeviceType  string `bson:"device_type" json:"device_type"`
	BrowserType string `bson:"browser_type" json:"browser_type"`
	DeviceOS    string `bson:"device_os" json:"device_os"`
	IsMobile    bool   `bson:"is_mobile" json:"is_mobile"`
	IPAddress   string `bson:"ip_address,omitempty" json:"ip_address,omitempty"`
	UserAgent   string `bson:"user_agent,omitempty" json:"user_agent,omitempty"`
} 