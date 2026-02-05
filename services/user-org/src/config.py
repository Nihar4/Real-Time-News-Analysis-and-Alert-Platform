from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Database
    db_host: str = Field(default="postgres", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="newsinsight", env="DB_NAME")
    db_user: str = Field(default="app", env="DB_USER")
    db_password: str = Field(default="app", env="DB_PASSWORD")
    
    # Security
    secret_key: str = Field(default="supersecretkey", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Kafka
    kafka_bootstrap_servers: str = Field(default="redpanda:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"

settings = Settings()
