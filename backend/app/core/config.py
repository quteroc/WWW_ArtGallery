"""
Configuration settings for the Classic Art Gallery application.
"""
import os
import secrets
from pydantic_settings import BaseSettings


from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""
    
    model_config = ConfigDict(case_sensitive=True)
    
    # Project metadata
    PROJECT_NAME: str = "Classic Art Gallery"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@db:5432/artgallery"
    )
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Static files - WikiArt dataset location
    STATIC_FILES_DIR: str = os.getenv("STATIC_FILES_DIR", "/app/ml/input/wikiart")
    
    # Image hosting via DigitalOcean Spaces CDN
    ARTWORKS_BASE_URL: str = os.getenv(
        "ARTWORKS_BASE_URL",
        "https://artappspace.nyc3.digitaloceanspaces.com"
    )


settings = Settings()
