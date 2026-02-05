import os
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Kafka
    kafka_bootstrap_servers: str = Field(default="redpanda:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic_input: str = Field(default="news.deduped", env="KAFKA_TOPIC_INPUT")
    kafka_topic_output: str = Field(default="events.created", env="KAFKA_TOPIC_OUTPUT")
    kafka_consumer_group: str = Field(default="event-mapper-group", env="KAFKA_CONSUMER_GROUP")
    
    # Database
    db_host: str = Field(default="postgres", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="newsinsight", env="DB_NAME")
    db_user: str = Field(default="app", env="DB_USER")
    db_password: str = Field(default="app", env="DB_PASSWORD")
    
    class Config:
        env_file = ".env"

settings = Settings()
