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
import yarn_clips
from config import config
from groq_meaning import get_meaning

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


def build_today_message() -> tuple[str, str, str, yarn_clips.YarnClip]:
    """Build the clip and caption for a fresh word without marking it sent."""
    word = words_mod.pick_word()
    meaning = get_meaning(word)

    clip = yarn_clips.find_clip(word)

    caption = (
        f"🎬 كلمة النهاردة\n\n"
        f"{meaning}\n\n"
        f"🎞️ من: {clip.title}\n"
        f"🔗 {clip.url}"
    )
    return str(clip.path), caption, word, clip


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
    clip_path, caption, word, clip = build_today_message()
    sent, failed = asyncio.run(broadcast(clip_path, caption))
    log.info("Broadcast done: %d sent, %d failed", sent, failed)
    if sent:
        db.mark_sent(word, clip.clip_id, clip.title)
    elif failed:
        raise RuntimeError("Failed to send the clip to every subscriber")
    else:
        log.warning("No active subscribers; word not marked as sent")


if __name__ == "__main__":
    main()
