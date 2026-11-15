"""Word bank: pick a word that has not been sent yet.

Words are English (movies are mostly English); meanings are in
Egyptian Arabic via Groq. Add more words to `words.txt` anytime.
"""

from __future__ import annotations

import logging
import random
from pathlib import Path

import db
from config import config

log = logging.getLogger(__name__)


def load_words(path: str | None = None) -> list[str]:
    """Load words from file (one per line, `#` comments ignored)."""
    words_path = Path(path or config.words_file)
    if not words_path.exists():
        raise FileNotFoundError(f"Words file not found: {words_path}")
    words = [
        line.strip().lower()
        for line in words_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not words:
        raise ValueError(f"No words in {words_path}")
    return words


def pick_word() -> str:
    """Pick a random word that was not sent before."""
    words = load_words()
    fresh = [w for w in words if not db.was_sent(w)]
    pool = fresh or words  # all sent -> allow repeats
    word = random.choice(pool)
    log.info("Picked word: %s (%d fresh / %d total)", word, len(fresh), len(words))
    return word
