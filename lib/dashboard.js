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
    const runs = exists.rows[0]?.name ? await client.query('SELECT * FROM delivery_runs ORDER BY id DESC LIMIT 30') : { rows: [] };
    const reliable = await client.query("SELECT to_regclass('delivery_attempts') AS name");
    let delivery = { sent:0, failed:0, uncertain:0, blocked:0, cached:0, saved:0, reports:0, errors:[] };
    let ai = {requests:0,failed:0,prompt_tokens:0,completion_tokens:0,unreported:0};
    if (reliable.rows[0]?.name) {
      const counts = await client.query(`SELECT
        count(*) FILTER(WHERE status='sent')::int AS sent,
        count(*) FILTER(WHERE status='failed')::int AS failed,
        count(*) FILTER(WHERE status IN ('uncertain','sending'))::int AS uncertain,
        count(*) FILTER(WHERE status='blocked')::int AS blocked,
        (SELECT count(*)::int FROM lesson_content WHERE telegram_file_id IS NOT NULL) AS cached,
        (SELECT count(*)::int FROM saved_lessons) AS saved,
        (SELECT count(*)::int FROM lesson_feedback) AS reports FROM delivery_attempts`);
      const errors = await client.query(`SELECT status,error_code,updated_at FROM delivery_attempts
        WHERE error_code IS NOT NULL ORDER BY updated_at DESC LIMIT 20`);
      delivery = {...counts.rows[0],errors:errors.rows};
      const usage = await client.query(`SELECT count(*)::int AS requests,count(*) FILTER(WHERE status='failed')::int AS failed,
        COALESCE(sum(prompt_tokens),0)::float AS prompt_tokens, COALESCE(sum(completion_tokens),0)::float AS completion_tokens,
        count(*) FILTER(WHERE prompt_tokens IS NULL AND completion_tokens IS NULL)::int AS unreported FROM ai_usage`);
      ai = usage.rows[0];
    }
    await client.query('COMMIT');
    return { ...result.rows[0].summary, recent: recent.rows, runs: runs.rows, delivery, ai, updated_at: new Date().toISOString() };
  } finally { await client.end(); }
}
