from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
    kafka_topic: str = os.getenv("KAFKA_TOPIC", "raw-news-articles")
    client_id: str = os.getenv("CLIENT_ID", "news-fetcher")
    kafka_acks: str = os.getenv("KAFKA_ACKS", "1")
    kafka_compression_type: str = os.getenv("KAFKA_COMPRESSION_TYPE", "gzip")
    kafka_max_in_flight: int = int(os.getenv("KAFKA_MAX_IN_FLIGHT", "5"))

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_hours: int = Field(default=24, alias="ACCESS_TOKEN_EXPIRE_HOURS")

    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8080, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
