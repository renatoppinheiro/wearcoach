"""Unit tests for coach.prompt.build — pure function, no network."""
from __future__ import annotations

import json

from coach import prompt


def test_build_includes_activities_and_wellness():
    activities = [{"date": "2026-07-20", "name": "Easy run", "distance_km": 8.0}]
    wellness = [{"date": "2026-07-20", "sleep_score": 82}]

    text = prompt.build(activities, wellness, "oura")

    assert "## Recent activities" in text
    assert "## Wellness (oura)" in text
    assert json.dumps(activities, indent=2, ensure_ascii=False) in text
    assert json.dumps(wellness, indent=2, ensure_ascii=False) in text


def test_build_no_activities_synced():
    text = prompt.build([], [{"date": "2026-07-20"}], "garmin")
    assert "(none synced)" in text


def test_build_no_wellness_source_mentions_asking_athlete():
    text = prompt.build([{"date": "2026-07-20", "name": "Run"}], [], None)
    assert "No wearable wellness connected" in text
    assert "## Wellness (" not in text


def test_build_wellness_source_but_empty_days():
    text = prompt.build([], [], "oura")
    assert "## Wellness (oura)" in text
    assert "(no data yet)" in text
