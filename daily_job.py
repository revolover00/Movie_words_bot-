"""Send one matching movie expression to each subscribed CEFR-level group."""
from __future__ import annotations

import asyncio
import logging

from telegram import Bot

import db
import phrases
import clip_cafe
import multilingual
from config import config
from groq_meaning import get_meaning

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def build_message(level: str):
    """Select an unseen expression with a real matching movie clip."""
    seen, recent_topics = db.phrase_history(level)
    for expression in phrases.candidates(level, seen, recent_topics):
        try:
            clip = clip_cafe.find_clip(expression.text)
        except RuntimeError as exc:
            log.info('No matching clip for %r: %s', expression.text, exc)
            continue
        meaning = get_meaning(expression.text, level=level, topic=expression.topic)
        caption = f"🎬 تعبير {level}\n\n{meaning}\n\n🎞️ من: {clip.title}\n🔗 {clip.url}"
        if len(caption) > 1024:
            raise ValueError('Telegram video caption exceeds 1024 characters')
        return expression, clip, caption
    raise RuntimeError(f'No matching movie clip for level {level}')


def build_localized_message(level: str, learning: str, explanation: str):
    """Find an expression and verify its audio before producing a caption."""
    seen, topics = db.phrase_history(level, learning)
    if learning == 'en':
        candidates = [(p.text, p.topic) for p in phrases.candidates(level, seen, topics)]
    else:
        candidates = multilingual.expressions(learning, level, seen, topics)
    for text, topic in candidates:
        try:
            clip = clip_cafe.find_clip(
                text, verify=lambda path, phrase: multilingual.verify_audio(path, phrase, learning))
        except RuntimeError:
            log.info('No verified audio found for expression %r', text)
            continue
        meaning = multilingual.meaning(text, learning, explanation, level)
        caption = f'🎬 {level} · {learning.upper()}\n\n{text}\n\n{meaning}\n\n🎞️ {clip.title}\n🔗 {clip.url}'
        if len(caption) > 1024:
            raise ValueError('Telegram video caption exceeds 1024 characters')
        return phrases.Phrase(text, topic), clip, caption
    raise RuntimeError(f'No verified clip for {level}/{learning}')


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
            print(f'::notice title=Level {level} delivery::{sent} sent, {failed} failed', flush=True)
            if sent:
                db.mark_phrase_sent(level, expression.text, expression.topic, clip.clip_id, clip.title)
            else:
                raise RuntimeError('Failed to send to any subscriber')
        except Exception:
            log.exception('Failed to process level %s', level)
            failures.append(level)
    if failures:
        raise RuntimeError('Failed levels: ' + ', '.join(failures))



async def run_due_subscribers(subscribers: list[dict]) -> None:
    """Deliver only to due subscribers; advance each schedule after successful sends.

    Clips must pass audio verification before delivery.
    """
    bot = Bot(token=config.bot_token)
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for sub in subscribers:
        key = (sub['level'], sub['learning_language'], sub['explanation_language'])
        groups.setdefault(key, []).append(sub)
    failures = []
    for (level, learning, explanation), group in groups.items():
        try:
            expression, clip, caption = build_localized_message(level, learning, explanation)
            sent_count = 0
            for sub in group:
                sent, failed = await broadcast(bot, [sub['chat_id']], str(clip.path), caption)
                if sent:
                    sent_count += 1
                    if not db.advance_due_after_delivery(sub['chat_id'], sub['settings_updated_at']):
                        log.info('Preferences changed during delivery; leaving new schedule unchanged')
                elif failed:
                    failures.append(f"chat {sub['chat_id']}")
            if sent_count:
                db.mark_phrase_sent(level, expression.text, expression.topic, clip.clip_id, clip.title, learning)
            print(f'::notice title=Level {level} delivery::{sent_count} sent', flush=True)
        except Exception:
            log.exception('Failed to process level %s', level)
            failures.append(level)
    if failures:
        raise RuntimeError(f'Failed to deliver {len(failures)} group(s) or subscriber(s)')

def main() -> None:
    config.validate('database_url', 'bot_token', 'groq_api_key')
    db.init_db()
    subscribers = db.due_subscribers()
    if not subscribers:
        log.info('No subscribers due; no messages sent')
        print('::notice title=Delivery::No subscribers due', flush=True)
        return
    asyncio.run(run_due_subscribers(subscribers))


if __name__ == '__main__':
    main()
