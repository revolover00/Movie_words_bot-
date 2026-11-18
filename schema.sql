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

-- Additive preferences for the upcoming multilingual scheduler. Existing
-- subscribers remain untouched; settings are created only on first use.
CREATE TABLE IF NOT EXISTS subscriber_preferences (
    chat_id BIGINT PRIMARY KEY REFERENCES subscribers(chat_id) ON DELETE CASCADE,
    learning_language TEXT NOT NULL DEFAULT 'en'
      CHECK (learning_language IN ('en', 'zh', 'hi', 'es', 'fr', 'ar', 'pt', 'ru', 'de', 'ja')),
    explanation_language TEXT NOT NULL DEFAULT 'ar'
      CHECK (explanation_language IN ('en', 'zh', 'hi', 'es', 'fr', 'ar', 'pt', 'ru', 'de', 'ja')),
    interval_minutes INTEGER NOT NULL DEFAULT 180 CHECK (interval_minutes BETWEEN 5 AND 1440),
    next_due_at TIMESTAMPTZ,
    input_state TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE subscriber_preferences ADD COLUMN IF NOT EXISTS input_state TEXT;
