package api

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"

	"transaction-service/internal/service"
)

// Server represents the HTTP server
type Server struct {
	router  *mux.Router
	server  *http.Server
	service service.TransactionService
}

// NewServer creates a new HTTP server
func NewServer(service service.TransactionService, port int) *Server {
	router := mux.NewRouter()
	
	server := &Server{
		router:  router,
		service: service,
		server: &http.Server{
			Addr:         fmt.Sprintf(":%d", port),
			Handler:      router,
			ReadTimeout:  15 * time.Second,
			WriteTimeout: 15 * time.Second,
			IdleTimeout:  60 * time.Second,
		},
	}

	server.setupRoutes()
	return server
}

// setupRoutes configures all the routes and middleware
func (s *Server) setupRoutes() {
	// Add middleware
	s.router.Use(RecoveryMiddleware)
	s.router.Use(LoggingMiddleware)
	s.router.Use(CORSMiddleware)
	s.router.Use(ContentTypeMiddleware)

	// Create API router
	api := s.router.PathPrefix("/api/v1").Subrouter()

	// Register transaction routes
	api.HandleFunc("/transactions/account/{id}", s.handleGetAccountTransactions).Methods(http.MethodGet)
	api.HandleFunc("/transactions", s.handleCreateTransaction).Methods(http.MethodPost)
	api.HandleFunc("/transactions", s.handleListTransactions).Methods(http.MethodGet)
	api.HandleFunc("/transactions/{id}", s.handleGetTransaction).Methods(http.MethodGet)
	api.HandleFunc("/transactions/{id}", s.handleUpdateTransaction).Methods(http.MethodPut)

	// Health check
	s.router.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
}

// handleCreateTransaction handles transaction creation
func (s *Server) handleCreateTransaction(w http.ResponseWriter, r *http.Request) {
	var input service.CreateTransactionInput
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	tx, err := s.service.CreateTransaction(r.Context(), input)
	if err != nil {
		switch err {
		case service.ErrInvalidInput:
			writeError(w, http.StatusBadRequest, err.Error())
		case service.ErrDuplicateTransaction:
			writeError(w, http.StatusConflict, err.Error())
		default:
			writeError(w, http.StatusInternalServerError, "Failed to create transaction")
		}
		return
	}

	writeJSON(w, http.StatusCreated, tx)
}

// handleGetTransaction handles getting a single transaction
func (s *Server) handleGetTransaction(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	tx, err := s.service.GetTransaction(r.Context(), id)
	if err != nil {
		switch err {
		case service.ErrTransactionNotFound:
			writeError(w, http.StatusNotFound, "Transaction not found")
		default:
			writeError(w, http.StatusInternalServerError, "Failed to get transaction")
		}
		return
	}

	writeJSON(w, http.StatusOK, tx)
}

// handleListTransactions handles listing transactions
func (s *Server) handleListTransactions(w http.ResponseWriter, r *http.Request) {
	params := service.ListTransactionsParams{
		Page:     1,
		PageSize: 10,
		SortBy:   "created_at",
		SortDesc: true,
	}

	// Parse query parameters
	if page := r.URL.Query().Get("page"); page != "" {
		fmt.Sscanf(page, "%d", &params.Page)
	}
	if pageSize := r.URL.Query().Get("page_size"); pageSize != "" {
		fmt.Sscanf(pageSize, "%d", &params.PageSize)
	}
	if sortBy := r.URL.Query().Get("sort_by"); sortBy != "" {
		params.SortBy = sortBy
	}
	if sortDesc := r.URL.Query().Get("sort_desc"); sortDesc == "false" {
		params.SortDesc = false
	}

	transactions, total, err := s.service.ListTransactions(r.Context(), params)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Failed to list transactions")
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"data": transactions,
		"total": total,
		"page": params.Page,
		"page_size": params.PageSize,
	})
}

// handleUpdateTransaction handles updating a transaction
func (s *Server) handleUpdateTransaction(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	var input service.UpdateTransactionInput
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	tx, err := s.service.UpdateTransaction(r.Context(), id, input)
	if err != nil {
		switch err {
		case service.ErrTransactionNotFound:
			writeError(w, http.StatusNotFound, "Transaction not found")
		case service.ErrInvalidInput:
			writeError(w, http.StatusBadRequest, err.Error())
		case service.ErrInvalidStatus:
			writeError(w, http.StatusBadRequest, err.Error())
		default:
			writeError(w, http.StatusInternalServerError, "Failed to update transaction")
		}
		return
	}

	writeJSON(w, http.StatusOK, tx)
}

// handleGetAccountTransactions handles getting transactions for an account
func (s *Server) handleGetAccountTransactions(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	accountID := vars["id"]

	params := service.ListTransactionsParams{
		AccountID: accountID,
		Page:     1,
		PageSize: 10,
		SortBy:   "created_at",
		SortDesc: true,
	}

	// Parse query parameters
	if page := r.URL.Query().Get("page"); page != "" {
		fmt.Sscanf(page, "%d", &params.Page)
	}
	if pageSize := r.URL.Query().Get("page_size"); pageSize != "" {
		fmt.Sscanf(pageSize, "%d", &params.PageSize)
	}
	if sortBy := r.URL.Query().Get("sort_by"); sortBy != "" {
		params.SortBy = sortBy
	}
	if sortDesc := r.URL.Query().Get("sort_desc"); sortDesc == "false" {
		params.SortDesc = false
	}

	transactions, total, err := s.service.ListTransactions(r.Context(), params)
	if err != nil {
		writeError(w, http.StatusInternalServerError, "Failed to get account transactions")
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"data": transactions,
		"total": total,
		"page": params.Page,
		"page_size": params.PageSize,
	})
}

// Start starts the HTTP server
func (s *Server) Start() error {
	// Start server in a goroutine
	go func() {
		log.Printf("Starting server on %s", s.server.Addr)
		if err := s.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server error: %v", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	// Shutdown gracefully
	log.Println("Shutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := s.server.Shutdown(ctx); err != nil {
		return fmt.Errorf("server shutdown error: %v", err)
	}

	log.Println("Server stopped gracefully")
	return nil
}

// Stop stops the HTTP server
func (s *Server) Stop(ctx context.Context) error {
	return s.server.Shutdown(ctx)
} 