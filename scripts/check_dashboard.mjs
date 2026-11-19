// Production smoke test. Password is supplied only through a temporary Actions secret.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const password = process.env.DASHBOARD_SMOKE_PASSWORD;
if (!password) throw new Error('Missing smoke credentials');
const base = 'https://scenelingoo.vercel.app';
const denied = await fetch(base + '/api/dashboard?data=1');
assert.equal(denied.status, 401);
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ httpCredentials: { username: 'admin', password } });
  const response = await context.request.get(base + '/api/dashboard?data=1');
  assert.equal(response.status(), 200);
  const data = await response.json();
  for (const key of ['total', 'active', 'setup', 'stopped', 'due']) assert.equal(typeof data[key], 'number');
  assert.equal(data.total, data.active + data.setup + data.stopped);
  assert.ok(data.due <= data.active);
  assert.ok(!JSON.stringify(data).includes('chat_id'));
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(base);
  await page.waitForFunction(() => document.querySelectorAll('#cards .card').length === 5);
  assert.equal(await page.locator('#error').isVisible(), false);
  await page.getByRole('button', { name: 'تحديث البيانات ↻' }).click();
  await page.waitForFunction(() => !document.querySelector('#refresh').disabled);
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  assert.deepEqual(errors, []);
  console.log('::notice title=Dashboard smoke::Private authentication, real database aggregates, desktop render, refresh and mobile layout passed.');
} finally { await browser.close(); }
