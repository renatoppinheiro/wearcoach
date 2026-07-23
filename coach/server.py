"""wearcoach local backend REST API server using FastAPI."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from coach import config, llm, prompt

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

_CHART_PATTERN = re.compile(r"```chart\n(.*?)\n```", re.DOTALL)


class FetchRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=60)


class ChatRequest(BaseModel):
    message: str
    days: int = Field(default=7, ge=1, le=60)


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


@app.post("/api/fetch")
def fetch_data(req: Optional[FetchRequest] = None) -> dict[str, Any]:
    """Trigger data pull from Strava / Oura / Garmin and save daily snapshot."""
    from coach import garmin, oura, strava

    days = req.days if req else 7

    if not strava.is_connected():
        raise HTTPException(status_code=400, detail="Strava not connected. Run: python main.py setup")

    activities = strava.fetch_recent_activities(days) if strava.is_connected() else []
    wellness: list[dict] = []
    source = None
    if oura.is_connected():
        wellness = oura.fetch_recent_wellness(days)
        source = "oura"
    elif garmin.is_connected():
        wellness = garmin.fetch_recent_wellness(days)
        source = "garmin"

    config.ensure_dirs()
    snapshot_filename = f"snapshot-{date.today().isoformat()}.json"
    out_path = config.DATA_DIR / snapshot_filename
    out_path.write_text(
        json.dumps({"activities": activities, "wellness": wellness, "wellness_source": source}, indent=2),
        encoding="utf-8",
    )
    return {
        "status": "success",
        "snapshot_file": snapshot_filename,
        "activities_count": len(activities),
        "wellness_count": len(wellness),
        "wellness_source": source,
    }


@app.post("/api/chat")
def chat_with_coach(req: ChatRequest) -> dict[str, Any]:
    """Send message to coach LLM and parse any ```chart``` JSON blocks."""
    config.ensure_dirs()
    snapshot_files = sorted(config.DATA_DIR.glob("snapshot-*.json"), reverse=True)
    if snapshot_files:
        try:
            snapshot = json.loads(snapshot_files[0].read_text(encoding="utf-8"))
            activities = snapshot.get("activities", [])
            wellness = snapshot.get("wellness", [])
            source = snapshot.get("wellness_source")
        except Exception:
            activities, wellness, source = [], [], None
    else:
        activities, wellness, source = [], [], None

    prompt_text = prompt.build(activities, wellness, source)
    full_prompt = f"{prompt_text}\n\nAthlete message: {req.message}"

    try:
        response_text = llm.ask(full_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM provider error: {e}") from e

    match = _CHART_PATTERN.search(response_text)
    chart_data = None
    cleaned_reply = response_text
    if match:
        raw_json = match.group(1).strip()
        try:
            chart_data = json.loads(raw_json)
            cleaned_reply = _CHART_PATTERN.sub("", response_text).strip()
        except json.JSONDecodeError:
            chart_data = None

    return {
        "reply": cleaned_reply,
        "chart": chart_data,
        "wellness_source": source,
    }

