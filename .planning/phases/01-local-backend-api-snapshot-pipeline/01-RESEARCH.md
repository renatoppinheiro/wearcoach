# Technical Research — Phase 1: Local Backend API & Snapshot Pipeline

**Phase:** 1 — Local Backend API & Snapshot Pipeline  
**Requirements:** REQ-INF-01, REQ-INF-02  
**Date:** 2026-07-22  

---

## 1. Executive Summary

Phase 1 provides the local backend API server infrastructure for `wearcoach`. It introduces the `python main.py dashboard` CLI command, launching a lightweight local server (FastAPI + Uvicorn) that exposes REST endpoints for reading local snapshots (`data/snapshot-*.json`), triggering data fetches, and communicating with the LLM coaching pipeline.

---

## 2. Technical Decisions & Framework Selection

### 2.1 Web Server Framework: FastAPI + Uvicorn
- **Rationale:**
  - Standard, high-performance Python ASGI framework with automatic OpenAPI documentation.
  - Native Pydantic model validation and JSON serialization.
  - Easy static file serving for web frontend assets.
  - Fits cleanly into the existing Python 3.10+ stack.
- **Dependencies Added:**
  - `fastapi>=0.110.0`
  - `uvicorn>=0.28.0`

### 2.2 Endpoint Architecture

| Endpoint | HTTP Method | Purpose | Request / Response |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | Server status check | `{"status": "ok", "version": "1.0.0"}` |
| `/api/snapshots` | `GET` | List all local snapshot files | `{"snapshots": ["snapshot-2026-07-22.json", ...]}` |
| `/api/snapshots/latest` | `GET` | Get latest daily snapshot data | Snapshot JSON payload |
| `/api/snapshots/{date}` | `GET` | Get snapshot for specific date | Snapshot JSON payload |
| `/api/fetch` | `POST` | Trigger fresh API fetch from Strava/Oura/Garmin | `{"status": "success", "fetched": {...}}` |
| `/api/chat` | `POST` | Coaching prompt endpoint (returns LLM text & optional ````chart```` JSON) | `{"reply": "...", "chart": {...}}` |

### 2.3 Integration with Existing `wearcoach` CLI
- Add `dashboard` subcommand to `main.py`:
  ```python
  dashboard_p = sub.add_parser("dashboard", help="launch local backend & web dashboard")
  dashboard_p.add_argument("--port", type=int, default=8000, help="port number (default 8000)")
  dashboard_p.add_argument("--host", type=str, default="127.0.0.1", help="host address")
  ```
- Module placement: `coach/server.py` encapsulates FastAPI app creation, CORS configuration, and router bindings.

---

## 3. Validation Architecture & Testing Strategy

- **Test Suite:** `tests/test_server.py`
- **Test Runner:** Pytest using `fastapi.testclient.TestClient`.
- **Coverage Requirements:**
  - Verify `/api/health` returns `200 OK`.
  - Verify `/api/snapshots` correctly parses `data/` directory.
  - Verify `/api/snapshots/latest` returns `404` when data directory is empty and `200` with valid JSON when snapshot exists.
  - Mock external API calls during `/api/fetch` and `/api/chat` tests.

---

## 4. Risks & Mitigations

- **Risk:** Port 8000 conflict with other local development services.
  - **Mitigation:** `--port` argument CLI option allowing customizable binding port.
- **Risk:** Missing data directory or empty snapshot folder.
  - **Mitigation:** Graceful error handling in snapshot endpoints returning empty list / clear HTTP 404 message.
