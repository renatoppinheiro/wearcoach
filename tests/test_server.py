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
