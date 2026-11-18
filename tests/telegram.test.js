import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import pg from 'pg';
import handler from '../api/telegram.js';

const queries = [];
const calls = [];
let inputState = null;
pg.Client.prototype.connect = async () => {};
pg.Client.prototype.end = async () => {};
pg.Client.prototype.query = async (sql, values) => {
  queries.push({ sql, values });
  if (sql.startsWith('SELECT input_state')) return { rowCount: 1, rows: [{ input_state: inputState }] };
  if (sql.startsWith('UPDATE subscribers SET level')) return { rowCount: 1, rows: [{ level: values[0] }] };
  if (sql.startsWith('SELECT level FROM')) return { rowCount: 1, rows: [{ level: 'A2' }] };
  return { rowCount: 1, rows: [] };
};
const oldFetch = globalThis.fetch;
globalThis.fetch = async (url, options) => {
  calls.push({ url, body: JSON.parse(options.body) });
  return { ok: true, json: async () => ({ ok: true }) };
};
after(() => { globalThis.fetch = oldFetch; });
function res() { return { status(code) { assert.equal(code, 200); return this; }, send() {} }; }

test('start shows level buttons and keeps existing level on conflict', async () => {
  queries.length = 0; calls.length = 0;
  await handler({ method: 'POST', body: { message: { chat: { id: 1, type: 'private' }, from: { id: 1 }, text: '/start' } } }, res());
  const insert = queries.find(q => q.sql.includes('INSERT INTO subscribers'));
  assert.ok(insert);
  assert.ok(!insert.sql.includes('level = EXCLUDED'));
  assert.equal(calls.at(-1).body.reply_markup.inline_keyboard[0].length, 5);
});

test('user can change level from a private callback', async () => {
  queries.length = 0; calls.length = 0;
  await handler({ method: 'POST', body: { callback_query: { id: 'cb', from: { id: 1 }, message: { chat: { id: 1, type: 'private' } }, data: 'level:C1' } } }, res());
  assert.deepEqual(queries.find(q => q.sql.startsWith('UPDATE subscribers SET level')).values, ['C1', 1]);
  assert.match(calls.at(-1).body.text, /C1/);
});

test('invalid callback is rejected without database update', async () => {
  queries.length = 0; calls.length = 0;
  await handler({ method: 'POST', body: { callback_query: { id: 'cb', from: { id: 1 }, message: { chat: { id: 1, type: 'private' } }, data: 'level:ZZ' } } }, res());
  assert.equal(queries.length, 0);
  assert.ok(calls.at(-1).url.endsWith('/answerCallbackQuery'));
});

test('language selection records the requested language', async () => {
  queries.length = 0; calls.length = 0;
  await handler({ method: 'POST', body: { callback_query: { id: 'cb', from: { id: 1 }, message: { chat: { id: 1, type: 'private' } }, data: 'learn:es' } } }, res());
  const query = queries.find(q => q.sql.includes('INSERT INTO subscriber_preferences') && q.sql.includes('learning_language'));
  assert.deepEqual(query.values, ['es', 1]);
  assert.match(query.sql, /subscribed_at \+ interval '3 hours'/);
  assert.match(calls.at(-1).body.text, /es/);
});

test('interval accepts Arabic numerals and rejects values outside bounds', async () => {
  inputState = 'interval'; queries.length = 0; calls.length = 0;
  const update = text => ({ method: 'POST', body: { message: { chat: { id: 1, type: 'private' }, from: { id: 1 }, text } } });
  await handler(update('٤'), res());
  assert.match(calls.at(-1).body.text, /٥/);
  assert.ok(!queries.some(q => q.sql.startsWith('UPDATE subscriber_preferences SET interval_minutes')));
  await handler(update('٦'), res());
  const saved = queries.find(q => q.sql.startsWith('UPDATE subscriber_preferences SET interval_minutes'));
  assert.deepEqual(saved.values, [6, 1]);
  inputState = null;
});

test('welcome explains language and interval controls', async () => {
  calls.length = 0;
  await handler({ method: 'POST', body: { message: { chat: { id: 1, type: 'private' }, from: { id: 1 }, text: '/start' } } }, res());
  assert.match(calls.at(-1).body.text, /\/learn/);
  assert.match(calls.at(-1).body.text, /\/explain/);
  assert.match(calls.at(-1).body.text, /\/interval/);
});


test('opening interval input preserves a new preferences row due time', async () => {
  queries.length = 0; calls.length = 0;
  await handler({ method: 'POST', body: { message: { chat: { id: 1, type: 'private' }, from: { id: 1 }, text: '/interval' } } }, res());
  const query = queries.find(q => q.sql.includes("'interval'") && q.sql.includes('INSERT INTO subscriber_preferences'));
  assert.match(query.sql, /subscribed_at \+ interval '3 hours'/);
});

test('webhook returns failure for Telegram errors so updates can retry', async () => {
  const previous = globalThis.fetch;
  const previousError = console.error;
  let status;
  globalThis.fetch = async () => { throw new Error('temporary'); };
  console.error = () => {};
  try {
    await handler({ method: 'POST', body: { message: { chat: { id: 1, type: 'private' }, from: { id: 1 }, text: '/help' } } },
      { status(code) { status = code; return this; }, send() {} });
    assert.equal(status, 500);
  } finally {
    console.error = previousError;
    globalThis.fetch = previous;
  }
});
