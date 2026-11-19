import { createHmac, timingSafeEqual } from 'node:crypto';

export function webhookSecret(token) {
  if (!token) throw new Error('Missing bot identity');
  return createHmac('sha256', token).update('scenelingo:telegram-webhook:v1').digest('hex');
}

export function authorizedWebhook(header, token) {
  if (!token || typeof header !== 'string' || !/^[a-f0-9]{64}$/.test(header)) return false;
  return timingSafeEqual(Buffer.from(header), Buffer.from(webhookSecret(token)));
}
