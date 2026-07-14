# src/config.py 
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Sentiment Analysis API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # Model
    MODEL_NAME: str = "distilbert-base-uncased-finetuned-sst-2-english"
    MAX_BATCH_SIZE: int = 32
    CACHE_SIZE: int = 1000
    CACHE_TTL: int = 3600
    
    # Redis
    REDIS_URL: Optional[str] = None
    USE_REDIS_CACHE: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    ERROR_LOG_FILE: str = "logs/errors.log"
    
    # Security
    API_KEY: Optional[str] = None
    RATE_LIMIT: int = 100
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: Optional[str] = None
    USE_DATABASE: bool = False
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()