import { test } from 'node:test';
import assert from 'node:assert/strict';
import { authorizedWebhook, webhookSecret } from '../lib/webhook-auth.js';

test('webhook uses a domain-separated secret matching Python test vector', () => {
  const secret = webhookSecret('123456:test-token');
  assert.equal(secret, '955961b5fd65a32feff2104749ff616a5af4d27aa07adbe4836505c583beaa39');
  assert.ok(authorizedWebhook(secret, '123456:test-token'));
  for (const value of [undefined, '', [], secret+'a', 'a'.repeat(64), '123456:test-token']) {
    assert.equal(authorizedWebhook(value, '123456:test-token'), false);
  }
  assert.equal(authorizedWebhook(secret, 'different-token'), false);
  assert.equal(authorizedWebhook(secret, undefined), false);
});
