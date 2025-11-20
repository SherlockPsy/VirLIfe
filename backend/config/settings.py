from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "VirLife Backend"
    environment: str = "production"
    database_url: str = "postgresql+asyncpg://user:password@localhost/virlife"
    venice_api_key: str = ""
    venice_base_url: str = "https://api.venice.ai/api/v1"
    
    model_config = SettingsConfigDict(env_file=".env")

    @property
    def async_database_url(self) -> str:
        """
        Ensures the database URL uses the correct async driver (asyncpg).
        Handles multiple URL formats:
        - postgres:// → postgresql+asyncpg://
        - postgresql:// → postgresql+asyncpg://
        """
        url = self.database_url
        
        # Handle postgres:// (old Heroku format)
        if url and url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        # Handle postgresql:// without asyncpg driver
        elif url and url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        return url

settings = Settings()
