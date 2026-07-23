# wearcoach

Local AI running coach. Reads your Strava (+ optionally Oura ring or Garmin
wellness), asks Claude or GPT for a briefing. Runs entirely on your machine —
your data and API keys never go anywhere except Strava/Oura/Garmin and
whichever LLM you pick.

**Not a medical professional.** Stop on pain. You own your training decisions.

## Setup (~5 min)

1. Install Python 3.10+, then:
   ```
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. Get an LLM API key (pick one):
   - Claude: https://console.anthropic.com → API Keys
   - GPT: https://platform.openai.com → API Keys

3. Create your own Strava API app (required, free, 2 min):
   - https://www.strava.com/settings/api
   - Authorization Callback Domain: `localhost`
   - Copy the Client ID + Client Secret

4. (Optional) If you own an Oura ring, create an app:
   - https://cloud.ouraring.com/oauth/applications
   - Redirect URI: `http://localhost:8734/callback`

5. (Optional) If you have Garmin instead of Oura, just have your Garmin
   email/password ready — no app registration needed for Garmin.

6. Run the wizard:
   ```
   python main.py setup
   ```
   This walks through connecting whichever of the above you have. Strava is
   required; Oura and Garmin are both optional (pick at most one — if both
   are connected, Oura wins).

7. Get your briefing:
   ```
   python main.py brief
   ```

## Commands

- `python main.py setup` — connect accounts, pick LLM (run once)
- `python main.py fetch` — pull recent data only, save to `data/`
- `python main.py brief` — fetch + ask your coach + print/save the briefing

## Why Oura instead of Garmin for wellness?

Garmin has no self-serve developer API for personal wellness data — the only
path is an unofficial library that logs in with your real Garmin password.
It works (this repo supports it), but if you own an Oura ring, its official
OAuth2 app path is safer and is what we recommend.

## Optional: talk to your coach with a persistent memory

`python main.py brief` is stateless — one snapshot in, one briefing out. If
you want an actual back-and-forth with your coach that remembers your goals,
injuries, and races across sessions, this repo also ships an **LLM wiki**
([Karpathy's pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)):
a folder of markdown the LLM reads and writes itself, so it compounds instead
of forgetting everything between chats.

How to use it:

1. Install [Claude Code](https://claude.com/claude-code) (or use any LLM tool
   that can read/write files in a folder).
2. Run `python main.py fetch` first, so there's a fresh `data/snapshot-*.json`
   to talk about.
3. `cd` into this repo and start a session (e.g. run `claude`).
4. Just talk to it — "how's my training going", "I tweaked my knee last week",
   "plan my next 3 weeks". `CLAUDE.md` at the repo root tells the LLM to read
   `wiki/index.md` first and file anything durable back into `wiki/entities/`
   or `wiki/concepts/`, citing the `data/` file it came from.
5. Over time `wiki/` becomes your own running history and rulebook — race
   times, what wrecked your last taper, your actual HRV baseline — without
   you writing any of it by hand.

This part is 100% optional and separate from `brief`/`fetch` — skip it if you
just want the one-shot daily briefing.

## Privacy

- `.env` (your keys/secrets) and `data/` (your fetched data + tokens) are
  gitignored — never commit them.
- Garmin credentials go directly to Garmin's login via the `garminconnect`
  library; nothing else sees them.
- Nothing is uploaded to any server this project controls — there is no
  backend, no hosting, no telemetry.
