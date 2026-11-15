"""Get a word's meaning in Egyptian Arabic via Groq (OpenAI-compatible)."""

from __future__ import annotations

import logging

from openai import OpenAI

from config import config

log = logging.getLogger(__name__)

PROMPT = """You are a friendly English teacher for Egyptian learners.
Word: "{word}"

Reply with exactly this format (no extra text):
📖 {word} = المعنى بالمصري
💬 مثال: جملة إنجليزية قصيرة + ترجمتها بالمصري

Keep the example short and from everyday / movie-style English.
"""


def get_meaning(word: str, retries: int = 3) -> str:
    """Return the formatted meaning block for `word` (with retries)."""
    import time

    config.validate("groq_api_key")
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=config.groq_api_key)
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            res = client.chat.completions.create(
                model=config.groq_model,
                messages=[{"role": "user", "content": PROMPT.format(word=word)}],
                temperature=0.3,
                max_tokens=200,
            )
            text = (res.choices[0].message.content or "").strip()
            log.info("Groq meaning for %r: %s", word, text[:80])
            return text or f"📖 {word}"
        except Exception as exc:  # noqa: BLE001 - retry any API error
            last_exc = exc
            log.warning("Groq attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"Groq failed after {retries} attempts: {last_exc}")
