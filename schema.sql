-- Movie Word Bot schema (Neon Postgres)
-- Run once in the Neon SQL editor or via: python -m db init

CREATE TABLE IF NOT EXISTS subscribers (
    chat_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS sent_words (
    word TEXT PRIMARY KEY,
    video_id TEXT,
    video_title TEXT,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
