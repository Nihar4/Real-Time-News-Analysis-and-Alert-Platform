import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
    kafka_topic_raw_articles: str = os.getenv("KAFKA_TOPIC_RAW_ARTICLES", "news.raw.fetched")
    kafka_topic_processed_articles: str = os.getenv("KAFKA_TOPIC_PROCESSED_ARTICLES", "news.cleaned")
    kafka_consumer_group: str = os.getenv("KAFKA_CONSUMER_GROUP", "content-processing-group")
    
    # Service
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    user_agent: str = os.getenv("USER_AGENT", "Mozilla/5.0 (compatible; NewsBot/1.0)")
    max_workers: int = int(os.getenv("MAX_WORKERS", "10"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Translation
    translate_to_english: bool = os.getenv("TRANSLATE_TO_ENGLISH", "true").lower() == "true"
    auto_translate_non_english: bool = os.getenv("AUTO_TRANSLATE_NON_ENGLISH", "true").lower() == "true"

    # Database
    db_host: str = os.getenv("DB_HOST", "postgres")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "newsinsight")
    db_user: str = os.getenv("DB_USER", "app")
    db_password: str = os.getenv("DB_PASSWORD", "app")
    
    class Config:
        env_file = ".env"

settings = Settings()