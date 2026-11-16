// Movie Word Bot — Telegram webhook (Vercel serverless function, Node 18+)
// Handles /start, /stop, /help, /today and writes to Neon Postgres.
// Deploy: import the repo on vercel.com → set env vars → deploy.
// Then point Telegram at it:
//   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<app>.vercel.app/api/telegram

import pg from "pg";

const { Client } = pg;

const WELCOME =
  "أهلاً بيك في بوت كلمات الأفلام 🎬\n\n" +
  "كل يوم هبعتلك كلمة جديدة + لقطة من فيلم اتقالت فيها.\n" +
  "هتتعلم إنجليزي وانت بتتفرج 😎\n\n" +
  "/today — آخر كلمة اتبعتت\n" +
  "/stop — إلغاء الاشتراك";

async function query(text, params) {
  const client = new Client({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false },
  });
  await client.connect();
  try {
    return await client.query(text, params);
  } finally {
    await client.end();
  }
}

async function sendMessage(token, chatId, text) {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text }),
  });
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(200).send("Movie Word Bot webhook");
    return;
  }
  try {
    const update = req.body || {};
    const message = update.message || {};
    const chatId = message.chat && message.chat.id;
    if (!chatId) {
      res.status(200).send("ok");
      return;
    }
    const text = (message.text || "").trim();
    const username = message.from ? message.from.username || null : null;
    const firstName = message.from ? message.from.first_name || null : null;
    const token = process.env.BOT_TOKEN;

    if (text.startsWith("/start")) {
      await query(
        `INSERT INTO subscribers (chat_id, username, first_name, is_active)
         VALUES ($1, $2, $3, TRUE)
         ON CONFLICT (chat_id) DO UPDATE
         SET username = EXCLUDED.username,
             first_name = EXCLUDED.first_name,
             is_active = TRUE`,
        [chatId, username, firstName]
      );
      await sendMessage(token, chatId, WELCOME);
    } else if (text.startsWith("/stop")) {
      await query(
        "UPDATE subscribers SET is_active = FALSE WHERE chat_id = $1",
        [chatId]
      );
      await sendMessage(token, chatId, "تم إلغاء الاشتراك. نراك قريباً 👋");
    } else if (text.startsWith("/today")) {
      const { rows } = await query(
        "SELECT word, video_title FROM sent_words ORDER BY sent_at DESC LIMIT 1"
      );
      const msg = rows.length
        ? `🎬 آخر كلمة: ${rows[0].word}\n🎞️ من: ${rows[0].video_title || "—"}`
        : "لسه مفيش كلمات اتبعتت. استنى أول كلمة النهاردة ⏳";
      await sendMessage(token, chatId, msg);
    } else if (text.startsWith("/help")) {
      await sendMessage(token, chatId, WELCOME);
    }
  } catch (err) {
    console.error("webhook error", err);
  }
  res.status(200).send("ok");
}
