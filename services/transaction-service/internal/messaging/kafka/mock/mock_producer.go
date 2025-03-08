package mock

import (
	"context"
	"github.com/stretchr/testify/mock"
	"transaction-service/internal/messaging/kafka"
)

// MockProducer is a mock implementation of kafka.Producer interface
type MockProducer struct {
	mock.Mock
}

// PublishEvent mocks the PublishEvent method
func (m *MockProducer) PublishEvent(ctx context.Context, event *kafka.TransactionEvent) error {
	args := m.Called(ctx, event)
	return args.Error(0)
}

// Close mocks the Close method
func (m *MockProducer) Close() error {
	args := m.Called()
	return args.Error(0)
} 