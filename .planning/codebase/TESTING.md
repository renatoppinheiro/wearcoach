# Testing Strategy & Structure

**Last Updated:** 2026-07-22

## Overview

The test suite in `wearcoach` provides complete coverage of all modules, CLI entry points, prompt formatting, and external integrations without requiring actual API credentials or live network requests.

---

## Test Framework & Configuration

- **Framework:** `pytest`
- **Config File:** `pytest.ini` (`testpaths = tests`)
- **Dependencies:** `pytest` (specified in `requirements-dev.txt`)

---

## Test Organization

Each module in `coach/` has a corresponding test module in `tests/`:

| Core Module | Test Module | Scope & Focus |
| :--- | :--- | :--- |
| `coach/config.py` | `tests/test_config.py` | Environment variable parsing, directory creation, `.env` file updates |
| `coach/garmin.py` | `tests/test_garmin.py` | Mocked Garmin Connect login, token caching, wellness metric extraction |
| `coach/llm.py` | `tests/test_llm.py` | Mocked Anthropic & OpenAI SDK invocations, provider selection logic |
| `main.py` | `tests/test_main.py` | CLI argument parsing (`setup`, `fetch`, `brief`), output generation, error handling |
| `coach/oura.py` | `tests/test_oura.py` | Mocked Oura OAuth flow, token refresh logic, readiness & sleep data parsing |
| `coach/prompt.py` | `tests/test_prompt.py` | Verification of generated system prompt text, thresholds, and formatted metrics |
| `coach/strava.py` | `tests/test_strava.py` | Mocked Strava OAuth loopback server interaction, token exchange, activity fetching |

---

## Execution Commands

### Running All Tests
```bash
pytest
```

### Running Tests with Verbose Output
```bash
pytest -v
```

### Running a Specific Test File
```bash
pytest tests/test_strava.py
```

---

## Mocking Strategy

- **HTTP Requests:** External endpoints (`requests.get`, `requests.post`) are mocked using `unittest.mock.patch` to return synthetic JSON payloads.
- **Local Server:** The OAuth loopback HTTP server in `coach/oauth_loopback.py` is tested using ephemeral ports or mocked socket calls.
- **FileSystem & Environment:** `monkeypatch` and `tmp_path` fixtures are used to test file generation (`data/snapshot-*.json`) and `.env` writing without affecting local user state.
