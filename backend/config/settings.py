from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import os

class Settings(BaseSettings):
    app_name: str = "VirLife Backend"
    environment: str = "production"
    database_url: str = ""
    redis_url: str = ""  # Optional: Phase 9 caching
    qdrant_url: str = ""  # Optional: Phase 9 vector memory
    qdrant_api_key: str = ""  # Optional: Phase 9 vector memory
    venice_api_key: str = ""
    venice_base_url: str = "https://api.venice.ai/api/v1"
    
    model_config = SettingsConfigDict(env_file=".env")

    @field_validator('database_url', mode='before')
    @classmethod
    def validate_database_url(cls, v):
        # DATABASE_URL is always required - no SQLite fallback
        if not v:
            raise ValueError(
                "DATABASE_URL environment variable is required and must not be empty. "
                "Expected format: postgresql://user:password@host:port/database "
                "(Railway provides this automatically when Postgres service is linked)"
            )
        
        # Ensure we're using Postgres, not SQLite
        if v.startswith("sqlite"):
            raise ValueError(
                "SQLite is not supported. This application requires PostgreSQL. "
                "Configure DATABASE_URL to point to a Railway Postgres service."
            )
        
        return v

    @property
    def async_database_url(self) -> str:
        """
        Ensures the database URL uses the correct async driver (asyncpg).
        Handles Railway Postgres URL formats:
        - postgres:// → postgresql+asyncpg://
        - postgresql:// → postgresql+asyncpg://
        """
        url = self.database_url
        
        # Handle postgres:// (Railway/Heroku format)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        # Handle postgresql:// without asyncpg driver
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        return url

settings = Settings()
