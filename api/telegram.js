// Telegram webhook: subscribe, change CEFR level, and see the latest expression.
import pg from 'pg';

const { Client } = pg;
const LEVELS = ['A2', 'B1', 'B2', 'C1', 'C2'];
const WELCOME = 'أهلاً بيك 🎬\nهيوصلك تعبير إنجليزي مع معناه بالمصري ومقطع من فيلم حسب مستواك.\n\nاختار مستواك من الأزرار، وتقدر تغيّره في أي وقت بـ /level.\n/today — آخر تعبير لمستواك\n/stop — إلغاء الاشتراك';
const KEYBOARD = { inline_keyboard: [LEVELS.map(level => ({ text: level, callback_data: `level:${level}` }))] };

async function withDb(fn) {
  const client = new Client({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } });
  await client.connect();
  try {
    // Idempotent migration: preserves existing subscriptions and defaults them to A2.
    await client.query("ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS level TEXT NOT NULL DEFAULT 'A2'");
    await client.query(`CREATE TABLE IF NOT EXISTS sent_phrases (
      id BIGSERIAL PRIMARY KEY, level TEXT NOT NULL, phrase TEXT NOT NULL, topic TEXT NOT NULL,
      clip_id TEXT, video_title TEXT, sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )`);
    return await fn(client);
  } finally {
    await client.end();
  }
}

async function telegram(method, payload) {
  const response = await fetch(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/${method}`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok || !body.ok) throw new Error(`Telegram ${method} failed: ${body.description || response.status}`);
}

async function sendMessage(chatId, text, keyboard) {
  await telegram('sendMessage', { chat_id: chatId, text, ...(keyboard ? { reply_markup: KEYBOARD } : {}) });
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(200).send('Movie Word Bot webhook');
  try {
    const update = req.body || {};
    const callback = update.callback_query;
    if (callback) {
      const chat = callback.message?.chat;
      const level = (callback.data || '').startsWith('level:') ? callback.data.slice(6) : '';
      if (!chat || chat.type !== 'private' || callback.from?.id !== chat.id || !LEVELS.includes(level)) {
        await telegram('answerCallbackQuery', { callback_query_id: callback.id, text: 'اختيار غير صالح' });
        return res.status(200).send('ok');
      }
      const result = await withDb(client => client.query(
        'UPDATE subscribers SET level = $1 WHERE chat_id = $2 AND is_active = TRUE RETURNING level',
        [level, chat.id],
      ));
      await telegram('answerCallbackQuery', { callback_query_id: callback.id });
      await sendMessage(chat.id, result.rowCount ? `تمام ✅ مستواك دلوقتي ${level}.` : 'اشترك الأول باستخدام /start');
      return res.status(200).send('ok');
    }
    const message = update.message || {};
    const chat = message.chat;
    if (!chat || chat.type !== 'private') return res.status(200).send('ok');
    const command = (message.text || '').trim().split(/\s+/)[0].split('@')[0].toLowerCase();
    const chatId = chat.id;
    if (command === '/start') {
      await withDb(client => client.query(`INSERT INTO subscribers (chat_id, username, first_name, is_active)
        VALUES ($1, $2, $3, TRUE) ON CONFLICT (chat_id) DO UPDATE
        SET username = EXCLUDED.username, first_name = EXCLUDED.first_name, is_active = TRUE`,
      [chatId, message.from?.username || null, message.from?.first_name || null]));
      await sendMessage(chatId, WELCOME, true);
    } else if (command === '/level') {
      const result = await withDb(client => client.query('SELECT level FROM subscribers WHERE chat_id = $1 AND is_active = TRUE', [chatId]));
      await sendMessage(chatId, result.rows.length ? `مستواك الحالي ${result.rows[0].level}. اختار مستوى جديد:` : 'اشترك الأول باستخدام /start', result.rows.length > 0);
    } else if (command === '/stop') {
      await withDb(client => client.query('UPDATE subscribers SET is_active = FALSE WHERE chat_id = $1', [chatId]));
      await sendMessage(chatId, 'تم إلغاء الاشتراك. تقدر ترجع بـ /start 👋');
    } else if (command === '/today') {
      const result = await withDb(client => client.query(`SELECT s.level, p.phrase, p.video_title
        FROM subscribers s LEFT JOIN LATERAL (
          SELECT phrase, video_title FROM sent_phrases WHERE level = s.level ORDER BY sent_at DESC LIMIT 1
        ) p ON TRUE WHERE s.chat_id = $1 AND s.is_active = TRUE`, [chatId]));
      const row = result.rows[0];
      await sendMessage(chatId, !row ? 'اشترك الأول باستخدام /start' : row.phrase
        ? `🎬 آخر تعبير لمستوى ${row.level}: ${row.phrase}\n🎞️ من: ${row.video_title || '—'}`
        : `لسه مفيش تعبير اتبعت لمستوى ${row.level} ⏳`);
    } else if (command === '/help') {
      await sendMessage(chatId, WELCOME, true);
    }
  } catch (err) {
    console.error('webhook error', err);
  }
  return res.status(200).send('ok');
}
