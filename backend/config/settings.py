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
        # If no DATABASE_URL is set and we're in production, require it
        if not v:
            if os.environ.get('RAILWAY_ENVIRONMENT_NAME') or os.environ.get('ENVIRONMENT') == 'production':
                raise ValueError(
                    "DATABASE_URL environment variable is required and must not be empty. "
                    "Expected format: postgresql://user:password@host:port/database"
                )
            # In development/testing, provide SQLite fallback (file-based for persistence across sessions)
            return "sqlite+aiosqlite:///./virlife.db"
        
        # Validate that we're not pointing to localhost in production
        if (os.environ.get('RAILWAY_ENVIRONMENT_NAME') or os.environ.get('ENVIRONMENT') == 'production'):
            if "localhost" in v or "127.0.0.1" in v:
                raise ValueError(
                    "DATABASE_URL points to localhost. On Railway, use the remote database URL. "
                    "Check your environment variables."
                )
        
        return v

    @property
    def async_database_url(self) -> str:
        """
        Ensures the database URL uses the correct async driver (asyncpg).
        Handles multiple URL formats:
        - postgres:// → postgresql+asyncpg://
        - postgresql:// → postgresql+asyncpg://
        """
        url = self.database_url
        
        # SQLite doesn't need conversion
        if url.startswith("sqlite"):
            return url
        
        # Handle postgres:// (old Heroku format)
        if url and url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        # Handle postgresql:// without asyncpg driver
        elif url and url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        return url

settings = Settings()
