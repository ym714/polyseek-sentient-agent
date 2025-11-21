"""Runtime configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


@dataclass(frozen=True)
class APISettings:
    polymarket_base: str = os.getenv("POLYMARKET_API_BASE", "https://gamma-api.polymarket.com")
    kalshi_base: str = os.getenv("KALSHI_API_BASE", "https://trading-api.kalshi.com")
    kalshi_api_key: Optional[str] = os.getenv("KALSHI_API_KEY")
    kalshi_api_secret: Optional[str] = os.getenv("KALSHI_API_SECRET")
    news_api_key: Optional[str] = os.getenv("NEWS_API_KEY")
    x_bearer_token: Optional[str] = os.getenv("X_BEARER_TOKEN")
    reddit_client_id: Optional[str] = os.getenv("REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = os.getenv("REDDIT_CLIENT_SECRET")


@dataclass(frozen=True)
class ScrapeSettings:
    timeout_seconds: float = float(os.getenv("SCRAPE_TIMEOUT", "8.0"))
    max_comments: int = int(os.getenv("SCRAPE_MAX_COMMENTS", "20"))
    max_comment_chars: int = int(os.getenv("SCRAPE_MAX_COMMENT_CHARS", "500"))


@dataclass(frozen=True)
class LLMSettings:
    model: str = os.getenv("LITELLM_MODEL_ID", "openrouter/google/gemini-2.0-flash-001")
    api_key: Optional[str] = (
        os.getenv("POLYSEEK_LLM_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "8192"))  # Increased from 2048 to 8192 for deep analysis


@dataclass(frozen=True)
class AppSettings:
    offline_mode: bool = os.getenv("POLYSEEK_OFFLINE", "0") == "1"


@dataclass(frozen=True)
class Settings:
    apis: APISettings = APISettings()
    scrape: ScrapeSettings = ScrapeSettings()
    llm: LLMSettings = LLMSettings()
    app: AppSettings = AppSettings()


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Return cached settings."""
    return Settings()
