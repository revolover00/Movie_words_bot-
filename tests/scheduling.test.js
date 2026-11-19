import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PGlite } from '@electric-sql/pglite';

// Execute the actual production SQL in Postgres, not a JavaScript reimplementation.
test('half-hour schedules follow clock slots without drift or catch-up bursts', async () => {
  const db = new PGlite();
  try {
    await db.exec(readFileSync(new URL('../schema.sql', import.meta.url), 'utf8'));
    await db.exec(readFileSync(new URL('../scheduling.sql', import.meta.url), 'utf8'));
    for (const [base, expected] of [
      ['2026-11-19T10:04:12Z', '2026-11-19T10:30:00.000Z'],
      ['2026-11-19T10:29:59.999Z', '2026-11-19T10:30:00.000Z'],
      ['2026-11-19T10:30:00Z', '2026-11-19T11:00:00.000Z'],
      ['2026-11-19T10:00:00Z', '2026-11-19T10:30:00.000Z'],
      ['2026-11-19T23:58:01Z', '2026-11-20T00:00:00.000Z'],
      ['2026-12-31T23:49:00Z', '2027-01-01T00:00:00.000Z'],
      // A late delivery at 11:12 must not turn the next due time into 11:42.
      ['2026-11-19T11:12:00Z', '2026-11-19T11:30:00.000Z'],
      ['2026-11-19T13:59:00+02:00', '2026-11-19T12:00:00.000Z'],
    ]) {
      const result = await db.query('SELECT next_delivery_at(30, $1::timestamptz) AS due', [base]);
      assert.equal(result.rows[0].due.toISOString(), expected);
    }
    for (const minutes of [60, 120, 180, 360, 720, 1440]) {
      const base = '2026-11-19T10:04:12Z';
      const result = await db.query('SELECT next_delivery_at($1, $2::timestamptz) AS due', [minutes, base]);
      assert.equal(result.rows[0].due.getTime(), Date.parse(base) + minutes * 60000);
    }
    await db.exec("INSERT INTO subscribers(chat_id) VALUES (1),(2),(3); INSERT INTO subscriber_preferences(chat_id,interval_minutes,next_due_at) VALUES (1,30,now()+interval '23 minutes 0.123 seconds'),(2,30,now()-interval '2 hours'),(3,60,now()+interval '47 minutes');");
    const before = (await db.query('SELECT chat_id,next_due_at FROM subscriber_preferences ORDER BY chat_id')).rows;
    await db.exec(readFileSync(new URL('../scheduling.sql', import.meta.url), 'utf8'));
    const after = (await db.query('SELECT chat_id,next_due_at FROM subscriber_preferences ORDER BY chat_id')).rows;
    assert.equal(after[0].next_due_at.getTime() % 1800000, 0);
    assert.equal(after[1].next_due_at.getTime(), before[1].next_due_at.getTime());
    assert.equal(after[2].next_due_at.getTime(), before[2].next_due_at.getTime());
    await db.exec(readFileSync(new URL('../scheduling.sql', import.meta.url), 'utf8'));
    assert.deepEqual((await db.query('SELECT chat_id,next_due_at FROM subscriber_preferences ORDER BY chat_id')).rows, after);
  } finally { await db.close(); }
});
