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


def active_subscribers_by_level() -> dict[str, list[int]]:
    """Return active subscriber chat IDs grouped by their selected CEFR level."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT level, chat_id FROM subscribers WHERE is_active = TRUE ORDER BY chat_id")
        groups: dict[str, list[int]] = {}
        for level, chat_id in cur.fetchall():
            groups.setdefault(level, []).append(chat_id)
        return groups


def phrase_history(level: str) -> tuple[set[str], list[str]]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT phrase, topic FROM sent_phrases WHERE level = %s ORDER BY sent_at DESC", (level,))
        rows = cur.fetchall()
        return {row[0].casefold() for row in rows}, [row[1] for row in rows[:3]]


def mark_phrase_sent(level: str, phrase: str, topic: str, clip_id: str, title: str) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO sent_phrases (level, phrase, topic, clip_id, video_title) VALUES (%s, %s, %s, %s, %s)",
            (level, phrase, topic, clip_id, title),
        )


def due_subscribers() -> list[dict]:
    """List active users due at the current database time, with their preferences.

    This is a scheduling building block, not a delivery claim. The caller must
    serialize scheduling runs and advance a user's due time only after delivery.
    """
    with connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT s.chat_id, s.level,
                       COALESCE(p.learning_language, 'en') AS learning_language,
                       COALESCE(p.explanation_language, 'ar') AS explanation_language,
                       COALESCE(p.interval_minutes, 180) AS interval_minutes,
                       p.updated_at AS settings_updated_at
                FROM subscribers s
                LEFT JOIN subscriber_preferences p ON p.chat_id = s.chat_id
                WHERE s.is_active = TRUE
                  AND COALESCE(p.next_due_at, s.subscribed_at + interval '3 hours') <= now()
                ORDER BY COALESCE(p.next_due_at, s.subscribed_at + interval '3 hours'), s.chat_id
            """)
            return [dict(row) for row in cur.fetchall()]


def advance_due_after_delivery(chat_id: int, settings_updated_at) -> bool:
    """Advance only if preferences haven't changed during delivery.

    New preference rows use the old three-hour default. Existing rows are
    guarded by updated_at, so a concurrent settings change is not overwritten.
    """
    with connect() as conn, conn.cursor() as cur:
        if settings_updated_at is None:
            cur.execute("""
                INSERT INTO subscriber_preferences (chat_id, next_due_at)
                SELECT chat_id, now() + interval '3 hours' FROM subscribers
                WHERE chat_id = %s AND is_active = TRUE
                ON CONFLICT (chat_id) DO NOTHING
                RETURNING chat_id
            """, (chat_id,))
        else:
            cur.execute("""
                UPDATE subscriber_preferences p
                SET next_due_at = now() + p.interval_minutes * interval '1 minute'
                FROM subscribers s
                WHERE p.chat_id = %s AND s.chat_id = p.chat_id AND s.is_active = TRUE
                  AND p.updated_at = %s
                RETURNING p.chat_id
            """, (chat_id, settings_updated_at))
        return cur.fetchone() is not None
