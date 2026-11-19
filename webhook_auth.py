"""Domain-separated webhook secret shared with the JavaScript receiver."""
import hashlib
import hmac


def webhook_secret(bot_token):
    if not bot_token:
        raise ValueError('Missing bot identity')
    return hmac.new(bot_token.encode(), b'scenelingo:telegram-webhook:v1', hashlib.sha256).hexdigest()
