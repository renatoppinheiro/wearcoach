"""wearcoach local backend REST API server using FastAPI."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from coach import config

app = FastAPI(
    title="wearcoach API",
    description="Local backend API server for wearcoach running coach & analytics",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/snapshots")
def list_snapshots() -> dict[str, list[str]]:
    """List all available daily snapshot dates."""
    config.ensure_dirs()
    snapshot_files = sorted(config.DATA_DIR.glob("snapshot-*.json"), reverse=True)
    dates = []
    for f in snapshot_files:
        name = f.name
        # snapshot-YYYY-MM-DD.json
        if name.startswith("snapshot-") and name.endswith(".json"):
            date_str = name[len("snapshot-") : -len(".json")]
            dates.append(date_str)
    return {"snapshots": dates}


@app.get("/api/snapshots/latest")
def get_latest_snapshot() -> dict[str, Any]:
    """Get the latest available snapshot payload."""
    config.ensure_dirs()
    snapshot_files = sorted(config.DATA_DIR.glob("snapshot-*.json"), reverse=True)
    if not snapshot_files:
        raise HTTPException(status_code=404, detail="No snapshots found in data directory")
    latest_file = snapshot_files[0]
    try:
        data = json.loads(latest_file.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse snapshot JSON: {e}") from e


@app.get("/api/snapshots/{snapshot_date}")
def get_snapshot_by_date(snapshot_date: str) -> dict[str, Any]:
    """Get snapshot payload for a specific date (YYYY-MM-DD)."""
    config.ensure_dirs()
    file_path = config.DATA_DIR / f"snapshot-{snapshot_date}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Snapshot for date {snapshot_date} not found")
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse snapshot JSON: {e}") from e
