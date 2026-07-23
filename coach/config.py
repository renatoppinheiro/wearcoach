"""Env + local paths. All tokens/data stay under DATA_DIR, gitignored."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
DATA_DIR = ROOT / "data"
TOKENS_DIR = DATA_DIR / "tokens"

load_dotenv(ENV_PATH)


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def require_env(*keys: str) -> list[str]:
    """Return keys that are missing/empty."""
    return [k for k in keys if not env(k)]


def ensure_dirs() -> None:
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)


def set_env_value(key: str, value: str) -> None:
    """Write/update a single key in .env, preserving the rest of the file."""
    ensure_dirs()
    if not ENV_PATH.exists():
        example = ROOT / ".env.example"
        ENV_PATH.write_text(example.read_text(encoding="utf-8") if example.exists() else "", encoding="utf-8")

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    out, found = [], False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    os.environ[key] = value
