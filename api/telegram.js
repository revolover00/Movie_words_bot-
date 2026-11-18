// Telegram webhook: subscribe, change CEFR level, and see the latest expression.
import pg from 'pg';

const { Client } = pg;
const LEVELS = ['A2', 'B1', 'B2', 'C1', 'C2'];
const LANGUAGES = [
  ['en', 'English'], ['zh', '中文'], ['hi', 'हिन्दी'], ['es', 'Español'],
  ['fr', 'Français'], ['ar', 'العربية'], ['pt', 'Português'], ['ru', 'Русский'],
  ['de', 'Deutsch'], ['ja', '日本語'],
];
const CODES = new Set(LANGUAGES.map(([code]) => code));
const languageKeyboard = (kind) => ({ inline_keyboard: Array.from({ length: 5 }, (_, row) =>
  LANGUAGES.slice(row * 2, row * 2 + 2).map(([code, label]) => ({ text: label, callback_data: `${kind}:${code}` }))) });
const WELCOME = 'أهلاً بيك 🎬\nهيوصلك تعبير ومقطع من فيلم حسب مستواك وإعداداتك.\n\nاختار مستواك من الأزرار، وتقدر تغيّره بـ /level.\n/learn — لغة التعلّم\n/explain — لغة الشرح\n/interval — الوقت بين الرسائل (من ٥ لـ ١٤٤٠ دقيقة)\n/today — آخر تعبير لمستواك\n/stop — إلغاء الاشتراك';
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
    await client.query("ALTER TABLE sent_phrases ADD COLUMN IF NOT EXISTS learning_language TEXT NOT NULL DEFAULT 'en'");
    await client.query(`CREATE TABLE IF NOT EXISTS subscriber_preferences (
      chat_id BIGINT PRIMARY KEY REFERENCES subscribers(chat_id) ON DELETE CASCADE,
      learning_language TEXT NOT NULL DEFAULT 'en' CHECK (learning_language IN ('en','zh','hi','es','fr','ar','pt','ru','de','ja')),
      explanation_language TEXT NOT NULL DEFAULT 'ar' CHECK (explanation_language IN ('en','zh','hi','es','fr','ar','pt','ru','de','ja')),
      interval_minutes INTEGER NOT NULL DEFAULT 180 CHECK (interval_minutes BETWEEN 5 AND 1440),
      next_due_at TIMESTAMPTZ, input_state TEXT, updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )`);
    await client.query('ALTER TABLE subscriber_preferences ADD COLUMN IF NOT EXISTS input_state TEXT');
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
  await telegram('sendMessage', { chat_id: chatId, text, ...(keyboard ? { reply_markup: keyboard === true ? KEYBOARD : keyboard } : {}) });
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(200).send('Movie Word Bot webhook');
  try {
    const update = req.body || {};
    const callback = update.callback_query;
    if (callback) {
      const chat = callback.message?.chat;
      const [kind, value] = (callback.data || '').split(':');
      const valid = (kind === 'level' && LEVELS.includes(value)) ||
        (['learn', 'explain'].includes(kind) && CODES.has(value));
      if (!chat || chat.type !== 'private' || callback.from?.id !== chat.id || !valid) {
        await telegram('answerCallbackQuery', { callback_query_id: callback.id, text: 'اختيار غير صالح' });
        return res.status(200).send('ok');
      }
      const result = await withDb(async client => {
        if (kind === 'level') return client.query(
          'UPDATE subscribers SET level = $1 WHERE chat_id = $2 AND is_active = TRUE RETURNING level', [value, chat.id]);
        // Insert only for active subscribers, preserving all other preferences.
        const column = kind === 'learn' ? 'learning_language' : 'explanation_language';
        return client.query(`INSERT INTO subscriber_preferences (chat_id, ${column}, next_due_at)
          SELECT chat_id, $1, subscribed_at + interval '3 hours' FROM subscribers WHERE chat_id = $2 AND is_active = TRUE
          ON CONFLICT (chat_id) DO UPDATE SET ${column} = EXCLUDED.${column}, updated_at = now()
          RETURNING ${column}`, [value, chat.id]);
      });
      await telegram('answerCallbackQuery', { callback_query_id: callback.id });
      await sendMessage(chat.id, result.rowCount ? `تمام ✅ ${kind === 'level' ? 'مستواك' : kind === 'learn' ? 'لغة التعلّم' : 'لغة الشرح'}: ${value}.` : 'اشترك الأول باستخدام /start');
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
    } else if (command === '/learn' || command === '/explain') {
      const kind = command === '/learn' ? 'learn' : 'explain';
      await sendMessage(chatId, kind === 'learn' ? 'اختار اللغة اللي عايز تتعلمها:' : 'اختار لغة الشرح:', languageKeyboard(kind));
    } else if (command === '/interval') {
      const result = await withDb(client => client.query(`INSERT INTO subscriber_preferences (chat_id, input_state, next_due_at)
        SELECT chat_id, 'interval', subscribed_at + interval '3 hours' FROM subscribers WHERE chat_id = $1 AND is_active = TRUE
        ON CONFLICT (chat_id) DO UPDATE SET input_state = 'interval' RETURNING chat_id`, [chatId]));
      await sendMessage(chatId, result.rowCount ? 'ابعت عدد الدقايق بين الرسائل، من ٥ لحد ١٤٤٠.' : 'اشترك الأول باستخدام /start');
    } else if (command === '/level') {
      const result = await withDb(client => client.query('SELECT level FROM subscribers WHERE chat_id = $1 AND is_active = TRUE', [chatId]));
      await sendMessage(chatId, result.rows.length ? `مستواك الحالي ${result.rows[0].level}. اختار مستوى جديد:` : 'اشترك الأول باستخدام /start', result.rows.length > 0);
    } else if (command === '/stop') {
      await withDb(client => client.query('UPDATE subscribers SET is_active = FALSE WHERE chat_id = $1', [chatId]));
      await sendMessage(chatId, 'تم إلغاء الاشتراك. تقدر ترجع بـ /start 👋');
    } else if (command === '/today') {
      const result = await withDb(client => client.query(`SELECT s.level, p.phrase, p.video_title
        FROM subscribers s
        LEFT JOIN subscriber_preferences settings ON settings.chat_id = s.chat_id
        LEFT JOIN LATERAL (
          SELECT phrase, video_title FROM sent_phrases
          WHERE level = s.level AND learning_language = COALESCE(settings.learning_language, 'en')
          ORDER BY sent_at DESC LIMIT 1
        ) p ON TRUE WHERE s.chat_id = $1 AND s.is_active = TRUE`, [chatId]));
      const row = result.rows[0];
      await sendMessage(chatId, !row ? 'اشترك الأول باستخدام /start' : row.phrase
        ? `🎬 آخر تعبير لمستوى ${row.level}: ${row.phrase}\n🎞️ من: ${row.video_title || '—'}`
        : `لسه مفيش تعبير اتبعت لمستوى ${row.level} ⏳`);
    } else if (command === '/help') {
      await sendMessage(chatId, WELCOME, true);
    } else if (message.text && !command.startsWith('/')) {
      const input = message.text.trim().replace(/[٠-٩]/g, d => String(d.charCodeAt(0) - 0x660)).replace(/[۰-۹]/g, d => String(d.charCodeAt(0) - 0x6f0));
      const result = await withDb(async client => {
        const state = await client.query("SELECT input_state FROM subscriber_preferences WHERE chat_id = $1", [chatId]);
        if (state.rows[0]?.input_state !== 'interval') return 'none';
        if (!/^[0-9]{1,4}$/.test(input) || Number(input) < 5 || Number(input) > 1440) return 'invalid';
        await client.query(`UPDATE subscriber_preferences SET interval_minutes = $1,
          next_due_at = now() + ($1 * interval '1 minute'), input_state = NULL, updated_at = now()
          WHERE chat_id = $2 AND input_state = 'interval'`, [Number(input), chatId]);
        return 'saved';
      });
      if (result === 'saved') await sendMessage(chatId, `تمام ✅ المدة بين الرسائل ${Number(input)} دقيقة.`);
      else if (result === 'invalid') await sendMessage(chatId, 'ابعت رقم صحيح من ٥ لحد ١٤٤٠ دقيقة.');
    }
  } catch (err) {
    console.error('webhook error', err);
    return res.status(500).send('temporary error');
  }
  return res.status(200).send('ok');
}
