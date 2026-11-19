# Movie Word Bot 🎬

A free, open-source Telegram bot for useful expressions with matching short movie clips and explanations. Subscribers choose a CEFR level, learning language, explanation language and delivery interval inside Telegram.

> Learn languages by watching movies — expressions for your level, zero self-hosting.

> **Multilingual rollout is experimental.** Clip availability varies by language, automatic audio verification is imperfect, and free-tier rate limits and worker duration can delay or prevent delivery. The scheduler is not exactly-once; failures between a Telegram send and the database update can cause duplicates. Test your setup before enabling production delivery.

## How it works

```
cron-job.org (every 2 minutes)
    │  POST → GitHub API (repository_dispatch)
    ▼
GitHub Actions (free ephemeral runner)
    │
    ▼
daily_job.py
    ├─ Neon Postgres   → due subscribers and their preferences
    ├─ Expressions     → curated candidates or transcript-first selection by CEFR level
    ├─ Clip.Cafe       → search and download a clip with a matching audio track
    ├─ Groq Whisper    → verify spoken language and phrase (best effort)
    ├─ Groq Qwen       → localized explanation and example
    ▼
Telegram Bot API       → send to each due subscriber
```

Use `/start` for guided setup: bot interface language (Arabic or English) → learning language → CEFR level → explanation language → delivery interval → review and confirm. Delivery starts only after confirmation. Use `/level` to pick A2–C2, `/learn` for the learning language, `/explain` for the explanation language, and `/interval` to choose a preset from 30 minutes to 24 hours. `/today` shows the most recent expression for the selected level and learning language; `/stop` unsubscribes. Both language menus offer English, Chinese, Hindi, Spanish, French, Arabic, Portuguese, Russian, German and Japanese. Intervals offer preset buttons (half an hour to 24 hours) only; typed numbers are not accepted. `/language` changes the bot interface language without changing learning or explanation preferences. Existing intervals below 30 minutes are raised to 30. Existing subscribers retain their subscription and default to English, Egyptian Arabic and 180 minutes. CEFR labels are approximate.

## Stack

| Tool | Role |
| --- | --- |
| cron-job.org | Every 2 minutes (HTTP POST) |
| GitHub Actions | Free ephemeral worker |
| Python + python-telegram-bot | The bot |
| Neon (Postgres) | Database |
| Clip.Cafe | Movie quote search and short clips |
| Groq API (`qwen/qwen3.8-27b`, Whisper) | Expressions, explanations and audio verification |

## Setup

### 1. Create the Telegram bot

Chat with [@BotFather](https://t.me/BotFather) → `/newbot` → copy the `BOT_TOKEN`.

### 2. Create the database

- Sign up at [Neon](https://neon.tech) (free, no credit card) → create a project → copy the **connection string** (`DATABASE_URL`).
- Run the schema once:
  ```bash
  pip install -r requirements.txt
  DATABASE_URL=postgresql://... python -m db
  ```

### 3. Get a Groq API key

- Sign up at [Groq](https://console.groq.com) → API Keys → create key (`GROQ_API_KEY`).

### 4. Configure

```bash
cp .env.example .env
# fill in BOT_TOKEN, DATABASE_URL, GROQ_API_KEY
```

### 5. Handle /start for free (Vercel, browser-only)

`bot.py` uses polling and needs a running process. For 24/7 free hosting
that works entirely from a phone browser:

1. Open [vercel.com](https://vercel.com) → sign in with GitHub → **Add New → Project**
   → import this repo. Framework preset: **Other**.
2. Add environment variables: `BOT_TOKEN`, `DATABASE_URL`.
3. Deploy. Then open this URL in your browser:

```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-app>.vercel.app/api/telegram
```

Telegram replies `{"ok":true,...}` — done. The function in `api/telegram.js`
handles the Telegram controls and talks to Neon over TLS. The webhook and scheduled job apply additive migrations automatically.

### 5b. Legacy Cloudflare Worker (does not support levels)

```bash
npm i -g wrangler
wrangler login
wrangler secret put BOT_TOKEN
wrangler secret put DATABASE_URL
wrangler deploy
```

This legacy worker does not implement level selection; use the Vercel webhook above for this version.

For local testing you can still run `python bot.py` (polling) instead.

### 6. Run locally (optional)

The `imageio-ffmpeg` dependency supplies FFmpeg when no system binary is available. A system `ffprobe`, if installed, is used for the stream-language precheck; otherwise the bundled FFmpeg inspects the stream.

```bash
pip install -r requirements.txt
python daily_job.py  # sends to subscribers whose delivery time is due
```

### 7. Automate with GitHub Actions

1. Push this repo to GitHub (public repo → free Actions minutes).
2. Add secrets: **Settings → Secrets and variables → Actions** → `BOT_TOKEN`, `DATABASE_URL`, `GROQ_API_KEY`.
3. Merge the workflow into the default branch. You can also trigger it manually from the **Actions** tab.

### 8. Schedule via cron-job.org

Create a free job on [cron-job.org](https://cron-job.org) scheduled every 2 minutes that POSTs to:

```
https://api.github.com/repos/<OWNER>/<REPO>/dispatches
```

with headers `Authorization: Bearer <PAT>`, `Accept: application/vnd.github+json`, and `Content-Type: application/json`, and body `{"event_type": "daily-word"}`.
The PAT needs `repo` scope (classic) or repository Contents read and write permission (fine-grained). The workflow must exist on the default branch and be enabled. Store the token only in the scheduler, not in the repository. This polling interval is not a delivery-time guarantee: Actions queueing, source availability, verification and rate limits can delay or prevent messages.

## Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `BOT_TOKEN` | ✅ | — | Telegram bot token |
| `DATABASE_URL` | ✅ | — | Neon Postgres connection string |
| `GROQ_API_KEY` | ✅ | — | Groq API key |
| `GROQ_MODEL` | | `qwen/qwen3.8-27b` | Groq model |
| `WORDS_FILE` | | `words.txt` | Word bank (one word per line) |
| `CLIP_BEFORE` | | `2` | Seconds before the word |
| `CLIP_AFTER` | | `3` | Seconds after the word |
| `SEND_DELAY` | | `0.2` | Seconds between sends |

## Project structure

```
bot.py               # Telegram bot, /start etc. (polling, for local use)
worker.js            # Cloudflare Worker webhook — free 24/7 /start hosting
daily_job.py         # Daily broadcast pipeline
phrases.py           # CEFR-labelled expressions and topics
clip_cafe.py         # Movie quote search and clip download
yarn_clips.py        # Legacy Yarn integration
youtube_free.py      # Legacy InnerTube search
clipper.py           # yt-dlp + FFmpeg clip cutting
groq_meaning.py      # Groq meanings (with retries)
words.py / words.txt # Word bank
db.py / schema.sql   # Neon Postgres layer
config.py            # Env config
tests/               # pytest suite
.github/workflows/daily.yml  # daily broadcast
.github/workflows/test.yml   # CI tests on push
```

## Testing

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
npm ci
node --test tests/telegram.test.js
```

## Notes

- Clip.Cafe integration parses public pages and HLS playlists, which may change or become unavailable. A localized audio track is combined with the video when available; otherwise the original MP4 is checked.
- English expressions use a curated bank, with generated candidates after it is exhausted. Other languages prefer expressions selected from a verified transcript, then fall back to generated candidates. Clips are only sent after best-effort audio verification. Some language/level combinations may have no usable clip.
- Serialized Actions runs and a pre-send settings check reduce races, but Telegram sends and database updates cannot be atomic. Long-running jobs can delay individual schedules; provider free tiers impose usage limits.
- Clips are short excerpts from Clip.Cafe for educational use.

## License

MIT — see [LICENSE](LICENSE).

### Starting with a different Telegram bot

Each bot now stores subscriptions and expression history in its own Postgres schema,
`bot_<numeric Telegram bot ID>`. Token rotation for the same bot retains its data;
a different bot starts with an empty subscription list. Public/legacy tables are
not deleted or imported. Both the webhook and scheduled sender use this isolation.

Update `BOT_TOKEN` in Vercel and GitHub Actions, deploy, then run **Configure Telegram
bot** with the new bot's numeric ID. The setup verifies the GitHub token belongs to
that bot before initializing its schema or registering the production webhook.
Users must open the new bot, press `/start`, and confirm setup before delivery.
Never put tokens in source files or workflow inputs.
