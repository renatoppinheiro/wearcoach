"""Garmin Connect auth + wellness fetch.

Same login pattern as stravator's scripts/garmin_auth.py: email/password go
straight to Garmin's own login via the `garminconnect`/`garth` libraries and
are never sent anywhere else. Tokens are cached locally so MFA only prompts
once. Garmin has no self-serve OAuth app (unlike Strava/Oura) — this is the
unofficial-but-widely-used path; only use your own account.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
)

from . import config


def _prompt_mfa() -> str:
    return input("Garmin MFA code: ").strip()


def _authenticate() -> Garmin:
    config.ensure_dirs()
    email = config.env("GARMIN_EMAIL")
    password = config.env("GARMIN_PASSWORD")
    if not email or not password:
        raise SystemExit("Set GARMIN_EMAIL and GARMIN_PASSWORD in .env first.")

    token_dir = config.TOKENS_DIR / "garmin"
    token_dir.mkdir(parents=True, exist_ok=True)

    api = Garmin(email=email, password=password, is_cn=False, prompt_mfa=_prompt_mfa)
    try:
        api.login(str(token_dir))
    except (FileNotFoundError, GarminConnectAuthenticationError):
        api.login()
        api.garth.dump(str(token_dir))
    return api


def connect() -> None:
    """Just proves the login works once (also caches the token)."""
    try:
        _authenticate()
    except GarminConnectAuthenticationError as e:
        raise SystemExit(f"Garmin auth failed: {e}")
    except GarminConnectConnectionError as e:
        raise SystemExit(f"Garmin connection failed: {e}")
    print("Garmin connected.")


def is_connected() -> bool:
    return bool(config.env("GARMIN_EMAIL") and config.env("GARMIN_PASSWORD"))


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:  # noqa: BLE001 — Garmin payloads vary, one bad field shouldn't kill the pull
        print(f"  {getattr(fn, '__name__', fn)}: {e}", file=sys.stderr)
        return None


def _day_slice(api: Garmin, target: str) -> dict:
    entry: dict = {"date": target}

    sleep_raw = _safe(api.get_sleep_data, target) or {}
    daily = sleep_raw.get("dailySleepDTO") or {}
    if daily.get("sleepTimeSeconds"):
        entry["sleep_duration_min"] = round(daily["sleepTimeSeconds"] / 60)
        scores = daily.get("sleepScores") or {}
        entry["sleep_score"] = (scores.get("overall") or {}).get("value")
        hrv_vals = [
            h.get("value") for h in (sleep_raw.get("hrvData") or [])
            if isinstance(h.get("value"), (int, float))
        ]
        if hrv_vals:
            entry["sleep_hrv_overnight_avg_ms"] = round(sum(hrv_vals) / len(hrv_vals), 1)

    tr = _safe(api.get_training_readiness, target)
    if isinstance(tr, list):
        tr = tr[0] if tr else None
    if isinstance(tr, dict):
        entry["training_readiness_score"] = tr.get("score")
        entry["training_readiness_level"] = tr.get("level")

    ts = _safe(api.get_training_status, target) or {}
    status_section = (ts.get("mostRecentTrainingStatus") or {}).get("latestTrainingStatusData") or {}
    device_status = next(iter(status_section.values()), {}) if isinstance(status_section, dict) else {}
    acute = device_status.get("acuteTrainingLoadDTO") or {}
    if acute.get("dailyAcuteChronicWorkloadRatio") is not None:
        entry["training_load_acwr"] = acute.get("dailyAcuteChronicWorkloadRatio")
        entry["training_load_acwr_status"] = acute.get("acwrStatus")

    bb = _safe(api.get_body_battery, target, target)
    bb_entry = bb[0] if isinstance(bb, list) and bb else (bb if isinstance(bb, dict) else {})
    if bb_entry:
        entry["body_battery_high"] = bb_entry.get("highestValue")
        entry["body_battery_low"] = bb_entry.get("lowestValue")

    hrv = _safe(api.get_hrv_data, target) or {}
    summary = (hrv.get("hrvSummary") or {})
    if summary.get("status"):
        entry["hrv_status"] = summary.get("status")

    return entry


def fetch_recent_wellness(days: int = 7) -> list[dict]:
    api = _authenticate()
    out = []
    today = date.today()
    for i in range(days):
        target = (today - timedelta(days=i)).isoformat()
        entry = _day_slice(api, target)
        if len(entry) > 1:  # more than just "date"
            out.append(entry)
    return sorted(out, key=lambda e: e["date"])
