package api

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gorilla/mux"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"go.mongodb.org/mongo-driver/bson/primitive"

	"transaction-service/internal/domain"
	"transaction-service/internal/service"
)

// MockTransactionService là một mock của TransactionService interface
type MockTransactionService struct {
	mock.Mock
}

func (m *MockTransactionService) CreateTransaction(ctx context.Context, input service.CreateTransactionInput) (*domain.Transaction, error) {
	args := m.Called(ctx, input)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransactionService) UpdateTransaction(ctx context.Context, id string, input service.UpdateTransactionInput) (*domain.Transaction, error) {
	args := m.Called(ctx, id, input)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransactionService) GetTransaction(ctx context.Context, id string) (*domain.Transaction, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*domain.Transaction), args.Error(1)
}

func (m *MockTransactionService) ListTransactions(ctx context.Context, params service.ListTransactionsParams) ([]domain.Transaction, int64, error) {
	args := m.Called(ctx, params)
	if args.Get(0) == nil {
		return nil, args.Get(1).(int64), args.Error(2)
	}
	return args.Get(0).([]domain.Transaction), args.Get(1).(int64), args.Error(2)
}

func (m *MockTransactionService) EnrichTransactionData(ctx context.Context, tx *domain.Transaction) error {
	args := m.Called(ctx, tx)
	return args.Error(0)
}

func (m *MockTransactionService) ProcessTransaction(ctx context.Context, tx *domain.Transaction) error {
	args := m.Called(ctx, tx)
	return args.Error(0)
}

func (m *MockTransactionService) PublishTransactionEvent(ctx context.Context, tx *domain.Transaction, eventType service.EventType) error {
	args := m.Called(ctx, tx, eventType)
	return args.Error(0)
}

func (m *MockTransactionService) ValidateTransaction(ctx context.Context, tx *domain.Transaction) error {
	args := m.Called(ctx, tx)
	return args.Error(0)
}

func TestCreateTransaction(t *testing.T) {
	mockService := new(MockTransactionService)
	handler := NewTransactionHandler(mockService)

	objID := primitive.NewObjectID()

	tests := []struct {
		name           string
		input         service.CreateTransactionInput
		mockResponse  *domain.Transaction
		mockError     error
		expectedCode  int
		expectedError string
	}{
		{
			name: "Tạo giao dịch thành công",
			input: service.CreateTransactionInput{
				AccountID: "acc123",
				Amount:    100.0,
				Currency: "USD",
			},
			mockResponse: &domain.Transaction{
				ID:        objID,
				AccountID: "acc123",
				Amount:    100.0,
				Currency: "USD",
				Status:   "PENDING",
			},
			mockError:    nil,
			expectedCode: http.StatusCreated,
		},
		{
			name: "Dữ liệu đầu vào không hợp lệ",
			input: service.CreateTransactionInput{},
			mockResponse: nil,
			mockError:    service.ErrInvalidInput,
			expectedCode: http.StatusBadRequest,
			expectedError: "invalid input data",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup mock
			mockService.On("CreateTransaction", mock.Anything, tt.input).Return(tt.mockResponse, tt.mockError)
			if tt.mockResponse != nil {
				mockService.On("ValidateTransaction", mock.Anything, tt.mockResponse).Return(nil)
				mockService.On("ProcessTransaction", mock.Anything, tt.mockResponse).Return(nil)
				mockService.On("PublishTransactionEvent", mock.Anything, tt.mockResponse, service.EventTypeCreated).Return(nil)
			}

			// Create request
			body, _ := json.Marshal(tt.input)
			req := httptest.NewRequest(http.MethodPost, "/transactions", bytes.NewBuffer(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			// Execute request
			handler.CreateTransaction(w, req)

			// Assert response
			assert.Equal(t, tt.expectedCode, w.Code)
			
			if tt.expectedError != "" {
				var response map[string]string
				json.NewDecoder(w.Body).Decode(&response)
				assert.Contains(t, response["error"], tt.expectedError)
			} else {
				var response domain.Transaction
				json.NewDecoder(w.Body).Decode(&response)
				assert.Equal(t, tt.mockResponse.ID, response.ID)
			}
		})
	}
}

func TestGetTransaction(t *testing.T) {
	mockService := new(MockTransactionService)
	handler := NewTransactionHandler(mockService)

	objID := primitive.NewObjectID()

	tests := []struct {
		name           string
		transactionID  string
		mockResponse   *domain.Transaction
		mockError      error
		expectedCode   int
		expectedError  string
	}{
		{
			name:          "Lấy giao dịch thành công",
			transactionID: objID.Hex(),
			mockResponse: &domain.Transaction{
				ID:        objID,
				AccountID: "acc123",
				Amount:    100.0,
				Status:    "COMPLETED",
			},
			mockError:     nil,
			expectedCode:  http.StatusOK,
		},
		{
			name:          "Giao dịch không tồn tại",
			transactionID: "invalid_id",
			mockResponse:  nil,
			mockError:     service.ErrTransactionNotFound,
			expectedCode:  http.StatusNotFound,
			expectedError: "transaction not found",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup mock
			mockService.On("GetTransaction", mock.Anything, tt.transactionID).Return(tt.mockResponse, tt.mockError)

			// Create request
			req := httptest.NewRequest(http.MethodGet, "/transactions/"+tt.transactionID, nil)
			req = mux.SetURLVars(req, map[string]string{"id": tt.transactionID})
			w := httptest.NewRecorder()

			// Execute request
			handler.GetTransaction(w, req)

			// Assert response
			assert.Equal(t, tt.expectedCode, w.Code)
			
			if tt.expectedError != "" {
				var response map[string]string
				json.NewDecoder(w.Body).Decode(&response)
				assert.Contains(t, response["error"], tt.expectedError)
			} else {
				var response domain.Transaction
				json.NewDecoder(w.Body).Decode(&response)
				assert.Equal(t, tt.mockResponse.ID, response.ID)
			}
		})
	}
}

func TestListTransactions(t *testing.T) {
	mockService := new(MockTransactionService)
	handler := NewTransactionHandler(mockService)

	objID := primitive.NewObjectID()

	tests := []struct {
		name          string
		queryParams   map[string]string
		mockResponse  []domain.Transaction
		mockTotal     int64
		mockError     error
		expectedCode  int
	}{
		{
			name: "Lấy danh sách giao dịch thành công",
			queryParams: map[string]string{
				"page": "1",
				"page_size": "10",
			},
			mockResponse: []domain.Transaction{
				{
					ID:        objID,
					AccountID: "acc123",
					Amount:    100.0,
					Status:    "COMPLETED",
				},
			},
			mockTotal:    1,
			mockError:    nil,
			expectedCode: http.StatusOK,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup mock
			mockService.On("ListTransactions", mock.Anything, mock.AnythingOfType("service.ListTransactionsParams")).
				Return(tt.mockResponse, tt.mockTotal, tt.mockError)

			// Create request with query parameters
			req := httptest.NewRequest(http.MethodGet, "/transactions", nil)
			q := req.URL.Query()
			for key, value := range tt.queryParams {
				q.Add(key, value)
			}
			req.URL.RawQuery = q.Encode()
			w := httptest.NewRecorder()

			// Execute request
			handler.ListTransactions(w, req)

			// Assert response
			assert.Equal(t, tt.expectedCode, w.Code)

			var response map[string]interface{}
			json.NewDecoder(w.Body).Decode(&response)
			
			transactions := response["transactions"].([]interface{})
			assert.Len(t, transactions, len(tt.mockResponse))
			assert.Equal(t, float64(tt.mockTotal), response["total"].(float64))
		})
	}
} 