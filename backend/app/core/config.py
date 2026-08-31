from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "dev-only-change-me-to-a-long-random-secret-key"
_DEFAULT_ENCRYPTION_KEY = "2Bah-XiMWI6lN6xpqdk6yhd2WuPUioT_z0H-9txKcgU="
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

    # Refresh-token cookie (httpOnly — never readable from JS; see auth.py)
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_path: str = "/api/v1/auth"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Security
    bcrypt_rounds: int = 12
    # Fernet key protecting mfa_secret at rest — separate from jwt_secret_key
    # so rotating one doesn't force rotating the other.
    encryption_key: str = Field(default=_DEFAULT_ENCRYPTION_KEY)

    # Login lockout: after `login_lockout_threshold` consecutive failures,
    # lock the account for base_seconds * 2^(failures - threshold), capped
    # at max_seconds.
    login_lockout_threshold: int = 5
    login_lockout_base_seconds: int = 30
    login_lockout_max_seconds: int = 900
    # slowapi rate-limit spec (see https://limits.readthedocs.io syntax)
    login_rate_limit: str = "10/minute"

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
            if self.encryption_key == _DEFAULT_ENCRYPTION_KEY:
                raise ValueError(
                    "ENCRYPTION_KEY is still the default dev value — set a real "
                    "Fernet key before running with APP_ENV=production"
                )
            if self.debug:
                raise ValueError("DEBUG must be false when APP_ENV=production")
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
