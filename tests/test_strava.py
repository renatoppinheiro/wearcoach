"""Unit tests for coach.strava. All requests calls are mocked — no network."""
from __future__ import annotations

import json
import time

import pytest

from coach import config, strava


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def isolate_token_path(monkeypatch, tmp_path):
    monkeypatch.setattr(strava, "TOKEN_PATH", tmp_path / "strava.json")
    monkeypatch.setattr(config, "TOKENS_DIR", tmp_path)


def test_is_connected_false_when_no_token_file():
    assert strava.is_connected() is False


def test_save_and_load_tokens_roundtrip():
    strava._save_tokens({"access_token": "abc", "expires_at": 123})
    assert strava.is_connected() is True
    assert strava._load_tokens() == {"access_token": "abc", "expires_at": 123}


def test_access_token_returns_cached_when_not_expired():
    strava._save_tokens({"access_token": "cached", "expires_at": time.time() + 3600})
    assert strava._access_token() == "cached"


def test_access_token_raises_when_not_connected():
    with pytest.raises(SystemExit, match="not connected"):
        strava._access_token()


def test_access_token_refreshes_when_expired(monkeypatch):
    strava._save_tokens(
        {"access_token": "stale", "refresh_token": "r1", "expires_at": time.time() - 10}
    )
    monkeypatch.setenv("STRAVA_CLIENT_ID", "cid")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")

    fresh = {"access_token": "fresh", "refresh_token": "r2", "expires_at": time.time() + 3600}
    monkeypatch.setattr(strava.requests, "post", lambda *a, **kw: FakeResponse(fresh))

    token = strava._access_token()

    assert token == "fresh"
    assert strava._load_tokens()["refresh_token"] == "r2"  # rotated token persisted


def test_fetch_recent_activities_trims_fields(monkeypatch):
    monkeypatch.setattr(strava, "_access_token", lambda: "tok")
    raw = [
        {
            "start_date_local": "2026-07-20T06:00:00Z",
            "name": "Easy run",
            "type": "Run",
            "distance": 8000,
            "moving_time": 2400,
            "average_heartrate": 145.0,
            "max_heartrate": 160.0,
            "total_elevation_gain": 50.0,
            "perceived_exertion": 4,
        }
    ]
    monkeypatch.setattr(strava.requests, "get", lambda *a, **kw: FakeResponse(raw))

    result = strava.fetch_recent_activities(days=7)

    assert result == [
        {
            "date": "2026-07-20",
            "name": "Easy run",
            "type": "Run",
            "distance_km": 8.0,
            "moving_time_min": 40,
            "avg_hr": 145.0,
            "max_hr": 160.0,
            "avg_pace_min_per_km": 5.0,
            "elevation_gain_m": 50.0,
            "perceived_exertion": 4,
        }
    ]


def test_fetch_recent_activities_handles_missing_distance(monkeypatch):
    monkeypatch.setattr(strava, "_access_token", lambda: "tok")
    raw = [{"start_date_local": "2026-07-20T06:00:00Z", "name": "Strength", "type": "WeightTraining"}]
    monkeypatch.setattr(strava.requests, "get", lambda *a, **kw: FakeResponse(raw))

    result = strava.fetch_recent_activities()

    assert result[0]["distance_km"] == 0
    assert result[0]["avg_pace_min_per_km"] is None
