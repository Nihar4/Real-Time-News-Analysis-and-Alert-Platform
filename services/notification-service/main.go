package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/smtp"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/segmentio/kafka-go"
)

// Config holds the service configuration
type Config struct {
	KafkaBootstrapServers string
	KafkaTopic            string
	KafkaConsumerGroup    string
	RedisAddr             string
	RedisPassword         string
	SMTPHost              string
	SMTPPort              string
	SMTPUser              string
	SMTPPassword          string
	FromEmail             string
}

// Event represents an enriched news event from the pipeline
type Event struct {
	ArticleID       string   `json:"article_id"`
	Title           string   `json:"title"`
	URL             string   `json:"url"`
	PrimaryCompany  string   `json:"primary_company"`
	EventType       string   `json:"event_type"`
	HeadlineSummary string   `json:"headline_summary"`
	ShortSummary    string   `json:"short_summary"`
	Sentiment       string   `json:"sentiment"`
	RiskScore       int      `json:"risk_score"`
	Tags            []string `json:"tags"`
	IsDuplicate     bool     `json:"is_duplicate"`
	EventID         string   `json:"event_id"`
}

// UserPreference represents a user's notification preferences
type UserPreference struct {
	UserID    string   `json:"user_id"`
	Email     string   `json:"email"`
	Companies []string `json:"companies"`
	EventTypes []string `json:"event_types"`
	MinRiskScore int   `json:"min_risk_score"`
}

// NotificationService handles real-time event notifications
type NotificationService struct {
	config      Config
	kafkaReader *kafka.Reader
	redisClient *redis.Client
	ctx         context.Context
	cancel      context.CancelFunc
}

// NewNotificationService creates a new notification service instance
func NewNotificationService(cfg Config) *NotificationService {
	ctx, cancel := context.WithCancel(context.Background())
	
	// Initialize Kafka reader
	kafkaReader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  strings.Split(cfg.KafkaBootstrapServers, ","),
		Topic:    cfg.KafkaTopic,
		GroupID:  cfg.KafkaConsumerGroup,
		MinBytes: 10e3, // 10KB
		MaxBytes: 10e6, // 10MB
	})
	
	// Initialize Redis client
	redisClient := redis.NewClient(&redis.Options{
		Addr:     cfg.RedisAddr,
		Password: cfg.RedisPassword,
		DB:       0,
	})
	
	return &NotificationService{
		config:      cfg,
		kafkaReader: kafkaReader,
		redisClient: redisClient,
		ctx:         ctx,
		cancel:      cancel,
	}
}

// isDuplicateNotification checks if we've already sent a notification for this event
func (s *NotificationService) isDuplicateNotification(eventID, userID string) bool {
	key := fmt.Sprintf("notification:sent:%s:%s", eventID, userID)
	exists, err := s.redisClient.Exists(s.ctx, key).Result()
	if err != nil {
		log.Printf("Redis error checking duplicate: %v", err)
		return false
	}
	return exists > 0
}

// markNotificationSent marks a notification as sent in Redis with TTL
func (s *NotificationService) markNotificationSent(eventID, userID string) {
	key := fmt.Sprintf("notification:sent:%s:%s", eventID, userID)
	// Set with 24-hour TTL to prevent duplicate notifications
	s.redisClient.Set(s.ctx, key, "1", 24*time.Hour)
}

// getUserPreferences fetches user preferences from Redis cache
func (s *NotificationService) getUserPreferences() ([]UserPreference, error) {
	// In production, this would fetch from database or Redis cache
	// For demo, returning mock preferences
	key := "user:preferences:all"
	data, err := s.redisClient.Get(s.ctx, key).Result()
	if err == redis.Nil {
		// Return default preferences for demo
		return []UserPreference{
			{
				UserID:       "user-1",
				Email:        "user@example.com",
				Companies:    []string{"Apple", "Google", "Microsoft"},
				EventTypes:   []string{"acquisition", "product_launch", "partnership"},
				MinRiskScore: 5,
			},
		}, nil
	} else if err != nil {
		return nil, err
	}
	
	var prefs []UserPreference
	if err := json.Unmarshal([]byte(data), &prefs); err != nil {
		return nil, err
	}
	return prefs, nil
}

// matchesUserPreferences checks if an event matches user's notification preferences
func (s *NotificationService) matchesUserPreferences(event Event, pref UserPreference) bool {
	// Skip duplicates
	if event.IsDuplicate {
		return false
	}
	
	// Check company match
	companyMatch := false
	for _, company := range pref.Companies {
		if strings.EqualFold(event.PrimaryCompany, company) {
			companyMatch = true
			break
		}
	}
	if !companyMatch && len(pref.Companies) > 0 {
		return false
	}
	
	// Check event type match
	eventTypeMatch := false
	for _, et := range pref.EventTypes {
		if strings.EqualFold(event.EventType, et) {
			eventTypeMatch = true
			break
		}
	}
	if !eventTypeMatch && len(pref.EventTypes) > 0 {
		return false
	}
	
	// Check risk score threshold
	if event.RiskScore < pref.MinRiskScore {
		return false
	}
	
	return true
}

// sendEmailNotification sends an email notification for an event
func (s *NotificationService) sendEmailNotification(event Event, pref UserPreference) error {
	// Email content
	subject := fmt.Sprintf("[Alert] %s: %s", event.PrimaryCompany, event.EventType)
	body := fmt.Sprintf(`
New Event Detected!

Company: %s
Event Type: %s
Sentiment: %s
Risk Score: %d

Summary:
%s

Read more: %s

---
Real-Time News Analysis Platform
`, event.PrimaryCompany, event.EventType, event.Sentiment, event.RiskScore, event.ShortSummary, event.URL)

	// SMTP authentication
	auth := smtp.PlainAuth("", s.config.SMTPUser, s.config.SMTPPassword, s.config.SMTPHost)
	
	// Compose message
	msg := []byte(fmt.Sprintf("To: %s\r\nSubject: %s\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n%s",
		pref.Email, subject, body))
	
	// Send email
	addr := fmt.Sprintf("%s:%s", s.config.SMTPHost, s.config.SMTPPort)
	err := smtp.SendMail(addr, auth, s.config.FromEmail, []string{pref.Email}, msg)
	if err != nil {
		return fmt.Errorf("failed to send email: %w", err)
	}
	
	log.Printf("Email sent to %s for event %s", pref.Email, event.EventID)
	return nil
}

// processEvent processes a single event and sends notifications
func (s *NotificationService) processEvent(event Event) {
	// Skip duplicate events
	if event.IsDuplicate {
		log.Printf("Skipping duplicate event: %s", event.ArticleID)
		return
	}
	
	// Get all user preferences
	preferences, err := s.getUserPreferences()
	if err != nil {
		log.Printf("Error fetching user preferences: %v", err)
		return
	}
	
	// Check each user's preferences
	for _, pref := range preferences {
		// Check if we've already sent this notification
		if s.isDuplicateNotification(event.EventID, pref.UserID) {
			log.Printf("Skipping duplicate notification for user %s, event %s", pref.UserID, event.EventID)
			continue
		}
		
		// Check if event matches user preferences
		if s.matchesUserPreferences(event, pref) {
			// Send notification
			if err := s.sendEmailNotification(event, pref); err != nil {
				log.Printf("Error sending notification: %v", err)
				continue
			}
			
			// Mark as sent to prevent duplicates
			s.markNotificationSent(event.EventID, pref.UserID)
		}
	}
}

// Run starts the notification service
func (s *NotificationService) Run() {
	log.Println("Starting Notification Service...")
	log.Printf("Consuming from Kafka topic: %s", s.config.KafkaTopic)
	
	// Graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	
	go func() {
		<-sigChan
		log.Println("Shutting down notification service...")
		s.cancel()
	}()
	
	// Main consumption loop
	for {
		select {
		case <-s.ctx.Done():
			return
		default:
			msg, err := s.kafkaReader.ReadMessage(s.ctx)
			if err != nil {
				if s.ctx.Err() != nil {
					return // Context cancelled
				}
				log.Printf("Error reading message: %v", err)
				continue
			}
			
			// Parse event
			var event Event
			if err := json.Unmarshal(msg.Value, &event); err != nil {
				log.Printf("Error parsing event: %v", err)
				continue
			}
			
			log.Printf("Processing event: %s - %s", event.PrimaryCompany, event.EventType)
			
			// Process and send notifications
			s.processEvent(event)
		}
	}
}

// Close cleans up resources
func (s *NotificationService) Close() {
	s.kafkaReader.Close()
	s.redisClient.Close()
}

func main() {
	// Load configuration from environment
	cfg := Config{
		KafkaBootstrapServers: getEnv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
		KafkaTopic:            getEnv("KAFKA_TOPIC", "news.deduped"),
		KafkaConsumerGroup:    getEnv("KAFKA_CONSUMER_GROUP", "notification-service-group"),
		RedisAddr:             getEnv("REDIS_ADDR", "localhost:6379"),
		RedisPassword:         getEnv("REDIS_PASSWORD", ""),
		SMTPHost:              getEnv("SMTP_HOST", "smtp.gmail.com"),
		SMTPPort:              getEnv("SMTP_PORT", "587"),
		SMTPUser:              getEnv("SMTP_USER", ""),
		SMTPPassword:          getEnv("SMTP_PASSWORD", ""),
		FromEmail:             getEnv("FROM_EMAIL", "alerts@newsplatform.com"),
	}
	
	// Create and run service
	service := NewNotificationService(cfg)
	defer service.Close()
	
	service.Run()
}

// getEnv gets an environment variable with a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
