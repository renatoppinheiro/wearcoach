"""Oura OAuth2 (self-serve app, Dec-2025 PAT deprecation means OAuth2 is the
only path for new connections) + daily sleep/readiness/activity fetch."""
from __future__ import annotations

import json
import time
from datetime import date, timedelta

import requests

from . import config

AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
API_BASE = "https://api.ouraring.com/v2/usercollection"
REDIRECT_PORT = 8734
TOKEN_PATH = config.TOKENS_DIR / "oura.json"


def connect() -> None:
    from .oauth_loopback import capture_code

    missing = config.require_env("OURA_CLIENT_ID", "OURA_CLIENT_SECRET")
    if missing:
        raise SystemExit(
            f"Missing {', '.join(missing)}. Create an app at "
            "https://cloud.ouraring.com/oauth/applications "
            f"(redirect URI: http://localhost:{REDIRECT_PORT}/callback) and set them in .env."
        )

    client_id = config.env("OURA_CLIENT_ID")
    client_secret = config.env("OURA_CLIENT_SECRET")
    redirect_uri = f"http://localhost:{REDIRECT_PORT}/callback"

    authorize_url = (
        f"{AUTH_URL}?response_type=code&client_id={client_id}"
        f"&redirect_uri={redirect_uri}&scope=daily+heartrate"
    )
    code = capture_code(authorize_url, REDIRECT_PORT)

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    resp.raise_for_status()
    _save_tokens(resp.json())
    print("Oura connected.")


def _save_tokens(payload: dict) -> None:
    config.ensure_dirs()
    payload["_obtained_at"] = time.time()
    TOKEN_PATH.write_text(json.dumps(payload), encoding="utf-8")


def _load_tokens() -> dict | None:
    if not TOKEN_PATH.exists():
        return None
    return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))


def is_connected() -> bool:
    return _load_tokens() is not None


def _access_token() -> str:
    tokens = _load_tokens()
    if not tokens:
        raise SystemExit("Oura not connected. Run: python main.py setup")

    obtained_at = tokens.get("_obtained_at", 0)
    expires_in = tokens.get("expires_in", 0)
    if obtained_at + expires_in > time.time() + 60:
        return tokens["access_token"]

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": config.env("OURA_CLIENT_ID"),
            "client_secret": config.env("OURA_CLIENT_SECRET"),
        },
        timeout=30,
    )
    resp.raise_for_status()
    fresh = resp.json()
    _save_tokens(fresh)
    return fresh["access_token"]


def _get(endpoint: str, token: str, start: str, end: str) -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        params={"start_date": start, "end_date": end},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def fetch_recent_wellness(days: int = 7) -> list[dict]:
    """Return per-day dicts merging sleep + readiness, keyed by date."""
    token = _access_token()
    end = date.today() + timedelta(days=1)  # end_date is exclusive in Oura's API
    start = date.today() - timedelta(days=days)
    start_s, end_s = start.isoformat(), end.isoformat()

    by_date: dict[str, dict] = {}

    for s in _get("daily_sleep", token, start_s, end_s):
        d = by_date.setdefault(s["day"], {"date": s["day"]})
        d["sleep_score"] = s.get("score")

    for r in _get("daily_readiness", token, start_s, end_s):
        d = by_date.setdefault(r["day"], {"date": r["day"]})
        d["readiness_score"] = r.get("score")
        contrib = r.get("contributors", {})
        d["hrv_balance_contrib"] = contrib.get("hrv_balance")
        d["resting_hr_contrib"] = contrib.get("resting_heart_rate")

    for a in _get("daily_activity", token, start_s, end_s):
        d = by_date.setdefault(a["day"], {"date": a["day"]})
        d["activity_score"] = a.get("score")
        d["steps"] = a.get("steps")

    return sorted(by_date.values(), key=lambda x: x["date"])
