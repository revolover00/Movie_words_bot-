"""Neon Postgres data layer.

Tables:
    subscribers(chat_id, username, first_name, subscribed_at, is_active)
    sent_words(word, video_id, video_title, sent_at)
"""

from __future__ import annotations

import logging
from typing import Optional

import psycopg2
import psycopg2.extras

from config import config

log = logging.getLogger(__name__)


def connect():
    """Open a Neon Postgres connection."""
    config.validate("database_url")
    return psycopg2.connect(config.database_url)


def init_db() -> None:
    """Create tables if they do not exist."""
    with open("schema.sql", encoding="utf-8") as f:
        ddl = f.read()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
    log.info("Database initialized")


def add_subscriber(chat_id: int, username: str | None, first_name: str | None) -> None:
    """Subscribe (or reactivate) a user."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO subscribers (chat_id, username, first_name, is_active)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT (chat_id) DO UPDATE
                SET username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    is_active = TRUE
                """,
                (chat_id, username, first_name),
            )
        conn.commit()


def remove_subscriber(chat_id: int) -> None:
    """Unsubscribe a user (soft delete)."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE subscribers SET is_active = FALSE WHERE chat_id = %s",
                (chat_id,),
            )
        conn.commit()


def list_subscribers() -> list[dict]:
    """Return all active subscribers."""
    with connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT chat_id FROM subscribers WHERE is_active = TRUE ORDER BY chat_id"
            )
            return [dict(row) for row in cur.fetchall()]


def was_sent(word: str) -> bool:
    """Check whether a word was already sent."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM sent_words WHERE word = %s", (word,))
            return cur.fetchone() is not None


def mark_sent(word: str, video_id: str | None, video_title: str | None) -> None:
    """Record a word as sent."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sent_words (word, video_id, video_title)
                VALUES (%s, %s, %s)
                ON CONFLICT (word) DO NOTHING
                """,
                (word, video_id, video_title),
            )
        conn.commit()


def last_sent_word() -> Optional[str]:
    """Return the most recently sent word, if any."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT word FROM sent_words ORDER BY sent_at DESC LIMIT 1"
            )
            row = cur.fetchone()
            return row[0] if row else None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
