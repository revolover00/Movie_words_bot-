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


def get_meaning(word: str) -> str:
    """Return the formatted meaning block for `word`."""
    config.validate("groq_api_key")
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=config.groq_api_key)
    res = client.chat.completions.create(
        model=config.groq_model,
        messages=[{"role": "user", "content": PROMPT.format(word=word)}],
        temperature=0.3,
        max_tokens=200,
    )
    text = (res.choices[0].message.content or "").strip()
    log.info("Groq meaning for %r: %s", word, text[:80])
    return text or f"📖 {word}"
