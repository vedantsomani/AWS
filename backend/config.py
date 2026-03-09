"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All environment configuration in one place."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = ""
    MODEL_NAME: str = "gpt-4"
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = ""

    # E2B Sandbox
    E2B_API_KEY: str = ""
    E2B_TEMPLATE: str = ""

    # Gemini API (passed to sandbox for image generation)
    GEMINI_API_KEY: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Rate limiting
    RATE_LIMIT_PER_HOUR: int = 10

    # Server
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
