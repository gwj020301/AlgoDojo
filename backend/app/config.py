"""Application settings, loaded from environment variables / .env file.

Uses pydantic-settings so config is validated and typed. Distinguish
dev/prod via the ``ENV`` variable.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime
    env: Literal["dev", "prod", "test"] = "dev"
    debug: bool = True

    # Database (PostgreSQL via asyncpg)
    database_url: str = Field(
        default="postgresql+asyncpg://algodojo:algodojo@localhost:5432/algodojo",
        description="SQLAlchemy async database URL.",
    )

    # Redis (task queue + result cache)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL.",
    )

    # API
    api_title: str = "AlgoDojo API"
    api_version: str = "0.1.0"

    # Frontend base URL (OAuth success/error redirects target this).
    frontend_url: str = "http://localhost:5173"

    # GitHub OAuth (https://github.com/settings/developers)
    github_client_id: str = ""
    github_client_secret: str = ""
    # Only read-only user scope — never request repo write access (requirement 1.7).
    github_scope: str = "read:user"
    # Backend base URL used to build the OAuth callback redirect_uri.
    backend_url: str = "http://localhost:8000"

    # JWT
    jwt_secret: str = "dev-insecure-secret-change-me-in-production-0123456789"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Judge queue + sandbox
    judge_queue_key: str = "algodojo:judge:queue"
    judge_image: str = "algodojo-judge:latest"
    judge_concurrency: int = 2  # max simultaneous judgings per worker process
    judge_time_limit_s: float = 2.0
    judge_memory_limit_mb: int = 256
    judge_max_attempts: int = 2  # retry once on system_error

    @property
    def github_redirect_uri(self) -> str:
        return f"{self.backend_url}/auth/github/callback"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
