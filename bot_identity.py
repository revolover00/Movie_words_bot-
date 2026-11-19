"""Use the Telegram bot ID as a stable, non-secret database namespace."""
import re


def database_schema(token: str) -> str:
    bot_id, separator, _ = token.partition(':')
    if not separator or not re.fullmatch(r'[0-9]+', bot_id):
        raise ValueError('A valid BOT_TOKEN is required to select the bot database')
    return f'bot_{bot_id}'
