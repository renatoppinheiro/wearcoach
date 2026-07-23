# External Integrations

**Last Updated:** 2026-07-22

## Overview
`wearcoach` integrates with multiple fitness data providers, LLM API backends, and local persistent memory protocols.

---

## 1. Fitness & Wearable Providers

### Strava (`coach/strava.py`, `coach/oauth_loopback.py`)
- **Purpose:** Fetches recent running and cross-training activity history.
- **Auth Flow:** OAuth2 Authorization Code flow. Uses a temporary local HTTP server (`coach/oauth_loopback.py`, default port `8734`) to capture the callback code.
- **Endpoints:**
  - Token exchange: `https://www.strava.com/oauth/token`
  - Activities: `https://www.strava.com/api/v3/athlete/activities`
- **Token Cache:** Saved to `data/tokens/strava.json` with automatic refresh on token expiry.

### Oura Ring (`coach/oura.py`)
- **Purpose:** Fetches daily readiness, sleep scores, sleep duration, HRV balance, and stress metrics.
- **Auth Flow:** OAuth2 Authorization Code flow (uses `coach/oauth_loopback.py` loopback server on port `8734`).
- **Endpoints:**
  - `https://api.ouraring.com/v2/usercollection/daily_readiness`
  - `https://api.ouraring.com/v2/usercollection/daily_sleep`
  - `https://api.ouraring.com/v2/usercollection/daily_activity`
  - `https://api.ouraring.com/v2/usercollection/daily_spo2`
  - `https://api.ouraring.com/v2/usercollection/daily_stress`
- **Token Cache:** Saved to `data/tokens/oura.json`.

### Garmin Connect (`coach/garmin.py`)
- **Purpose:** Fetches Garmin training readiness, HRV status, body battery, sleep metrics, and ACWR (Acute:Chronic Workload Ratio).
- **Auth Flow:** Credential-based authentication (email & password) via the `garminconnect` Python library.
- **Session Cache:** Tokens stored in `data/tokens/garmin/` to avoid repeated re-authentications.

---

## 2. LLM Service Backends (`coach/llm.py`)

### Anthropic Claude
- **API Key:** `ANTHROPIC_API_KEY`
- **Default Model:** `claude-3-7-sonnet-latest` (or `claude-3-5-sonnet-latest`)
- **Usage:** Used when `LLM_PROVIDER=anthropic` in standalone CLI mode (`python main.py brief`).

### OpenAI GPT
- **API Key:** `OPENAI_API_KEY`
- **Default Model:** `gpt-4o`
- **Usage:** Used when `LLM_PROVIDER=openai` in standalone CLI mode.

---

## 3. Agent & Knowledge Base Integration

### Coding Agent Integration (`CLAUDE.md`)
- Supported agents: Claude Code, Cursor, Windsurf, Copilot, etc.
- In Agent mode, the LLM API key is bypassed; the interactive coding agent reads `CLAUDE.md`, consumes `data/snapshot-YYYY-MM-DD.json`, and acts as the brain.

### LLM Wiki Knowledge Base (`.wiki/`)
- Implements Karpathy's LLM-wiki design pattern via `llm-wiki` plugin (`AGENTS.md`).
- Persists long-term athlete notes, injury history, race targets, and recovery baselines across coaching sessions.
