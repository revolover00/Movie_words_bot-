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

-- Keep existing subscribers and give them a sensible default level.
ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS level TEXT NOT NULL DEFAULT 'A2';

CREATE TABLE IF NOT EXISTS sent_phrases (
    id BIGSERIAL PRIMARY KEY,
    level TEXT NOT NULL,
    phrase TEXT NOT NULL,
    topic TEXT NOT NULL,
    clip_id TEXT,
    video_title TEXT,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS sent_phrases_level_sent_at_idx ON sent_phrases (level, sent_at DESC);
