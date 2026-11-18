# Movie Word Bot 🎬

A free, open-source Telegram bot that sends useful English expressions with a matching short movie clip and an Egyptian Arabic explanation. Subscribers choose a CEFR level from A2 through C2.

> Learn English by watching movies — expressions for your level, zero self-hosting.

## How it works

```
cron-job.org (every 3 hours)
    │  POST → GitHub API (repository_dispatch)
    ▼
GitHub Actions (free ephemeral runner)
    │
    ▼
daily_job.py
    ├─ Curated phrases → expression for each active CEFR level
    ├─ Groq API        → Egyptian Arabic explanation + example
    ├─ Yarn            → find a movie quote containing the expression and download its clip
    ├─ Neon Postgres   → subscriber levels + sent expressions
    ▼
Telegram Bot API       → send each level’s clip to its subscribers
```

New users subscribe with `/start` and pick a level. `/level` changes it at any time, `/today` shows the latest expression for that level, and `/stop` unsubscribes. Existing subscribers default to A2 and keep their subscription. CEFR labels are approximate, and the curated bank rotates topics and avoids repeats until exhausted.

## Stack

| Tool | Role |
| --- | --- |
| cron-job.org | Every 3 hours (HTTP POST) |
| GitHub Actions | Free ephemeral worker |
| Python + python-telegram-bot | The bot |
| Neon (Postgres) | Database |
| Yarn | Movie quote search and short clips |
| Groq API (`qwen/qwen3.8-27b`) | Explanations and examples |

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
handles `/start`, `/level`, `/stop`, `/help`, `/today` and talks to Neon over TLS. The webhook and the scheduled job apply the additive level/history migration automatically.

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

```bash
pip install -r requirements.txt
python daily_job.py  # sends one expression to each active level group
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
phrases.py           # CEFR-labelled expressions and topics
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
