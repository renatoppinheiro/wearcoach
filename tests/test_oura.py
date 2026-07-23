"""Unit tests for coach.oura. All requests calls are mocked — no network."""
from __future__ import annotations

import json
import time

import pytest

from coach import config, oura


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
    monkeypatch.setattr(oura, "TOKEN_PATH", tmp_path / "oura.json")
    monkeypatch.setattr(config, "TOKENS_DIR", tmp_path)


def test_is_connected_false_when_no_token_file():
    assert oura.is_connected() is False


def test_save_tokens_stamps_obtained_at():
    oura._save_tokens({"access_token": "abc"})
    saved = oura._load_tokens()
    assert saved["access_token"] == "abc"
    assert "_obtained_at" in saved


def test_access_token_returns_cached_when_not_expired():
    oura._save_tokens({"access_token": "cached", "expires_in": 3600})
    assert oura._access_token() == "cached"


def test_access_token_raises_when_not_connected():
    with pytest.raises(SystemExit, match="not connected"):
        oura._access_token()


def test_access_token_refreshes_when_expired(monkeypatch):
    tokens = {"access_token": "stale", "refresh_token": "r1", "expires_in": 100}
    tokens["_obtained_at"] = time.time() - 1000  # long expired
    oura.TOKEN_PATH.write_text(json.dumps(tokens), encoding="utf-8")

    fresh = {"access_token": "fresh", "refresh_token": "r2", "expires_in": 3600}
    monkeypatch.setattr(oura.requests, "post", lambda *a, **kw: FakeResponse(fresh))

    token = oura._access_token()

    assert token == "fresh"
    assert oura._load_tokens()["refresh_token"] == "r2"


def test_fetch_recent_wellness_merges_by_date(monkeypatch):
    monkeypatch.setattr(oura, "_access_token", lambda: "tok")

    def fake_get(endpoint, token, start, end):
        return {
            "daily_sleep": [{"day": "2026-07-20", "score": 82}],
            "daily_readiness": [
                {
                    "day": "2026-07-20",
                    "score": 90,
                    "contributors": {"hrv_balance": 70, "resting_heart_rate": 85},
                }
            ],
            "daily_activity": [{"day": "2026-07-20", "score": 75, "steps": 8000}],
        }[endpoint]

    monkeypatch.setattr(oura, "_get", fake_get)

    result = oura.fetch_recent_wellness(days=1)

    assert result == [
        {
            "date": "2026-07-20",
            "sleep_score": 82,
            "readiness_score": 90,
            "hrv_balance_contrib": 70,
            "resting_hr_contrib": 85,
            "activity_score": 75,
            "steps": 8000,
        }
    ]


def test_fetch_recent_wellness_sorted_and_partial_days(monkeypatch):
    monkeypatch.setattr(oura, "_access_token", lambda: "tok")

    def fake_get(endpoint, token, start, end):
        if endpoint == "daily_sleep":
            return [{"day": "2026-07-21", "score": 60}, {"day": "2026-07-19", "score": 70}]
        return []

    monkeypatch.setattr(oura, "_get", fake_get)

    result = oura.fetch_recent_wellness(days=3)

    assert [d["date"] for d in result] == ["2026-07-19", "2026-07-21"]
