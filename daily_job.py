"""Daily job: pick a word, get its meaning, fetch a movie clip, broadcast.

Run with:  python daily_job.py
Triggered daily by GitHub Actions (see .github/workflows/daily.yml).
"""

from __future__ import annotations

import asyncio
import logging
import time

from telegram import Bot

import db
import words as words_mod
import youtube_free
from clipper import get_clip, get_clip_for_word
from config import config
from groq_meaning import get_meaning

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


def build_today_message() -> tuple[str, str]:
    """Build (clip_path, caption) for a fresh word. Marks it as sent."""
    word = words_mod.pick_word()
    meaning = get_meaning(word)

    videos = youtube_free.search(f"{word} movie scene", max_results=5)
    if not videos:
        raise RuntimeError(f"No YouTube results for {word!r}")

    # Try videos in order until the word is actually spoken in one.
    video = videos[0]
    clip_path = None
    for candidate in videos[:3]:
        clip_path = get_clip_for_word(
            candidate.video_id, word, config.clip_before, config.clip_after
        )
        if clip_path is not None:
            video = candidate
            break
    if clip_path is None:
        # No video contained the word — fall back to the first result.
        log.warning("Word %r not found in any subtitles, using fallback clip", word)
        clip_path = get_clip(video.video_id, word, config.clip_before, config.clip_after)

    caption = (
        f"🎬 كلمة النهاردة\n\n"
        f"{meaning}\n\n"
        f"🎞️ من: {video.title}\n"
        f"🔗 {video.url}"
    )
    db.mark_sent(word, video.video_id, video.title)
    return str(clip_path), caption


async def broadcast(clip_path: str, caption: str) -> tuple[int, int]:
    """Send the clip to all active subscribers. Returns (sent, failed)."""
    config.validate("bot_token")
    bot = Bot(token=config.bot_token)
    subscribers = db.list_subscribers()
    sent = failed = 0
    for sub in subscribers:
        chat_id = sub["chat_id"]
        try:
            with open(clip_path, "rb") as f:
                await bot.send_video(chat_id=chat_id, video=f, caption=caption)
            sent += 1
        except Exception as exc:  # noqa: BLE001 - one bad chat must not stop the rest
            log.warning("Send to %s failed: %s", chat_id, exc)
            failed += 1
        time.sleep(config.send_delay)
    return sent, failed


def main() -> None:
    config.validate("database_url", "bot_token", "groq_api_key")
    db.init_db()
    clip_path, caption = build_today_message()
    sent, failed = asyncio.run(broadcast(clip_path, caption))
    log.info("Broadcast done: %d sent, %d failed", sent, failed)


if __name__ == "__main__":
    main()
