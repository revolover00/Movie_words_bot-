// SceneLingo — Cloudflare Worker (free 24/7 webhook for /start, /stop, /help)
// Deploy: npm i -g wrangler && wrangler login && wrangler deploy
// Secrets: wrangler secret put BOT_TOKEN / DATABASE_URL
// Then set the webhook: curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WORKER_URL>"

import { neon } from "@neondatabase/serverless";

const WELCOME =
  "أهلاً بيك في بوت كلمات الأفلام 🎬\n\n" +
  "كل يوم هبعتلك كلمة جديدة + لقطة من فيلم اتقالت فيها.\n" +
  "هتتعلم إنجليزي وانت بتتفرج 😎\n\n" +
  "/today — آخر كلمة اتبعتت\n" +
  "/stop — إلغاء الاشتراك";

async function sendMessage(token, chatId, text) {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text }),
  });
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("SceneLingo webhook", { status: 200 });
    }
    const update = await request.json().catch(() => ({}));
    const message = update.message || {};
    const chatId = message.chat?.id;
    if (!chatId) return new Response("ok", { status: 200 });

    const text = (message.text || "").trim();
    const username = message.from?.username || null;
    const firstName = message.from?.first_name || null;
    const sql = neon(env.DATABASE_URL);

    try {
      if (text.startsWith("/start")) {
        await sql`
          INSERT INTO subscribers (chat_id, username, first_name, is_active)
          VALUES (${chatId}, ${username}, ${firstName}, TRUE)
          ON CONFLICT (chat_id) DO UPDATE
          SET username = EXCLUDED.username,
              first_name = EXCLUDED.first_name,
              is_active = TRUE
        `;
        await sendMessage(env.BOT_TOKEN, chatId, WELCOME);
      } else if (text.startsWith("/stop")) {
        await sql`UPDATE subscribers SET is_active = FALSE WHERE chat_id = ${chatId}`;
        await sendMessage(env.BOT_TOKEN, chatId, "تم إلغاء الاشتراك. نراك قريباً 👋");
      } else if (text.startsWith("/today")) {
        const rows = await sql`
          SELECT word, video_title FROM sent_words ORDER BY sent_at DESC LIMIT 1
        `;
        if (rows.length) {
          await sendMessage(
            env.BOT_TOKEN,
            chatId,
            `🎬 آخر كلمة: ${rows[0].word}\n🎞️ من: ${rows[0].video_title || "—"}`
          );
        } else {
          await sendMessage(env.BOT_TOKEN, chatId, "لسه مفيش كلمات اتبعتت. استنى أول كلمة النهاردة ⏳");
        }
      } else if (text.startsWith("/help")) {
        await sendMessage(env.BOT_TOKEN, chatId, WELCOME);
      }
    } catch (err) {
      console.error("webhook error", err);
    }
    return new Response("ok", { status: 200 });
  },
};
