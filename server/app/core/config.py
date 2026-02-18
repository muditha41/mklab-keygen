"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://swaps:swaps@localhost:5432/swaps"

    # Security
    secret_key: str = "change-me-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # License key generation (HMAC)
    license_hmac_secret: str = "change-me-hmac-secret-for-key-generation"

    # Validation API
    validation_timestamp_window_seconds: int = 300  # 5 minutes
    validation_rate_limit_per_key_per_hour: int = 10

    # Global rate limit (per IP)
    rate_limit_per_minute_per_ip: int = 100

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Grace period (SDK)
    grace_period_hours: int = 48


settings = Settings()
