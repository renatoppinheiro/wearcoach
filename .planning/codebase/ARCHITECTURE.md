# Architecture Overview

**Last Updated:** 2026-07-22

## System Architecture Pattern

`wearcoach` uses a decoupled, modular design dividing responsibilities into data fetching, credential management, prompt building, and intelligence dispatch.

```
┌─────────────────────────────────────────────────────────────────┐
│                          User Interface                         │
│   CLI: `python main.py [setup|fetch|brief]`  OR  Coding Agent  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Command Dispatcher                         │
│                           `main.py`                             │
└───────────────┬─────────────────┬─────────────────┬─────────────┘
                │                 │                 │
                ▼                 ▼                 ▼
  ┌───────────────────┐  ┌──────────────────┐  ┌──────────────────┐
  │   Strava Module   │  │   Oura Module    │  │  Garmin Module   │
  │ `coach/strava.py` │  │ `coach/oura.py`  │  │`coach/garmin.py` │
  └─────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ Snapshot JSON Generator  │
                     │ `data/snapshot-*.json`   │
                     └────────────┬─────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
                 ▼                                 ▼
┌─────────────────────────────────┐   ┌──────────────────────────┐
│        Coding Agent Mode        │   │   Standalone CLI Mode    │
│ Reads snapshot + `.wiki/` memory│   │  `coach/prompt.py` +     │
│ Enforces `CLAUDE.md` rules      │   │  `coach/llm.py` API call │
└─────────────────────────────────┘   └──────────────────────────┘
```

---

## Core Modules & Layers

### 1. Control Layer (`main.py`)
- CLI entry point parsing positional commands (`setup`, `fetch`, `brief`) and `--days` flag.
- Manages setup wizard flow (`cmd_setup`) to populate credentials and test connections safely.

### 2. Data Provider Layer (`coach/strava.py`, `coach/oura.py`, `coach/garmin.py`)
- Encapsulates authentication, OAuth loopback server interaction (`coach/oauth_loopback.py`), token refresh, and HTTP requests.
- Normalizes raw API responses into structured lists of dicts containing activity and wellness parameters.

### 3. Configuration & State Layer (`coach/config.py`)
- Defines root paths (`ROOT`, `DATA_DIR`, `TOKENS_DIR`).
- Manages key-value environment reading/writing from/to `.env`.

### 4. Intelligence & Prompt Layer (`coach/prompt.py`, `coach/llm.py`)
- `coach/prompt.py`: Formats activities and wellness data into a structured system/user prompt containing coaching instructions and threshold checks.
- `coach/llm.py`: Instantiates Anthropic or OpenAI API client based on `LLM_PROVIDER` environment variable and returns response text.
