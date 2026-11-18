# Movie Word Bot 🎬

A free, open-source Telegram bot that sends subscribers **one English word per day** with a **short movie clip** where the word is spoken, plus its meaning in Egyptian Arabic.

> Learn English by watching movies — one word a day, zero cost, zero self-hosting.

## How it works

```
cron-job.org (every 3 hours)
    │  POST → GitHub API (repository_dispatch)
    ▼
GitHub Actions (free ephemeral runner)
    │
    ▼
daily_job.py
    ├─ Groq API        → word meaning (Egyptian Arabic) + example
    ├─ Yarn            → find a movie quote containing the word and download its clip
    ├─ Neon Postgres   → subscribers list + already-sent words
    ▼
Telegram Bot API       → send video + caption to all subscribers
```

New users subscribe via `/start` (handled by `bot.py` with long polling).

## Stack

| Tool | Role |
| --- | --- |
| cron-job.org | Every 3 hours (HTTP POST) |
| GitHub Actions | Free ephemeral worker |
| Python + python-telegram-bot | The bot |
| Neon (Postgres) | Database |
| Yarn | Movie quote search and short clips |
| Groq API (`qwen/qwen3.8-27b`) | Word meanings |

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
handles `/start`, `/stop`, `/help`, `/today` and talks to Neon over TLS.

### 5b. Alternative: Cloudflare Worker (needs a desktop/CLI)

```bash
npm i -g wrangler
wrangler login
wrangler secret put BOT_TOKEN
wrangler secret put DATABASE_URL
wrangler deploy
```

Then point Telegram at `https://<worker-url>` the same way.

For local testing you can still run `python bot.py` (polling) instead.

### 6. Run locally (optional)

```bash
pip install -r requirements.txt
sudo apt-get install ffmpeg   # or: brew install ffmpeg
python daily_job.py  # sends today's word immediately
```

### 7. Automate with GitHub Actions

1. Push this repo to GitHub (public repo → free Actions minutes).
2. Add secrets: **Settings → Secrets and variables → Actions** → `BOT_TOKEN`, `DATABASE_URL`, `GROQ_API_KEY`.
3. Merge the workflow into the default branch. You can also trigger it manually from the **Actions** tab.

### 8. Schedule via cron-job.org

Create a free job on [cron-job.org](https://cron-job.org) scheduled every 3 hours that POSTs to:

```
https://api.github.com/repos/<OWNER>/<REPO>/dispatches
```

with headers `Authorization: Bearer <PAT>`, `Accept: application/vnd.github+json`, and `Content-Type: application/json`, and body `{"event_type": "daily-word"}`.
The PAT needs `repo` scope (classic) or repository Contents read and write permission (fine-grained). The workflow must exist on the default branch. Store the token only in the scheduler, not in the repository.

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
yarn_clips.py        # Yarn movie quote search and clip download
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
```

## Notes

- Yarn integration parses public web pages, which may change or become unavailable.
- Words are English by default; meanings come in Egyptian Arabic. To switch languages, edit `words.txt` and the prompt in `groq_meaning.py`.
- Clips are short excerpts from Yarn for educational use.

## License

MIT — see [LICENSE](LICENSE).
