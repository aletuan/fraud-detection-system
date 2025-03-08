package api

import (
	"context"
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
	handler := NewTransactionHandler(s.service)
	handler.RegisterRoutes(api)

	// Health check
	s.router.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
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