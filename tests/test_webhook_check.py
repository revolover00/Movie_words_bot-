import os
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from scripts import check_webhook


class WebhookRecoveryTests(unittest.TestCase):
    def run_check(self, info, endpoint_status=200):
        self.calls = []

        def post(url, **kwargs):
            payload = kwargs.get('json', {})
            self.calls.append((url, payload))
            if url == check_webhook.EXPECTED:
                return SimpleNamespace(status_code=endpoint_status)
            method = url.rsplit('/', 1)[-1]
            result = info.pop(0) if method == 'getWebhookInfo' else True
            return SimpleNamespace(ok=True, json=lambda: {'ok': True, 'result': result})

        with patch.dict(os.environ, {'BOT_TOKEN': '9051063252:test', 'REPAIR_WEBHOOK': 'true'}), patch.object(check_webhook.requests, 'post', post):
            check_webhook.main()

    def test_repair_preserves_pending_and_only_sets_webhook(self):
        self.run_check([{'url': 'https://example.com/other', 'pending_update_count': 4}, {'url': check_webhook.EXPECTED}])
        writes = [p for url, p in self.calls if url.endswith('/setWebhook')]
        self.assertEqual(writes, [{'url': check_webhook.EXPECTED, 'allowed_updates': ['message', 'callback_query'], 'drop_pending_updates': False}])
        self.assertFalse(any('/send' in url for url, _ in self.calls))

    def test_correct_webhook_is_not_rewritten(self):
        self.run_check([{'url': check_webhook.EXPECTED}])
        self.assertFalse(any(url.endswith('/setWebhook') for url, _ in self.calls))

    def test_unhealthy_endpoint_cannot_replace_webhook(self):
        with self.assertRaisesRegex(RuntimeError, 'endpoint failed'):
            self.run_check([{'url': 'https://example.com'}], 500)
        self.assertFalse(any(url.endswith('/setWebhook') for url, _ in self.calls))
