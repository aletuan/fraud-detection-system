package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"sync"
	"time"
)

type LogEntry struct {
	Timestamp  string      `json:"timestamp"`
	Method     string      `json:"method"`
	Path       string      `json:"path"`
	Status     int         `json:"status"`
	Duration   string      `json:"duration"`
	IP         string      `json:"ip"`
	UserAgent  string      `json:"user_agent"`
	ServerName string      `json:"server_name"`
	Payload    interface{} `json:"payload,omitempty"`
}

type logstashConnection struct {
	conn     net.Conn
	mu       sync.Mutex
	host     string
	port     string
	lastTry  time.Time
	retryInt time.Duration
}

func newLogstashConnection(host, port string) *logstashConnection {
	return &logstashConnection{
		host:     host,
		port:     port,
		retryInt: 5 * time.Second,
	}
}

func (lc *logstashConnection) getConnection() net.Conn {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	// If we have a connection and it's working, return it
	if lc.conn != nil {
		return lc.conn
	}

	// If we recently tried to connect and failed, wait before trying again
	if time.Since(lc.lastTry) < lc.retryInt {
		return nil
	}

	// Try to establish a new connection
	lc.lastTry = time.Now()
	conn, err := net.Dial("tcp", lc.host+":"+lc.port)
	if err != nil {
		log.Printf("Failed to connect to Logstash: %v", err)
		return nil
	}

	lc.conn = conn
	return conn
}

func (lc *logstashConnection) write(data []byte) error {
	conn := lc.getConnection()
	if conn == nil {
		return fmt.Errorf("no connection to Logstash available")
	}

	data = append(data, '\n')
	_, err := conn.Write(data)
	if err != nil {
		// Connection might be broken, clear it so we'll try to reconnect next time
		lc.mu.Lock()
		lc.conn = nil
		lc.mu.Unlock()
	}
	return err
}

// LoggingMiddleware logs request information
func LoggingMiddleware(next http.Handler) http.Handler {
	hostname, _ := os.Hostname()
	logstashConn := newLogstashConnection(
		os.Getenv("LOGSTASH_HOST"),
		os.Getenv("LOGSTASH_PORT"),
	)

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Create a custom response writer to capture status code
		rw := &responseWriter{
			ResponseWriter: w,
			status:         http.StatusOK,
		}

		// Read and parse request body for non-GET requests
		var payload interface{}
		if r.Method != http.MethodGet && r.ContentLength > 0 {
			if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
				log.Printf("Failed to read request body: %v", err)
			}
			// Create a new reader with the same data for the next handler
			jsonData, _ := json.Marshal(payload)
			r.Body = io.NopCloser(bytes.NewBuffer(jsonData))
		}

		// Call the next handler
		next.ServeHTTP(rw, r)

		// Create log entry
		entry := LogEntry{
			Timestamp:  time.Now().UTC().Format(time.RFC3339Nano),
			Method:     r.Method,
			Path:       r.URL.Path,
			Status:     rw.status,
			Duration:   time.Since(start).String(),
			IP:         r.RemoteAddr,
			UserAgent:  r.UserAgent(),
			ServerName: hostname,
			Payload:    payload,
		}

		// Convert to JSON
		jsonEntry, err := json.Marshal(entry)
		if err != nil {
			log.Printf("Failed to marshal log entry: %v", err)
			return
		}

		// Send to Logstash
		if err := logstashConn.write(jsonEntry); err != nil {
			log.Printf("Failed to send log to Logstash: %v", err)
		}

		// Also log to stdout
		log.Printf(
			"Method: %s, Path: %s, Status: %d, Duration: %v, IP: %s, UserAgent: %s, Server: %s",
			entry.Method,
			entry.Path,
			entry.Status,
			entry.Duration,
			entry.IP,
			entry.UserAgent,
			entry.ServerName,
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
