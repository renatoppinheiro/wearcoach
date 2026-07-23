# Technology Stack

**Last Updated:** 2026-07-22

## Core Technologies
- **Language:** Python 3.10+ (enforced in `main.py` via `sys.version_info < (3, 10)` check)
- **Runtime:** Standard CPython 3.10+
- **Execution Model:** Local CLI tool (`main.py`) and optional Coding Agent driven workflow (`CLAUDE.md`)

## Key Dependencies & Libraries
- **HTTP Client:** `requests>=2.31` (`requirements.txt`) — used for API communication with Strava and Oura endpoints
- **Environment Management:** `python-dotenv>=1.0` (`requirements.txt`) — parses and loads environment variables from `.env`
- **Garmin API:** `garminconnect>=0.2.19` (`requirements.txt`) — Python client wrapper for Garmin Connect services
- **LLM SDKs:**
  - `anthropic>=0.40` (`requirements.txt`) — Anthropic Python client for Claude models
  - `openai>=1.50` (`requirements.txt`) — OpenAI Python client for GPT models

## Testing & Tooling
- **Test Runner:** `pytest` (`pytest.ini`, `requirements-dev.txt`)
- **Testing Standard:** Unit test suite in `tests/` leveraging `unittest.mock` to mock network responses and OAuth flows.

## Configuration & Persistence
- `.env` / `.env.example`: Environment configuration for Client IDs, Secrets, and API Keys.
- `data/`: Local json snapshots (`data/snapshot-YYYY-MM-DD.json`), daily briefings (`data/briefing-YYYY-MM-DD.md`), and OAuth token cache (`data/tokens/`).
- `.wiki/`: Knowledge graph and memory bank driven by `llm-wiki` protocol for persistent cross-session athletic coaching memory.
