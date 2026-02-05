from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List
import os

class Settings(BaseSettings):
    # Kafka Configuration
    kafka_bootstrap_servers: str = Field(default="redpanda:9092")
    kafka_topic_input: str = Field(default="news.cleaned")
    kafka_topic_output: str = Field(default="news.enriched")
    kafka_consumer_group: str = Field(default="llm-intelligence-group")
    
    # Gemini LLM Configuration - stored as comma-separated string
    gemini_api_keys_str: str = Field(default="", alias="GEMINI_API_KEYS")
    gemini_models: List[str] = Field(default=[
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ])
    
    # Cerebras LLM Configuration - stored as comma-separated string
    cerebras_api_keys_str: str = Field(default="", alias="CEREBRAS_API_KEYS")
    
    # Multiple models to try
    cerebras_models: List[str] = Field(default=[
        "llama3.1-8b",
        "llama-3.3-70b",
        "gpt-oss-120b",
        "qwen-3-32b",
        "qwen-3-235b-a22b-instruct-2507",
        "zai-glm-4.6"
    ])
    
    cerebras_max_tokens: int = Field(default=4096)
    cerebras_temperature: float = Field(default=0.7)

    # Database
    db_host: str = Field(default="postgres")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="newsinsight")
    db_user: str = Field(default="app")
    db_password: str = Field(default="app")
    
    @property
    def gemini_api_keys(self) -> List[str]:
        """Parse comma-separated Gemini API keys."""
        if self.gemini_api_keys_str:
            return [k.strip() for k in self.gemini_api_keys_str.split(",") if k.strip()]
        return []
    
    @property
    def cerebras_api_keys(self) -> List[str]:
        """Parse comma-separated Cerebras API keys."""
        if self.cerebras_api_keys_str:
            return [k.strip() for k in self.cerebras_api_keys_str.split(",") if k.strip()]
        return []
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True

settings = Settings()
