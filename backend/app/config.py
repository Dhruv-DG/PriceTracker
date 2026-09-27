"""
Application configuration.
All settings are loaded from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Price Intelligence Dashboard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    DEMO_MODE: bool = False  # Set to True to run without API keys

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:5174,http://localhost:5175"

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{Path(__file__).parent.parent / 'data' / 'pricetracker.db'}"

    # Search Provider
    SEARCH_PROVIDER: str = "serper"  # "serper" or "demo"
    SERPER_API_KEY: Optional[str] = None

    # LLM Provider
    LLM_PROVIDER: str = "gemini"  # "gemini" or "demo"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash-lite"

    # Historical Price Providers
    KEEPA_API_KEY: Optional[str] = None

    # Cache
    CACHE_TTL_SEARCH: int = 3600  # 1 hour
    CACHE_TTL_PRICE: int = 300  # 5 minutes
    CACHE_TTL_HISTORY: int = 86400  # 24 hours
    CACHE_MAX_SIZE: int = 1000

    # Rate Limiting
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT: int = 15  # seconds
    SEARCH_RESULTS_LIMIT: int = 15

    # Tracking
    TRACKING_INTERVAL_MINUTES: int = 360  # 6 hours
    TRACKING_ENABLED: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_demo_mode(self) -> bool:
        """Auto-detect demo mode if API keys are missing."""
        if self.DEMO_MODE:
            return True
        if not self.SERPER_API_KEY and not self.GEMINI_API_KEY:
            return True
        return False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
