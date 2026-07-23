"""Strava OAuth (self-serve app, read-only scope) + recent activity fetch."""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from . import config

AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
REDIRECT_PORT = 8721
TOKEN_PATH = config.TOKENS_DIR / "strava.json"


def connect() -> None:
    """Interactive one-time OAuth grant. Requires STRAVA_CLIENT_ID/SECRET in .env."""
    from .oauth_loopback import capture_code

    missing = config.require_env("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET")
    if missing:
        raise SystemExit(
            f"Missing {', '.join(missing)}. Create an app at "
            "https://www.strava.com/settings/api (Authorization Callback Domain: localhost) "
            "and set them in .env first."
        )

    client_id = config.env("STRAVA_CLIENT_ID")
    client_secret = config.env("STRAVA_CLIENT_SECRET")
    redirect_uri = f"http://localhost:{REDIRECT_PORT}/callback"

    authorize_url = (
        f"{AUTH_URL}?client_id={client_id}&redirect_uri={redirect_uri}"
        "&response_type=code&scope=read,activity:read_all&approval_prompt=auto"
    )
    code = capture_code(authorize_url, REDIRECT_PORT)

    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    resp.raise_for_status()
    _save_tokens(resp.json())
    print("Strava connected.")


def _save_tokens(payload: dict) -> None:
    config.ensure_dirs()
    TOKEN_PATH.write_text(json.dumps(payload), encoding="utf-8")


def _load_tokens() -> dict | None:
    if not TOKEN_PATH.exists():
        return None
    return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))


def _access_token() -> str:
    tokens = _load_tokens()
    if not tokens:
        raise SystemExit("Strava not connected. Run: python main.py setup")

    if tokens.get("expires_at", 0) > time.time() + 60:
        return tokens["access_token"]

    # Refresh — Strava rotates the refresh token on every use, must persist the new one.
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": config.env("STRAVA_CLIENT_ID"),
            "client_secret": config.env("STRAVA_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        },
        timeout=30,
    )
    resp.raise_for_status()
    fresh = resp.json()
    _save_tokens(fresh)
    return fresh["access_token"]


def is_connected() -> bool:
    return _load_tokens() is not None


def fetch_recent_activities(days: int = 7) -> list[dict]:
    """Return recent activities, trimmed to the fields the coach prompt needs."""
    token = _access_token()
    after = int(time.time()) - days * 86400
    resp = requests.get(
        ACTIVITIES_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"after": after, "per_page": 50},
        timeout=30,
    )
    resp.raise_for_status()
    activities = resp.json()

    return [
        {
            "date": a.get("start_date_local", "")[:10],
            "name": a.get("name"),
            "type": a.get("type"),
            "distance_km": round(a.get("distance", 0) / 1000, 2),
            "moving_time_min": round(a.get("moving_time", 0) / 60),
            "avg_hr": a.get("average_heartrate"),
            "max_hr": a.get("max_heartrate"),
            "avg_pace_min_per_km": (
                round((a["moving_time"] / 60) / (a["distance"] / 1000), 2)
                if a.get("distance") and a.get("moving_time")
                else None
            ),
            "elevation_gain_m": a.get("total_elevation_gain"),
            "perceived_exertion": a.get("perceived_exertion"),
        }
        for a in activities
    ]
