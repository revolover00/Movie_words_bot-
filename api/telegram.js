// Telegram webhook: subscribe, change CEFR level, and see the latest expression.
import pg from 'pg';
import { text, intervalLabel, validInterval, intervalKeyboard, levelKeyboard, uiKeyboard, UI_LANGUAGES } from '../bot_ui.js';

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
const label = code => LANGUAGES.find(([key]) => key === code)?.[1] || code;
const fallbackLanguage = user => user?.language_code?.toLowerCase().startsWith('en') ? 'en' : 'ar';
async function interfaceLanguage(chatId, fallback) {
  return withDb(async client => {
    const result = await client.query('SELECT ui_language FROM subscriber_preferences WHERE chat_id = $1', [chatId]);
    return result.rows[0]?.ui_language || fallback;
  });
}

async function setupPrompt(chatId, state, settings = {}, fallback = 'ar', messageId) {
  const lang = settings.ui_language || fallback;
  const keyboards = {
    setup_ui: () => uiKeyboard('setup_ui'),
    setup_learn: () => languageKeyboard('setup_learn'),
    setup_level: () => levelKeyboard('setup_level', lang),
    setup_explain: () => languageKeyboard('setup_explain'),
    setup_interval: () => intervalKeyboard('setup_interval', lang),
  };
  if (keyboards[state]) {
    const keyboard = keyboards[state]();
    if (state !== 'setup_ui') keyboard.inline_keyboard.push([{ text: text(lang, 'back'), callback_data: 'setup_back:yes' }]);
    return renderMessage(chatId, text(lang, state), keyboard, messageId);
  }
  return renderMessage(chatId, text(lang, 'review', {
    learn: label(settings.learning_language), level: settings.level,
    explain: label(settings.explanation_language), interval: intervalLabel(settings.interval_minutes, lang),
  }), { inline_keyboard: [[{ text: text(lang, 'confirm'), callback_data: 'setup_confirm:yes' }],
    [{ text: text(lang, 'restart'), callback_data: 'setup_restart:yes' }]] }, messageId);
}

// Persist and lock each step so stale buttons cannot skip or overwrite steps.
async function setupChoice(client, chatId, kind, value) {
  await client.query('BEGIN');
  try {
    const result = await client.query(`SELECT p.*, s.level FROM subscriber_preferences p JOIN subscribers s USING (chat_id)
      WHERE p.chat_id = $1 AND s.is_active = TRUE FOR UPDATE OF p`, [chatId]);
    const settings = result.rows[0];
    if (!settings?.input_state?.startsWith('setup_')) {
      await client.query('COMMIT');
      return { missing: true };
    }
    if (kind !== settings.input_state && !['setup_restart', 'setup_back'].includes(kind)) {
      await client.query('COMMIT');
      return { state: settings.input_state, settings };
    }
    const previous = { setup_ui: 'setup_ui', setup_learn: 'setup_ui', setup_level: 'setup_learn', setup_explain: 'setup_level', setup_interval: 'setup_explain', setup_confirm: 'setup_interval' };
    const next = kind === 'setup_back' ? previous[settings.input_state] : { setup_ui: 'setup_learn', setup_learn: 'setup_level', setup_level: 'setup_explain', setup_explain: 'setup_interval', setup_interval: 'setup_confirm', setup_restart: 'setup_ui', setup_confirm: null }[kind];
    if (kind === 'setup_level') {
      await client.query('UPDATE subscribers SET level = $1 WHERE chat_id = $2', [value, chatId]);
      settings.level = value;
    }
    const column = { setup_ui: 'ui_language', setup_learn: 'learning_language', setup_explain: 'explanation_language', setup_interval: 'interval_minutes' }[kind];
    if (column) {
      settings[column] = kind === 'setup_interval' ? Number(value) : value;
      await client.query(`UPDATE subscriber_preferences SET ${column} = $1 WHERE chat_id = $2`, [settings[column], chatId]);
    }
    await client.query(`UPDATE subscriber_preferences SET input_state = $1, updated_at = now(),
      next_due_at = CASE WHEN $1::text IS NULL THEN now() + interval_minutes * interval '1 minute' ELSE next_due_at END
      WHERE chat_id = $2`, [next, chatId]);
    await client.query('COMMIT');
    return { state: next, settings };
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  }
}

async function withDb(fn) {
  const client = new Client({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } });
  await client.connect();
  try {
    const botId = (process.env.BOT_TOKEN || '').split(':')[0];
    if (!/^[0-9]+$/.test(botId)) throw new Error('A valid BOT_TOKEN is required');
    // Digits-only bot ID keeps this identifier safe and stable across token rotations.
    const schema = `bot_${botId}`;
    await client.query(`CREATE SCHEMA IF NOT EXISTS "${schema}"`);
    await client.query(`SET search_path TO "${schema}"`);
    await client.query(`CREATE TABLE IF NOT EXISTS subscribers (
      chat_id BIGINT PRIMARY KEY, username TEXT, first_name TEXT,
      subscribed_at TIMESTAMPTZ NOT NULL DEFAULT now(), is_active BOOLEAN NOT NULL DEFAULT TRUE
    )`);
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
      interval_minutes INTEGER NOT NULL DEFAULT 180 CHECK (interval_minutes BETWEEN 30 AND 1440),
      next_due_at TIMESTAMPTZ, input_state TEXT, updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )`);
    await client.query('ALTER TABLE subscriber_preferences ADD COLUMN IF NOT EXISTS input_state TEXT');
    await client.query("ALTER TABLE subscriber_preferences ADD COLUMN IF NOT EXISTS ui_language TEXT NOT NULL DEFAULT 'ar' CHECK (ui_language IN ('ar', 'en'))");
    await client.query(`DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'subscriber_preferences'::regclass
        AND conname = 'subscriber_preferences_interval_minutes_check'
        AND pg_get_constraintdef(oid) NOT LIKE '%30%') THEN

-- Raise old short intervals while preserving the remaining preferences.
ALTER TABLE subscriber_preferences DROP CONSTRAINT IF EXISTS subscriber_preferences_interval_minutes_check;
UPDATE subscriber_preferences SET interval_minutes = 30,
    next_due_at = GREATEST(next_due_at, now() + interval '30 minutes'), updated_at = now()
    WHERE interval_minutes < 30;
ALTER TABLE subscriber_preferences ADD CONSTRAINT subscriber_preferences_interval_minutes_check
    CHECK (interval_minutes BETWEEN 30 AND 1440);
      END IF;
    END $$`);
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
  // Repeated taps and retried callbacks may render exactly the same screen.
  if (method === 'editMessageText' && body.error_code === 400 &&
      body.description?.includes('message is not modified')) return;
  if (!response.ok || !body.ok) throw new Error(`Telegram ${method} failed: ${body.description || response.status}`);
}

async function sendMessage(chatId, text, keyboard) {
  await telegram('sendMessage', { chat_id: chatId, text, ...(keyboard ? { reply_markup: keyboard } : {}) });
}

// Only the initial command sends a message. Button navigation edits that message.
async function renderMessage(chatId, text, keyboard, messageId) {
  if (messageId == null) return sendMessage(chatId, text, keyboard);
  await telegram('editMessageText', {
    chat_id: chatId, message_id: messageId, text,
    reply_markup: keyboard || { inline_keyboard: [] },
  });
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(200).send('Movie Word Bot webhook');
  try {
    const update = req.body || {};
    const callback = update.callback_query;
    if (callback) {
      const chat = callback.message?.chat;
      const messageId = callback.message?.message_id;
      const [kind, value] = (callback.data || '').split(':');
      const valid = (['level', 'setup_level'].includes(kind) && LEVELS.includes(value)) ||
        (['ui', 'setup_ui'].includes(kind) && UI_LANGUAGES.has(value)) ||
        (['setup_learn', 'setup_explain'].includes(kind) && CODES.has(value)) ||
        (['interval', 'setup_interval'].includes(kind) && validInterval(value)) ||
        (['setup_confirm', 'setup_restart', 'setup_back'].includes(kind) && value === 'yes') ||
        (['learn', 'explain'].includes(kind) && CODES.has(value));
      if (!chat || chat.type !== 'private' || callback.from?.id !== chat.id || !valid) {
        await telegram('answerCallbackQuery', { callback_query_id: callback.id, text: text(fallbackLanguage(callback.from), 'invalid') });
        return res.status(200).send('ok');
      }
      const lang = await interfaceLanguage(chat.id, fallbackLanguage(callback.from));
      if (kind.startsWith('setup_')) {
        const result = await withDb(client => setupChoice(client, chat.id, kind, value));
        await telegram('answerCallbackQuery', { callback_query_id: callback.id });
        if (result.missing) await renderMessage(chat.id, text(lang, 'missing'), undefined, messageId);
        else if (result.state) await setupPrompt(chat.id, result.state, result.settings, lang, messageId);
        else await renderMessage(chat.id, text(lang, 'done', { interval: intervalLabel(result.settings.interval_minutes, lang) }), undefined, messageId);
        return res.status(200).send('ok');
      }
      const result = await withDb(async client => {
        const state = await client.query('SELECT input_state FROM subscriber_preferences WHERE chat_id = $1', [chat.id]);
        if (state.rows[0]?.input_state?.startsWith('setup_')) {
          const settings = await client.query('SELECT p.*, s.level FROM subscriber_preferences p JOIN subscribers s USING (chat_id) WHERE p.chat_id = $1', [chat.id]);
          return { setup: state.rows[0].input_state, settings: settings.rows[0] };
        }
        if (kind === 'ui') return client.query(`INSERT INTO subscriber_preferences (chat_id, ui_language, next_due_at)
          SELECT chat_id, $1, subscribed_at + interval '3 hours' FROM subscribers WHERE chat_id = $2 AND is_active = TRUE
          ON CONFLICT (chat_id) DO UPDATE SET ui_language = EXCLUDED.ui_language, updated_at = now() RETURNING chat_id`, [value, chat.id]);
        if (kind === 'interval') return client.query(`UPDATE subscriber_preferences p SET interval_minutes = $1,
          next_due_at = now() + ($1 * interval '1 minute'), input_state = NULL, updated_at = now()
          FROM subscribers s WHERE p.chat_id = $2 AND s.chat_id = p.chat_id AND s.is_active = TRUE RETURNING p.chat_id`, [Number(value), chat.id]);
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
      if (result.setup) {
        await setupPrompt(chat.id, result.setup, result.settings, lang, messageId);
        return res.status(200).send('ok');
      }
      const displayValue = kind === 'interval' ? intervalLabel(value, lang) : label(value);
      await renderMessage(chat.id, result.rowCount
        ? text(kind === 'ui' ? value : lang, `saved_${kind}`, { value: displayValue })
        : text(lang, 'subscribe'), undefined, messageId);
      return res.status(200).send('ok');
    }
    const message = update.message || {};
    const chat = message.chat;
    if (!chat || chat.type !== 'private') return res.status(200).send('ok');
    const command = (message.text || '').trim().split(/\s+/)[0].split('@')[0].toLowerCase();
    const chatId = chat.id;
    const lang = await interfaceLanguage(chatId, fallbackLanguage(message.from));
    if (command === '/start') {
      await withDb(async client => {
        await client.query('BEGIN');
        try {
          await client.query(`INSERT INTO subscribers (chat_id, username, first_name, is_active)
            VALUES ($1, $2, $3, TRUE) ON CONFLICT (chat_id) DO UPDATE
            SET username = EXCLUDED.username, first_name = EXCLUDED.first_name, is_active = TRUE`,
          [chatId, message.from?.username || null, message.from?.first_name || null]);
          await client.query(`INSERT INTO subscriber_preferences (chat_id, input_state, ui_language)
            VALUES ($1, 'setup_ui', $2) ON CONFLICT (chat_id) DO UPDATE
            SET input_state = 'setup_ui', updated_at = now()`, [chatId, lang]);
          await client.query('COMMIT');
        } catch (error) { await client.query('ROLLBACK'); throw error; }
      });
      await setupPrompt(chatId, 'setup_ui', {}, lang);
    } else if (['/learn', '/explain', '/level', '/interval', '/language'].includes(command) && await withDb(async client => {
      const state = await client.query('SELECT input_state FROM subscriber_preferences WHERE chat_id = $1', [chatId]);
      if (!state.rows[0]?.input_state?.startsWith('setup_')) return false;
      // Re-open the wizard without showing an incomplete review.
      const result = await client.query('SELECT p.*, s.level FROM subscriber_preferences p JOIN subscribers s USING (chat_id) WHERE p.chat_id = $1', [chatId]);
      await setupPrompt(chatId, state.rows[0].input_state, result.rows[0], lang);
      return true;
    })) {
      // Finish the current setup before editing individual settings.
    } else if (command === '/language') {
      await sendMessage(chatId, text(lang, 'choose_ui'), uiKeyboard());
    } else if (command === '/learn' || command === '/explain') {
      const kind = command === '/learn' ? 'learn' : 'explain';
      await sendMessage(chatId, text(lang, kind), languageKeyboard(kind));
    } else if (command === '/interval') {
      const result = await withDb(client => client.query(`INSERT INTO subscriber_preferences (chat_id, input_state, next_due_at)
        SELECT chat_id, 'interval', subscribed_at + interval '3 hours' FROM subscribers WHERE chat_id = $1 AND is_active = TRUE
        ON CONFLICT (chat_id) DO UPDATE SET input_state = 'interval' RETURNING chat_id`, [chatId]));
      await sendMessage(chatId, text(lang, result.rowCount ? 'interval' : 'subscribe'), result.rowCount ? intervalKeyboard('interval', lang) : undefined);
    } else if (command === '/level') {
      const result = await withDb(client => client.query('SELECT level FROM subscribers WHERE chat_id = $1 AND is_active = TRUE', [chatId]));
      await sendMessage(chatId, result.rows.length ? text(lang, 'level', { level: result.rows[0].level }) : text(lang, 'subscribe'), result.rows.length ? levelKeyboard('level', lang) : undefined);
    } else if (command === '/stop') {
      await withDb(client => client.query('UPDATE subscribers SET is_active = FALSE WHERE chat_id = $1', [chatId]));
      await sendMessage(chatId, text(lang, 'stopped'));
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
      await sendMessage(chatId, !row ? text(lang, 'subscribe') : row.phrase
        ? text(lang, 'today', { level: row.level, phrase: row.phrase, title: row.video_title || '—' })
        : text(lang, 'empty', { level: row.level }));
    } else if (command === '/help') {
      await sendMessage(chatId, text(lang, 'welcome'));
    } else if (message.text) {
      const result = await withDb(client => client.query(`SELECT p.*, s.level FROM subscriber_preferences p
        JOIN subscribers s USING (chat_id) WHERE p.chat_id = $1 AND s.is_active = TRUE`, [chatId]));
      const settings = result.rows[0];
      if (settings?.input_state?.startsWith('setup_')) {
        await setupPrompt(chatId, settings.input_state, settings, lang);
      } else if (settings?.input_state === 'interval') {
        await sendMessage(chatId, text(lang, 'buttons'), intervalKeyboard('interval', lang));
      } else {
        await sendMessage(chatId, text(lang, 'unknown'));
      }
    }

  } catch (err) {
    console.error('webhook error', err);
    return res.status(500).send('temporary error');
  }
  return res.status(200).send('ok');
}
