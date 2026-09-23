from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Support Ticketing API"
    database_url: str
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()