"""Inspect/restore the existing Vercel webhook without exposing credentials."""
import os
import requests

EXPECTED = 'https://scenelingoo.vercel.app/api/telegram'


def main():
    token = os.environ['BOT_TOKEN']
    if token.split(':')[0] != '9051063252':
        raise RuntimeError('Unexpected bot identity')

    def api(method, **payload):
        try:
            r = requests.post(f'https://api.telegram.org/bot{token}/{method}', json=payload, timeout=30)
            data = r.json()
            if not r.ok or not data.get('ok'):
                raise ValueError()
            return data['result']
        except Exception:
            raise RuntimeError(f'Telegram {method} failed') from None

    info = api('getWebhookInfo')
    matches = info.get('url') == EXPECTED
    print(f'::notice title=Webhook inspection::expected_url={matches}, pending={info.get("pending_update_count", 0)}, recent_error={bool(info.get("last_error_message"))}', flush=True)
    if info.get('last_error_message'):
        message = info['last_error_message']
        # Only emit known diagnostic classifications, never raw remote text.
        classification = next((s for s in ['500', '404', '401', '403', 'timeout', 'SSL'] if s.lower() in message.lower()), 'other')
        print(f'::notice title=Webhook error class::{classification}', flush=True)
    try:
        response = requests.post(EXPECTED, json={}, timeout=45)
        print(f'::notice title=Webhook endpoint::empty_update_http={response.status_code}', flush=True)
        if response.status_code != 200:
            raise ValueError()
    except Exception:
        raise RuntimeError('Production webhook endpoint failed safe empty-update probe') from None
    if not matches and os.environ.get('REPAIR_WEBHOOK') == 'true':
        api('setWebhook', url=EXPECTED, allowed_updates=['message', 'callback_query'], drop_pending_updates=False)
        if api('getWebhookInfo').get('url') != EXPECTED:
            raise RuntimeError('Webhook repair verification failed')
        print('::notice title=Webhook repair::Vercel webhook restored; pending updates preserved', flush=True)
    elif not matches:
        raise RuntimeError('Webhook points away from production Vercel endpoint')


if __name__ == '__main__':
    main()
