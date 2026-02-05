from pydantic import BaseModel
import os

class Settings(BaseModel):
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
    kafka_topic: str = os.getenv("KAFKA_TOPIC", "news.raw.fetched")
    client_id: str = os.getenv("CLIENT_ID", "news-fetcher")
    kafka_acks: int = int(os.getenv("KAFKA_ACKS", "-1"))
    kafka_compression_type: str = os.getenv("KAFKA_COMPRESSION_TYPE", "gzip")
    kafka_max_in_flight: int = int(os.getenv("KAFKA_MAX_IN_FLIGHT", "5"))

    # Fetcher settings
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
    http_timeout: int = int(os.getenv("HTTP_TIMEOUT", "15"))
    rate_limit_delay: float = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))

    # Redis for deduplication
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))

    # Feeds configuration
    feeds_file: str = os.getenv("FEEDS_FILE", "src/feeds.yaml")

    # Database
    db_host: str = os.getenv("DB_HOST", "postgres")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "newsinsight")
    db_user: str = os.getenv("DB_USER", "app")
    db_password: str = os.getenv("DB_PASSWORD", "app")

settings = Settings()
