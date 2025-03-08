package kafka

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"os"
	"time"

	"github.com/IBM/sarama"
)

// Producer interface defines methods for publishing events
type Producer interface {
	// PublishEvent publishes an event to Kafka
	PublishEvent(ctx context.Context, event *TransactionEvent) error
	// Close closes the producer
	Close() error
}

// producer implements the Producer interface
type producer struct {
	config     Config
	syncProducer sarama.SyncProducer
}

// NewProducer creates a new Kafka producer
func NewProducer(config Config) (Producer, error) {
	if err := config.Validate(); err != nil {
		return nil, fmt.Errorf("invalid config: %w", err)
	}

	// Create Sarama config
	saramaConfig := sarama.NewConfig()

	// Set producer specific configuration
	saramaConfig.Producer.RequiredAcks = sarama.RequiredAcks(getRequiredAcks(config.RequiredAcks))
	saramaConfig.Producer.Compression = getCompressionCodec(config.Compression)
	saramaConfig.Producer.Retry.Max = config.MaxRetries
	saramaConfig.Producer.Retry.Backoff = config.RetryBackoff
	saramaConfig.Producer.Return.Successes = config.ProducerConfig.ReturnSuccesses

	// Set client configuration
	saramaConfig.ClientID = config.ClientID
	saramaConfig.Net.DialTimeout = config.Timeout
	saramaConfig.Net.ReadTimeout = config.Timeout
	saramaConfig.Net.WriteTimeout = config.Timeout
	saramaConfig.Net.MaxOpenRequests = 5
	saramaConfig.Net.KeepAlive = 30 * time.Second

	// Disable metadata auto refresh to prevent localhost resolution
	saramaConfig.Metadata.RefreshFrequency = 0
	saramaConfig.Metadata.Full = false
	saramaConfig.Metadata.Retry.Max = 0

	// Configure TLS if enabled
	if config.TLS.Enabled {
		tlsConfig, err := createTLSConfig(config.TLS)
		if err != nil {
			return nil, fmt.Errorf("failed to create TLS config: %w", err)
		}
		saramaConfig.Net.TLS.Enable = true
		saramaConfig.Net.TLS.Config = tlsConfig
	}

	// Configure SASL if enabled
	if config.SASL.Enabled {
		saramaConfig.Net.SASL.Enable = true
		saramaConfig.Net.SASL.Mechanism = sarama.SASLMechanism(config.SASL.Mechanism)
		saramaConfig.Net.SASL.User = config.SASL.Username
		saramaConfig.Net.SASL.Password = config.SASL.Password
	}

	// Create sync producer
	syncProducer, err := sarama.NewSyncProducer(config.Brokers, saramaConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create sync producer: %w", err)
	}

	return &producer{
		config:       config,
		syncProducer: syncProducer,
	}, nil
}

// PublishEvent publishes an event to Kafka
func (p *producer) PublishEvent(ctx context.Context, event *TransactionEvent) error {
	// Convert event to JSON
	value, err := event.ToJSON()
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	// Create message
	msg := &sarama.ProducerMessage{
		Topic:     p.config.Topic,
		Key:       sarama.StringEncoder(event.Transaction.ID), // Use transaction ID as key for partitioning
		Value:     sarama.ByteEncoder(value),
		Timestamp: event.OccurredAt,
		Headers: []sarama.RecordHeader{
			{
				Key:   []byte("event_type"),
				Value: []byte(event.EventType),
			},
			{
				Key:   []byte("version"),
				Value: []byte(event.Version),
			},
		},
	}

	// Add correlation ID if available
	if event.Metadata.CorrelationID != "" {
		msg.Headers = append(msg.Headers, sarama.RecordHeader{
			Key:   []byte("correlation_id"),
			Value: []byte(event.Metadata.CorrelationID),
		})
	}

	// Send message with context
	partition, offset, err := p.syncProducer.SendMessage(msg)
	if err != nil {
		return fmt.Errorf("failed to send message: %w", err)
	}

	// Log success (in production, use proper logging)
	fmt.Printf("Event published successfully - Topic: %s, Partition: %d, Offset: %d\n",
		p.config.Topic, partition, offset)

	return nil
}

// Close closes the producer
func (p *producer) Close() error {
	if err := p.syncProducer.Close(); err != nil {
		return fmt.Errorf("failed to close producer: %w", err)
	}
	return nil
}

// Helper functions

func getRequiredAcks(acks string) sarama.RequiredAcks {
	switch acks {
	case "no":
		return sarama.NoResponse
	case "local":
		return sarama.WaitForLocal
	case "all":
		return sarama.WaitForAll
	default:
		return sarama.WaitForAll
	}
}

func getCompressionCodec(compression string) sarama.CompressionCodec {
	switch compression {
	case "gzip":
		return sarama.CompressionGZIP
	case "snappy":
		return sarama.CompressionSnappy
	case "lz4":
		return sarama.CompressionLZ4
	case "zstd":
		return sarama.CompressionZSTD
	default:
		return sarama.CompressionNone
	}
}

func createTLSConfig(config struct {
	Enabled             bool
	CertFile           string
	KeyFile            string
	CAFile             string
	VerifySSL          bool
	InsecureSkipVerify bool
}) (*tls.Config, error) {
	tlsConfig := &tls.Config{
		InsecureSkipVerify: config.InsecureSkipVerify,
	}

	// Load client cert
	if config.CertFile != "" && config.KeyFile != "" {
		cert, err := tls.LoadX509KeyPair(config.CertFile, config.KeyFile)
		if err != nil {
			return nil, fmt.Errorf("failed to load client cert: %w", err)
		}
		tlsConfig.Certificates = []tls.Certificate{cert}
	}

	// Load CA cert
	if config.CAFile != "" {
		caCert, err := os.ReadFile(config.CAFile)
		if err != nil {
			return nil, fmt.Errorf("failed to read CA cert: %w", err)
		}

		caCertPool := x509.NewCertPool()
		if !caCertPool.AppendCertsFromPEM(caCert) {
			return nil, fmt.Errorf("failed to parse CA cert")
		}
		tlsConfig.RootCAs = caCertPool
	}

	return tlsConfig, nil
} 