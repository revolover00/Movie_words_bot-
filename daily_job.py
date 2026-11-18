"""Send one matching movie expression to each subscribed CEFR-level group."""
from __future__ import annotations

import asyncio
import logging

from telegram import Bot

import db
import phrases
import yarn_clips
from config import config
from groq_meaning import get_meaning

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def build_message(level: str):
    """Select an unseen expression with a real matching movie clip."""
    seen, recent_topics = db.phrase_history(level)
    for expression in phrases.candidates(level, seen, recent_topics):
        try:
            clip = yarn_clips.find_clip(expression.text)
        except RuntimeError as exc:
            log.info('No matching clip for %r: %s', expression.text, exc)
            continue
        meaning = get_meaning(expression.text, level=level, topic=expression.topic)
        caption = f"🎬 تعبير {level}\n\n{meaning}\n\n🎞️ من: {clip.title}\n🔗 {clip.url}"
        if len(caption) > 1024:
            raise ValueError('Telegram video caption exceeds 1024 characters')
        return expression, clip, caption
    raise RuntimeError(f'No matching movie clip for level {level}')


async def broadcast(bot: Bot, chat_ids: list[int], clip_path: str, caption: str) -> tuple[int, int]:
    sent = failed = 0
    for chat_id in chat_ids:
        try:
            with open(clip_path, 'rb') as video:
                await bot.send_video(chat_id=chat_id, video=video, caption=caption)
            sent += 1
        except Exception as exc:  # one blocked chat must not stop the group
            log.warning('Send to %s failed: %s', chat_id, exc)
            failed += 1
        await asyncio.sleep(config.send_delay)
    return sent, failed


async def run_groups(groups: dict[str, list[int]]) -> None:
    bot = Bot(token=config.bot_token)
    failures = []
    for level in phrases.LEVELS:
        chat_ids = groups.get(level, [])
        if not chat_ids:
            continue
        try:
            expression, clip, caption = build_message(level)
            sent, failed = await broadcast(bot, chat_ids, str(clip.path), caption)
            log.info('Level %s: %d sent, %d failed', level, sent, failed)
            if sent:
                db.mark_phrase_sent(level, expression.text, expression.topic, clip.clip_id, clip.title)
            else:
                raise RuntimeError('Failed to send to any subscriber')
        except Exception:
            log.exception('Failed to process level %s', level)
            failures.append(level)
    if failures:
        raise RuntimeError('Failed levels: ' + ', '.join(failures))


def main() -> None:
    config.validate('database_url', 'bot_token', 'groq_api_key')
    db.init_db()
    groups = db.active_subscribers_by_level()
    if not groups:
        log.info('No active subscribers; no messages sent')
        return
    asyncio.run(run_groups(groups))


if __name__ == '__main__':
    main()
