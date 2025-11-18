import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

SECRET_KEY = os.getenv("SECRET_KEY", "DEFAULT_SECRET_KEY_NEVER_USE_IN_PROD_12345")

GCS_EXPIRATION_DEFAULT = 300 

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra='ignore'
    )

    PROJECT_NAME: str = "Image Processor Service"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    SECRET_KEY: str = SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day expiration
    
    STORAGE_PATH: str = "images_store"
    
    GCS_BUCKET_NAME: str = Field("image-processor-bucket", env="GCS_BUCKET_NAME")
    
    GCS_SIGNED_URL_EXPIRATION_SECONDS: int = Field(GCS_EXPIRATION_DEFAULT, env="GCS_SIGNED_URL_EXPIRATION_SECONDS") 
    
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")

    IMAGE_URL_CACHE_SECONDS: int = Field(GCS_EXPIRATION_DEFAULT - 10, env="IMAGE_URL_CACHE_SECONDS")

    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TRANSFORMATION_TOPIC: str = "image_transformations"
    
    RATE_LIMIT: str = "10/minute"

    
settings = Settings()