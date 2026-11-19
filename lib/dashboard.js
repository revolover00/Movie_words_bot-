import { createHash, timingSafeEqual } from 'node:crypto';
import pg from 'pg';

export function authorized(header, expectedHash) {
  if (!/^[a-f0-9]{64}$/.test(expectedHash || '') || !header?.startsWith('Basic ')) return false;
  const credentials = Buffer.from(header.slice(6), 'base64').toString();
  const separator = credentials.indexOf(':');
  if (separator < 0 || credentials.slice(0, separator) !== 'admin') return false;
  const hash = createHash('sha256').update(credentials.slice(separator + 1)).digest();
  return timingSafeEqual(hash, Buffer.from(expectedHash, 'hex'));
}

export async function snapshot() {
  const botId = (process.env.BOT_TOKEN || '').split(':')[0];
  if (!/^\d+$/.test(botId)) throw new Error('Missing bot identity');
  const client = new pg.Client({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } });
  await client.connect();
  try {
    await client.query('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY');
    await client.query(`SET LOCAL search_path TO "bot_${botId}"`);
    // Counts and distributions use exactly the same eligibility rule as scheduling.
    const result = await client.query(`WITH audience AS (
      SELECT s.is_active, s.level, s.subscribed_at,
        COALESCE(p.learning_language, 'en') AS learning,
        COALESCE(p.explanation_language, 'ar') AS explanation,
        COALESCE(p.interval_minutes, 180) AS minutes,
        LEFT(COALESCE(p.input_state, ''), 6) = 'setup_' AS in_setup,
        COALESCE(p.next_due_at, s.subscribed_at + interval '3 hours') AS due_at
      FROM subscribers s LEFT JOIN subscriber_preferences p USING (chat_id)
    ) SELECT json_build_object(
      'total', count(*),
      'active', count(*) FILTER (WHERE is_active AND NOT in_setup),
      'setup', count(*) FILTER (WHERE is_active AND in_setup),
      'stopped', count(*) FILTER (WHERE NOT is_active),
      'due', count(*) FILTER (WHERE is_active AND NOT in_setup AND due_at <= now()),
      'next_due', min(due_at) FILTER (WHERE is_active AND NOT in_setup),
      'groups', COALESCE((SELECT json_agg(g) FROM (
        SELECT learning, explanation, level, minutes, count(*) AS subscribers,
          count(*) FILTER (WHERE due_at <= now()) AS due
        FROM audience WHERE is_active AND NOT in_setup
        GROUP BY learning, explanation, level, minutes ORDER BY learning, level, minutes
      ) g), '[]'::json)
    ) AS summary FROM audience`);
    const recent = await client.query('SELECT level, learning_language, phrase, video_title, sent_at FROM sent_phrases ORDER BY sent_at DESC LIMIT 20');
    const exists = await client.query("SELECT to_regclass('delivery_runs') AS name");
    const runs = exists.rows[0]?.name ? await client.query('SELECT status, due_count, finished_at FROM delivery_runs ORDER BY id DESC LIMIT 30') : { rows: [] };
    await client.query('COMMIT');
    return { ...result.rows[0].summary, recent: recent.rows, runs: runs.rows, updated_at: new Date().toISOString() };
  } finally { await client.end(); }
}
