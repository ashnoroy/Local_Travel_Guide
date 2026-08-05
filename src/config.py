"""
config.py
---------
Centralized configuration loader for the Local Travel Guide Chatbot.
Reads environment variables (from `.env`) and exposes them as constants
so the rest of the app never touches `os.environ` directly.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Fetch a required env var, raising a clear error if it's missing."""
    value = os.getenv(key)
    if not value or "your_" in value:
        raise EnvironmentError(
            f"Missing required environment variable: {key}. "
            f"Copy .env.example to .env and fill in your keys."
        )
    return value


class Settings:
    """Typed access to project settings."""

    # --- API Keys ---
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_PLACES_API_KEY: str = os.getenv("GOOGLE_PLACES_API_KEY", "")

    # --- LLM / Agent tuning ---
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    AGENT_VERBOSE: bool = os.getenv("AGENT_VERBOSE", "True").lower() == "true"

    # --- Defaults ---
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "USD")
    DEFAULT_SEARCH_RADIUS_METERS: int = int(
        os.getenv("DEFAULT_SEARCH_RADIUS_METERS", "3000")
    )

    @classmethod
    def validate(cls) -> None:
        """Call at startup to fail fast with a helpful message."""
        _require("OPENAI_API_KEY")
        _require("GOOGLE_PLACES_API_KEY")


settings = Settings()
