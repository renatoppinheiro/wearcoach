# Directory & Code Structure

**Last Updated:** 2026-07-22

## Repository Layout

```
wearcoach/
├── main.py                 # CLI entry point (commands: setup, fetch, brief)
├── requirements.txt        # Core dependencies (requests, garminconnect, etc.)
├── requirements-dev.txt    # Development dependencies (pytest)
├── pytest.ini              # Pytest configuration file
├── CLAUDE.md               # System prompt & rules for coding agents
├── README.md               # Documentation (English & Portuguese)
├── LICENSE                 # MIT License
├── .env.example            # Template environment variables file
├── coach/                  # Core package modules
│   ├── __init__.py         # Package initialization
│   ├── config.py           # Path constants and .env file manager
│   ├── garmin.py           # Garmin Connect authentication & data fetcher
│   ├── llm.py              # Provider-agnostic LLM client (Anthropic / OpenAI)
│   ├── oauth_loopback.py   # Temporary HTTP loopback server for OAuth redirect
│   ├── oura.py             # Oura Ring OAuth & wellness data fetcher
│   ├── prompt.py           # Coaching briefing prompt formatter
│   └── strava.py           # Strava OAuth & activity data fetcher
├── tests/                  # Unit test directory
│   ├── test_config.py      # Tests for config helper functions
│   ├── test_garmin.py      # Mocked tests for Garmin integration
│   ├── test_llm.py         # Mocked tests for Anthropic and OpenAI calls
│   ├── test_main.py        # Integration & CLI entry point tests
│   ├── test_oura.py        # Mocked tests for Oura OAuth and fetching
│   ├── test_prompt.py      # Tests for prompt string generation
│   └── test_strava.py      # Mocked tests for Strava OAuth and fetching
└── data/                   # Dynamic data folder (gitignored)
    ├── snapshot-*.json     # Daily activity & wellness snapshot data
    ├── briefing-*.md       # Generated briefing output files
    └── tokens/             # Stored authentication tokens for API providers
```

## Key Files & Responsibilities

| File Path | Description |
| :--- | :--- |
| `main.py` | Orchestrates interactive setup, data fetching, and brief commands |
| `coach/config.py` | Provides `ROOT`, `DATA_DIR`, `TOKENS_DIR`, and `.env` reader/writer helpers |
| `coach/oauth_loopback.py` | Runs `http.server.HTTPServer` on port 8734 to receive OAuth callbacks |
| `coach/strava.py` | Strava OAuth setup, token refresh, and activity fetching |
| `coach/oura.py` | Oura Ring OAuth setup, token refresh, and wellness metrics retrieval |
| `coach/garmin.py` | Garmin Connect authentication and metrics (readiness, HRV, body battery) |
| `coach/prompt.py` | Builds structured coaching prompt for LLM consumption |
| `coach/llm.py` | Wraps `anthropic` and `openai` Python SDK calls |
