package api

import (
	"log"
	"net/http"
	"time"
)

// LoggingMiddleware logs request information
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create a custom response writer to capture status code
		rw := &responseWriter{
			ResponseWriter: w,
			status:        http.StatusOK,
		}

		// Call the next handler
		next.ServeHTTP(rw, r)

		// Log request details
		log.Printf(
			"Method: %s, Path: %s, Status: %d, Duration: %v, IP: %s, UserAgent: %s",
			r.Method,
			r.URL.Path,
			rw.status,
			time.Since(start),
			r.RemoteAddr,
			r.UserAgent(),
		)
	})
}

// RecoveryMiddleware recovers from panics and returns 500 error
func RecoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				log.Printf("Panic recovered: %v", err)
				writeError(w, http.StatusInternalServerError, "Internal server error")
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// Custom response writer to capture status code
type responseWriter struct {
	http.ResponseWriter
	status int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.status = code
	rw.ResponseWriter.WriteHeader(code)
}

// CORSMiddleware handles Cross-Origin Resource Sharing
func CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set CORS headers
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		// Handle preflight requests
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// ContentTypeMiddleware ensures JSON content type
func ContentTypeMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip content type check for GET and OPTIONS requests
		if r.Method != http.MethodGet && r.Method != http.MethodOptions {
			contentType := r.Header.Get("Content-Type")
			if contentType != "application/json" {
				writeError(w, http.StatusUnsupportedMediaType, "Content-Type must be application/json")
				return
			}
		}

		next.ServeHTTP(w, r)
	})
} 