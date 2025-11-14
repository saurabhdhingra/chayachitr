import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Ensure a secret key is set for JWT signing
SECRET_KEY = os.getenv("SECRET_KEY", "DEFAULT_SECRET_KEY_NEVER_USE_IN_PROD_12345")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra='ignore'
    )

    # General App Settings
    PROJECT_NAME: str = "Image Processor Service"
    API_V1_STR: str = "/api/v1"
    
    # DB Settings
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # JWT Settings
    SECRET_KEY: str = SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day expiration
    
    # Storage Settings (Local Mock for GCS)
    STORAGE_PATH: str = "images_store"
    
    # GCS SETTINGS
    GCS_BUCKET_NAME: str = Field("image-processor-bucket", env="GCS_BUCKET_NAME")
    GCS_SIGNED_URL_EXPIRATION_SECONDS: int = Field(300, env="GCS_SIGNED_URL_EXPIRATION_SECONDS") # 5 minutes
    
    # Redis Settings
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    # NEW: TTL for caching GCS Signed URLs (Set to 10 seconds less than GCS expiration)
    IMAGE_URL_CACHE_SECONDS: int = Field(GCS_SIGNED_URL_EXPIRATION_SECONDS - 10, env="IMAGE_URL_CACHE_SECONDS")

    # Kafka Settings
    # NOTE: Set KAFKA_BOOTSTRAP_SERVERS to a running Kafka instance for async processing
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TRANSFORMATION_TOPIC: str = "image_transformations"
    
    # Rate Limit Settings
    RATE_LIMIT: str = "10/minute"

    
settings = Settings()