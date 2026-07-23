"""Unit tests for coach.garmin. No real Garmin login — a fake api stub
stands in for garminconnect.Garmin."""
from __future__ import annotations

from coach import garmin


class FakeApi:
    """Stub matching the subset of garminconnect.Garmin's interface _day_slice uses."""

    def __init__(self, *, sleep=None, readiness=None, status=None, battery=None, hrv=None, raise_on=None):
        self._sleep = sleep or {}
        self._readiness = readiness
        self._status = status or {}
        self._battery = battery
        self._hrv = hrv or {}
        self._raise_on = raise_on or set()

    def _maybe_raise(self, name):
        if name in self._raise_on:
            raise RuntimeError(f"{name} boom")

    def get_sleep_data(self, target):
        self._maybe_raise("sleep")
        return self._sleep

    def get_training_readiness(self, target):
        self._maybe_raise("readiness")
        return self._readiness

    def get_training_status(self, target):
        self._maybe_raise("status")
        return self._status

    def get_body_battery(self, start, end):
        self._maybe_raise("battery")
        return self._battery

    def get_hrv_data(self, target):
        self._maybe_raise("hrv")
        return self._hrv


# --- _safe ---------------------------------------------------------------

def test_safe_returns_value_on_success():
    assert garmin._safe(lambda: 42) == 42


def test_safe_returns_none_on_exception(capsys):
    def boom():
        raise ValueError("nope")

    assert garmin._safe(boom) is None
    assert "nope" in capsys.readouterr().err


# --- _day_slice ------------------------------------------------------------

FULL_SLEEP = {
    "dailySleepDTO": {"sleepTimeSeconds": 7 * 3600, "sleepScores": {"overall": {"value": 88}}},
    "hrvData": [{"value": 40}, {"value": 44}],
}
FULL_STATUS = {
    "mostRecentTrainingStatus": {
        "latestTrainingStatusData": {
            "device1": {
                "acuteTrainingLoadDTO": {
                    "dailyAcuteChronicWorkloadRatio": 1.4,
                    "acwrStatus": "HIGH",
                }
            }
        }
    }
}


def test_day_slice_full_data():
    api = FakeApi(
        sleep=FULL_SLEEP,
        readiness=[{"score": 62, "level": "LOW"}],
        status=FULL_STATUS,
        battery=[{"highestValue": 80, "lowestValue": 20}],
        hrv={"hrvSummary": {"status": "BALANCED"}},
    )

    entry = garmin._day_slice(api, "2026-07-20")

    assert entry["date"] == "2026-07-20"
    assert entry["sleep_duration_min"] == 420
    assert entry["sleep_score"] == 88
    assert entry["sleep_hrv_overnight_avg_ms"] == 42.0
    assert entry["training_readiness_score"] == 62
    assert entry["training_readiness_level"] == "LOW"
    assert entry["training_load_acwr"] == 1.4
    assert entry["training_load_acwr_status"] == "HIGH"
    assert entry["body_battery_high"] == 80
    assert entry["body_battery_low"] == 20
    assert entry["hrv_status"] == "BALANCED"


def test_day_slice_empty_day_has_only_date():
    api = FakeApi()
    entry = garmin._day_slice(api, "2026-07-20")
    assert entry == {"date": "2026-07-20"}


def test_day_slice_no_sleep_synced_omits_sleep_fields():
    api = FakeApi(sleep={"dailySleepDTO": {}})
    entry = garmin._day_slice(api, "2026-07-20")
    assert "sleep_duration_min" not in entry
    assert "sleep_score" not in entry


def test_day_slice_one_metric_failing_does_not_kill_others():
    api = FakeApi(
        sleep=FULL_SLEEP,
        readiness=[{"score": 62, "level": "LOW"}],
        raise_on={"status", "battery"},
        hrv={"hrvSummary": {"status": "BALANCED"}},
    )

    entry = garmin._day_slice(api, "2026-07-20")

    assert entry["sleep_score"] == 88
    assert entry["training_readiness_score"] == 62
    assert entry["hrv_status"] == "BALANCED"
    assert "training_load_acwr" not in entry
    assert "body_battery_high" not in entry


# --- fetch_recent_wellness --------------------------------------------------

def test_fetch_recent_wellness_filters_empty_and_sorts(monkeypatch):
    from datetime import date

    fixed_today = date(2026, 7, 20)

    class FixedDate(date):
        @classmethod
        def today(cls):
            return fixed_today

    monkeypatch.setattr(garmin, "date", FixedDate)
    monkeypatch.setattr(garmin, "_authenticate", lambda: object())

    canned = {
        "2026-07-20": {"date": "2026-07-20", "sleep_score": 80},
        "2026-07-19": {"date": "2026-07-19"},  # only "date" key -> filtered
        "2026-07-18": {"date": "2026-07-18", "sleep_score": 70},
    }
    monkeypatch.setattr(garmin, "_day_slice", lambda api, target: canned[target])

    result = garmin.fetch_recent_wellness(days=3)

    assert [e["date"] for e in result] == ["2026-07-18", "2026-07-20"]


# --- is_connected ------------------------------------------------------------

def test_is_connected_true_when_both_set(monkeypatch):
    monkeypatch.setenv("GARMIN_EMAIL", "a@b.com")
    monkeypatch.setenv("GARMIN_PASSWORD", "pw")
    assert garmin.is_connected() is True


def test_is_connected_false_when_missing(monkeypatch):
    monkeypatch.delenv("GARMIN_EMAIL", raising=False)
    monkeypatch.delenv("GARMIN_PASSWORD", raising=False)
    assert garmin.is_connected() is False
