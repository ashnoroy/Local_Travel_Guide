"""
config.py
---------
Centralized configuration loader for the Local Travel Guide Chatbot.
Reads environment variables (from `.env`) and exposes them as constants
so the rest of the app never touches `os.environ` directly.

Uses fully FREE platforms:
- Groq (console.groq.com) for the LLM — free API key, no credit card.
- OpenStreetMap (Nominatim + Overpass) for places search — no API key
  needed at all, just a descriptive User-Agent per their usage policy.
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
    # Free Groq key: https://console.groq.com/keys (no credit card required)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # --- LLM / Agent tuning ---
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    AGENT_VERBOSE: bool = os.getenv("AGENT_VERBOSE", "True").lower() == "true"

    # --- OpenStreetMap (free, keyless) ---
    # Nominatim's usage policy requires a real, identifying User-Agent —
    # this isn't a secret, just good API citizenship.
    OSM_USER_AGENT: str = os.getenv(
        "OSM_USER_AGENT", "wanderly-travel-chatbot/1.0 (contact: your_email@example.com)"
    )
    NOMINATIM_URL: str = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
    OVERPASS_URL: str = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

    # --- Defaults ---
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "USD")
    DEFAULT_SEARCH_RADIUS_METERS: int = int(
        os.getenv("DEFAULT_SEARCH_RADIUS_METERS", "3000")
    )

    @classmethod
    def validate(cls) -> None:
        """Call at startup to fail fast with a helpful message."""
        _require("GROQ_API_KEY")


settings = Settings()
