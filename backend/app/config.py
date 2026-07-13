from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QuoteIQ API"
    app_version: str = "0.8.0"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./quoteiq.db"

    jwt_secret_key: str = "change-this-secret-before-deployment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()