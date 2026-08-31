from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "dev-only-change-me-to-a-long-random-secret-key"
_ALLOWED_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Fintech Operations Dashboard"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops"
    )
    database_echo: bool = False

    # JWT
    jwt_secret_key: str = Field(default=_DEFAULT_JWT_SECRET, min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Security
    bcrypt_rounds: int = 12

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_async_driver(cls, value: str) -> str:
        url = str(value)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @field_validator("jwt_algorithm")
    @classmethod
    def restrict_jwt_algorithm(cls, value: str) -> str:
        if value not in _ALLOWED_JWT_ALGORITHMS:
            raise ValueError(
                f"jwt_algorithm must be one of {sorted(_ALLOWED_JWT_ALGORITHMS)}, got {value!r}"
            )
        return value

    @model_validator(mode="after")
    def guard_production_config(self) -> "Settings":
        if self.app_env == "production":
            if self.jwt_secret_key == _DEFAULT_JWT_SECRET:
                raise ValueError(
                    "JWT_SECRET_KEY is still the default dev value — set a real "
                    "secret before running with APP_ENV=production"
                )
            if self.debug:
                raise ValueError("DEBUG must be false when APP_ENV=production")
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
