# wearcoach

Local AI Running Coach with Interactive Data Science Dashboard & Performance Analytics

## What This Is

`wearcoach` is a 100% local AI-powered running coach and training analytics system. It connects Strava activities with Oura Ring and Garmin Connect wellness data, storing persistent training memory in `.wiki/`.

This project enhances `wearcoach` with a local interactive web dashboard and data science suite inspired by `stravator`, featuring:
- **Interactive Web Dashboard**: Local web server rendering real-time performance analytics, HRV trends, ACWR (Acute:Chronic Workload Ratio) training load charts, and heart rate / pace distributions.
- **Dynamic Inline Charting**: ````chart```` block parsing and rendering via interactive frontend charts in the coaching UI.
- **Advanced Data Science Insights**: Strain/recovery balances, race time estimations, cross-training/CrossFit classification, and fatigue forecasting.

## Core Value

Empower athletes with local, private, data-driven running coaching and high-visibility training science visualizations without needing cloud subscriptions or third-party data lock-in.

## Requirements

### Validated

- ✓ Local CLI setup wizard (`python main.py setup`) — existing
- ✓ Strava OAuth2 activity fetching (`coach/strava.py`) — existing
- ✓ Oura Ring v2 wellness & readiness API (`coach/oura.py`) — existing
- ✓ Garmin Connect readiness, HRV, and ACWR tracking (`coach/garmin.py`) — existing
- ✓ Local snapshot generation in `data/snapshot-YYYY-MM-DD.json` (`main.py:cmd_fetch`) — existing
- ✓ Persistent memory in `.wiki/` via Karpathy's LLM-wiki pattern (`CLAUDE.md`) — existing
- ✓ Provider-agnostic LLM interface for Anthropic & OpenAI (`coach/llm.py`) — existing
- ✓ Automated unit test suite with mocked network coverage (`tests/`) — existing

### Active

- [ ] Local web server backend API (`python main.py dashboard`) to serve metrics and coaching chat sessions
- [ ] Interactive Dashboard UI frontend with training metrics, history, and real-time coaching interface
- [ ] Data science analytics engine (ACWR strain/fatigue curves, HRV readiness trends, pace & HR zone distribution)
- [ ] Dynamic ````chart```` JSON block parser and inline charting component (inspired by `stravator` chart builder)
- [ ] CrossFit / cross-training classification & multi-sport workload integration
- [ ] Race time estimation and performance trend predictors based on activity history and heart rate efficiency

### Out of Scope

- Cloud hosting or remote server deployment — 100% local execution strictly enforced
- Medical diagnosis or clinical prescription — health safety guardrails remain intact
- Mobile app (iOS/Android native) build — desktop web interface is the primary focus

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Local Web Architecture | Prioritize privacy and fast local execution matching existing `wearcoach` philosophy | Approved |
| Stravator-inspired Charting | Re-use ````chart```` JSON block schema for seamless LLM-to-UI visual rendering | Approved |
| Brownfield Baseline | Preserved all existing CLI, `.wiki/`, Strava/Oura/Garmin integrations | Approved |

## Context

Existing Python 3.10+ codebase with `requests`, `garminconnect`, `anthropic`, `openai`, `pytest`. Codebase map fully generated under `.planning/codebase/`. `stravator` reference repository analyzed at `C:\Users\Renato\src\stravator`.

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-22 after initialization*
