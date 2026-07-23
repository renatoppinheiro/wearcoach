# wearcoach

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Local only](https://img.shields.io/badge/hosting-none%2C%20fully%20local-brightgreen)

Local AI running coach. Reads your Strava (+ optionally Oura ring or Garmin
wellness) and turns it into a daily briefing. Runs entirely on your machine —
your data never goes anywhere except Strava/Oura/Garmin and whichever LLM
you use to talk to it.

**Not a medical professional.** Stop on pain. You own your training decisions.

Two ways to use it — pick one:

- **Recommended: your own coding agent** (Claude Code, Cursor, Windsurf,
  Copilot, ...). The scripts here only fetch data; the agent reads
  `CLAUDE.md` and does the actual coaching. No LLM API key needed — you use
  whatever you already pay for / have installed.
- **Standalone fallback**: `python main.py brief` calls Claude or GPT
  directly with your own API key. Use this if you don't have a coding agent.

## Setup (~5 min)

1. Install Python 3.10+, then:
   ```
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. Create your own Strava API app (required, free, 2 min):
   - https://www.strava.com/settings/api
   - Authorization Callback Domain: `localhost`
   - Copy the Client ID + Client Secret

3. (Optional) If you own an Oura ring, create an app:
   - https://cloud.ouraring.com/oauth/applications
   - Redirect URI: `http://localhost:8734/callback`

4. (Optional) If you have Garmin instead of Oura, just have your Garmin
   email/password ready — no app registration needed for Garmin.

5. Run the wizard:
   ```
   python main.py setup
   ```
   It'll ask if you're using a coding agent (skips the LLM key step if so),
   then walks through connecting Strava (required) and Oura/Garmin
   (optional — pick at most one; if both are connected, Oura wins).

## How to use it: your own coding agent (recommended)

1. `python main.py fetch` — pulls recent activities + wellness into `data/`.
2. Open this folder in Claude Code (`claude`), Cursor, Windsurf, or any agent
   that can read files and run shell commands.
3. Just ask: *"give me today's briefing"*. `CLAUDE.md` tells it exactly what
   to read and which thresholds matter — it'll run `fetch` itself if needed.
4. Keep talking to it like a coach — "I tweaked my knee last week", "plan my
   next 3 weeks", "how's my training going". It files anything durable back
   into `wiki/entities/` or `wiki/concepts/` (the
   [Karpathy LLM-wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)),
   so it remembers your goals, injuries, and races across sessions instead of
   starting fresh every time.

Over time `wiki/` becomes your own running history and rulebook — race
times, what wrecked your last taper, your actual HRV baseline — without you
writing any of it by hand.

## How to use it: standalone (no coding agent)

```
python main.py fetch                # pull recent data only, save to data/
python main.py brief                 # fetch + ask your coach + print/save the briefing
python main.py fetch --days 14       # pull more history (default 7, max 60)
```

This mode is stateless (one snapshot in, one briefing out, no wiki memory)
and needs `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`:
- Claude: https://console.anthropic.com → API Keys
- GPT: https://platform.openai.com → API Keys

## Commands

| Command | What it does |
|---|---|
| `python main.py setup` | Interactive wizard: pick coach mode, connect Strava/Oura/Garmin |
| `python main.py fetch [--days N]` | Pull recent activities + wellness into `data/` |
| `python main.py brief [--days N]` | `fetch`, then ask the built-in LLM for a briefing (standalone mode) |
| `python main.py --help` | Full command reference |

## Why Oura instead of Garmin for wellness?

Garmin has no self-serve developer API for personal wellness data — the only
path is an unofficial library that logs in with your real Garmin password.
It works (this repo supports it), but if you own an Oura ring, its official
OAuth2 app path is safer and is what we recommend.

## Privacy

- `.env` (your keys/secrets) and `data/` (your fetched data + tokens) are
  gitignored — never commit them.
- Garmin credentials go directly to Garmin's login via the `garminconnect`
  library; nothing else sees them.
- Nothing is uploaded to any server this project controls — there is no
  backend, no hosting, no telemetry.
