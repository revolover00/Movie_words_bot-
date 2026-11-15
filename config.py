"""Central configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    bot_token: str = _get("BOT_TOKEN")
    database_url: str = _get("DATABASE_URL")
    groq_api_key: str = _get("GROQ_API_KEY")
    groq_model: str = _get("GROQ_MODEL", "llama-3.1-8b-instant")
    words_file: str = _get("WORDS_FILE", "words.txt")
    clip_before: int = _get_int("CLIP_BEFORE", 2)
    clip_after: int = _get_int("CLIP_AFTER", 3)
    send_delay: float = _get_float("SEND_DELAY", 0.2)

    def validate(self, *required: str) -> None:
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


config = Config()
