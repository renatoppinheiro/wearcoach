"""Unit tests for FastAPI server endpoints in coach/server.py."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from coach.server import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_list_snapshots_empty(tmp_path: Path) -> None:
    with patch("coach.config.DATA_DIR", tmp_path):
        response = client.get("/api/snapshots")
        assert response.status_code == 200
        assert response.json() == {"snapshots": []}


def test_list_snapshots_with_files(tmp_path: Path) -> None:
    (tmp_path / "snapshot-2026-07-20.json").write_text("{}", encoding="utf-8")
    (tmp_path / "snapshot-2026-07-22.json").write_text("{}", encoding="utf-8")

    with patch("coach.config.DATA_DIR", tmp_path):
        response = client.get("/api/snapshots")
        assert response.status_code == 200
        snapshots = response.json()["snapshots"]
        assert snapshots == ["2026-07-22", "2026-07-20"]


def test_get_latest_snapshot_not_found(tmp_path: Path) -> None:
    with patch("coach.config.DATA_DIR", tmp_path):
        response = client.get("/api/snapshots/latest")
        assert response.status_code == 404
        assert "No snapshots found" in response.json()["detail"]


def test_get_latest_snapshot_success(tmp_path: Path) -> None:
    sample_data = {"activities": [{"id": 1, "name": "Morning Run"}], "wellness": [], "wellness_source": None}
    (tmp_path / "snapshot-2026-07-22.json").write_text(json.dumps(sample_data), encoding="utf-8")

    with patch("coach.config.DATA_DIR", tmp_path):
        response = client.get("/api/snapshots/latest")
        assert response.status_code == 200
        assert response.json() == sample_data


def test_get_snapshot_by_date(tmp_path: Path) -> None:
    sample_data = {"activities": [], "wellness": [], "wellness_source": "oura"}
    (tmp_path / "snapshot-2026-07-21.json").write_text(json.dumps(sample_data), encoding="utf-8")

    with patch("coach.config.DATA_DIR", tmp_path):
        # Found
        res_ok = client.get("/api/snapshots/2026-07-21")
        assert res_ok.status_code == 200
        assert res_ok.json() == sample_data

        # Not found
        res_404 = client.get("/api/snapshots/2026-07-20")
        assert res_404.status_code == 404


def test_fetch_endpoint_not_connected() -> None:
    with patch("coach.strava.is_connected", return_value=False):
        response = client.post("/api/fetch", json={"days": 7})
        assert response.status_code == 400
        assert "Strava not connected" in response.json()["detail"]


def test_fetch_endpoint_success(tmp_path: Path) -> None:
    with (
        patch("coach.strava.is_connected", return_value=True),
        patch("coach.strava.fetch_recent_activities", return_value=[{"id": 100}]),
        patch("coach.oura.is_connected", return_value=True),
        patch("coach.oura.fetch_recent_wellness", return_value=[{"score": 85}]),
        patch("coach.config.DATA_DIR", tmp_path),
    ):
        response = client.post("/api/fetch", json={"days": 7})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["activities_count"] == 1
        assert data["wellness_count"] == 1
        assert data["wellness_source"] == "oura"


def test_chat_endpoint_plain_text(tmp_path: Path) -> None:
    with (
        patch("coach.llm.ask", return_value="Great job today! Keep going."),
        patch("coach.config.DATA_DIR", tmp_path),
    ):
        response = client.post("/api/chat", json={"message": "How should I train?"})
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Great job today! Keep going."
        assert data["chart"] is None


def test_chat_endpoint_with_chart_block(tmp_path: Path) -> None:
    llm_output = (
        "Here is your weekly volume trend:\n\n"
        "```chart\n"
        '{"type": "line", "data": [{"day": "Mon", "km": 5}, {"day": "Tue", "km": 10}]}\n'
        "```\n\n"
        "Take it easy tomorrow."
    )
    with (
        patch("coach.llm.ask", return_value=llm_output),
        patch("coach.config.DATA_DIR", tmp_path),
    ):
        response = client.post("/api/chat", json={"message": "Show volume chart"})
        assert response.status_code == 200
        data = response.json()
        assert "Here is your weekly volume trend:" in data["reply"]
        assert "Take it easy tomorrow." in data["reply"]
        assert data["chart"] == {"type": "line", "data": [{"day": "Mon", "km": 5}, {"day": "Tue", "km": 10}]}

