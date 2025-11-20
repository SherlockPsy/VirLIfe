from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "VirLife Backend"
    environment: str = "production"
    database_url: str = "postgresql+asyncpg://user:password@localhost/virlife"
    
    model_config = SettingsConfigDict(env_file=".env")

    @property
    def async_database_url(self) -> str:
        """
        Ensures the database URL uses the correct async driver.
        Railway (and Heroku) often provide 'postgres://' which needs to be 'postgresql+asyncpg://'.
        """
        if self.database_url and self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self.database_url

settings = Settings()
