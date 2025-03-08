package kafka

import (
	"fmt"
	"time"
)

// Config contains Kafka producer configuration
type Config struct {
	// Basic configuration
	Brokers        []string
	Topic          string
	ClientID       string
	MaxMessageSize int
	Timeout        time.Duration

	// Producer specific configuration
	Compression     string
	RequiredAcks    string
	MaxRetries      int
	RetryBackoff    time.Duration
	FlushFrequency  time.Duration
	FlushMessages   int
	FlushBytes      int

	// TLS configuration
	TLS struct {
		Enabled             bool
		CertFile           string
		KeyFile            string
		CAFile             string
		VerifySSL          bool
		InsecureSkipVerify bool
	}

	// SASL configuration
	SASL struct {
		Enabled    bool
		Mechanism  string
		Username   string
		Password   string
	}

	// Add Producer.Return.Successes
	ProducerConfig struct {
		ReturnSuccesses bool
	}
}

// DefaultConfig returns default configuration
func DefaultConfig() Config {
	return Config{
		Brokers:        []string{"kafka:29092"},
		Topic:          "transactions",
		ClientID:       "transaction-service",
		MaxMessageSize: 1000000, // 1MB
		Timeout:        10 * time.Second,

		Compression:    "snappy",
		RequiredAcks:   "all", // -1
		MaxRetries:     3,
		RetryBackoff:   100 * time.Millisecond,
		FlushFrequency: 500 * time.Millisecond,
		FlushMessages:  100,
		FlushBytes:     1000000, // 1MB,
		
		// Add Producer.Return.Successes
		ProducerConfig: struct {
			ReturnSuccesses bool
		}{
			ReturnSuccesses: true,
		},
	}
}

// Validate validates the configuration
func (c *Config) Validate() error {
	if len(c.Brokers) == 0 {
		return fmt.Errorf("at least one broker is required")
	}
	if c.Topic == "" {
		return fmt.Errorf("topic is required")
	}
	if c.ClientID == "" {
		return fmt.Errorf("client ID is required")
	}
	if c.MaxMessageSize <= 0 {
		return fmt.Errorf("max message size must be positive")
	}
	if c.Timeout <= 0 {
		return fmt.Errorf("timeout must be positive")
	}
	if c.MaxRetries < 0 {
		return fmt.Errorf("max retries cannot be negative")
	}
	if c.RetryBackoff <= 0 {
		return fmt.Errorf("retry backoff must be positive")
	}
	if c.FlushFrequency <= 0 {
		return fmt.Errorf("flush frequency must be positive")
	}
	if c.FlushMessages <= 0 {
		return fmt.Errorf("flush messages must be positive")
	}
	if c.FlushBytes <= 0 {
		return fmt.Errorf("flush bytes must be positive")
	}

	// Validate TLS configuration
	if c.TLS.Enabled {
		if c.TLS.CertFile == "" {
			return fmt.Errorf("TLS cert file is required when TLS is enabled")
		}
		if c.TLS.KeyFile == "" {
			return fmt.Errorf("TLS key file is required when TLS is enabled")
		}
		if c.TLS.CAFile == "" && !c.TLS.InsecureSkipVerify {
			return fmt.Errorf("TLS CA file is required when TLS is enabled and verify SSL is true")
		}
	}

	// Validate SASL configuration
	if c.SASL.Enabled {
		if c.SASL.Mechanism == "" {
			return fmt.Errorf("SASL mechanism is required when SASL is enabled")
		}
		if c.SASL.Username == "" {
			return fmt.Errorf("SASL username is required when SASL is enabled")
		}
		if c.SASL.Password == "" {
			return fmt.Errorf("SASL password is required when SASL is enabled")
		}
	}

	return nil
} 