# Coding Conventions & Patterns

**Last Updated:** 2026-07-22

## Python Style & Language Standards

- **Python Version Target:** Python 3.10+ modern syntax (union types `X | Y`, built-in generics `list[dict]`, `from __future__ import annotations`).
- **Code Style:** Clean standard Python conforming to PEP 8 standards.
- **File Encoding:** Always specify `encoding="utf-8"` explicitly for all file read/write operations to maintain cross-platform compatibility (especially on Windows).

## Naming Conventions

- **Functions & Variables:** `snake_case` (e.g., `cmd_fetch`, `fetch_recent_activities`, `wellness_source`).
- **Private/Internal Helpers:** Prefixed with a single leading underscore (e.g., `_step`, `_confirm`, `_run_step`, `_build_parser`).
- **Constants:** `ALL_CAPS_SNAKE_CASE` (e.g., `ROOT`, `DATA_DIR`, `TOKENS_DIR`, `DEFAULT_PORT`).

## Error Handling & UX Patterns

- **CLI Error Handling:** Use `SystemExit("User readable message")` for operational errors (missing configuration, missing Strava authorization, invalid parameter ranges).
- **Graceful Failure in Wizard:** The setup wizard (`main.py:cmd_setup`) uses `_run_step()` to catch account connection exceptions gracefully, allowing user setup to continue even if one optional integration fails.
- **Top-Level CLI Catch:** `main.py:main()` catches top-level `Exception` to display clean user-facing messages rather than dumping unhandled Python tracebacks.
- **Windows Terminal Encoding Guard:** `main.py` explicitly wraps `sys.stdout` with a UTF-8 `TextIOWrapper` when running on Windows to prevent `UnicodeEncodeError` on em-dashes and special symbols.

## State & Credentials Management

- All file paths are constructed relative to `coach/config.py:ROOT` using `pathlib.Path`.
- Direct access to `os.environ` is encapsulated within `coach/config.py` via `config.env()` and `config.set_env_value()`.
- API keys, OAuth tokens, and secrets are strictly gitignored (`.env`, `data/tokens/`).
