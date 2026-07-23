# Phase 2: Data Science & Analytics Engine - Research

**Researched:** 2026-07-23
**Domain:** Sports-science training-load analytics (ACWR, fitness/fatigue curves, HRV/readiness trend & correlation) implemented as pure-Python calculation modules over existing local snapshot data
**Confidence:** MEDIUM

## Summary

Phase 2 has no CONTEXT.md — no discuss-phase happened, so there are no locked user decisions. This research fills that gap using REQUIREMENTS.md, STATE.md, ROADMAP.md, and a direct read of the Phase-1 codebase (`coach/server.py`, `coach/strava.py`, `coach/oura.py`, `coach/garmin.py`, `main.py`). Several of the choices below (EWMA vs. rolling-average ACWR, the training-load formula, and the definition of "training quality" for REQ-DS-02's correlation) are sports-science conventions with more than one valid answer — they are marked `[ASSUMED]` and belong in the Assumptions Log so the planner/user can confirm them, per the same rule that would normally apply to CONTEXT.md-sourced decisions.

The core finding: this is **not a numpy/pandas job**. wearcoach snapshots are small (≤60 days, capped by the existing `--days` CLI/API limits), and Python 3.10+ (the project's stated minimum) ships `statistics.correlation`, `statistics.linear_regression`, and `statistics.fmean` in the standard library — verified directly in this environment (Python 3.12.10). Adding pandas/numpy would contradict the project's explicit "lightweight, local, no heavy deps" ethos (CLAUDE.md, README) for no real benefit at this data scale. **No new third-party packages are needed for this phase.**

The second core finding: raw Strava activity fields never reliably include `perceived_exertion` (Strava's RPE field requires manual in-app logging and is usually `null`), and none of the three data sources expose the athlete's max/resting HR needed for a textbook TRIMP calculation. This forces a **tiered training-load fallback** (sRPE → HR-based proxy → duration-only) rather than a single canonical formula, and this must be documented and surfaced to the caller (which tier fired), not silently applied.

The third core finding: the existing `--days` cap (max 60, default 7 in both CLI and `/api/fetch`) means a snapshot fetched with defaults has **only 7 days of activity history** — nowhere near the 28-day chronic window ACWR needs. The analytics layer must either request `days=60` itself when data is insufficient, or clearly report `insufficient_history` rather than silently producing a misleading ratio. This is the single most important pitfall for planning task ordering and acceptance criteria.

**Primary recommendation:** Add a stdlib-only `coach/analytics.py` module with pure functions (daily load aggregation with fallback tiers → zero-filled daily series → rolling-average or EWMA ACWR → Banister-style CTL/ATL/TSB fitness-fatigue curve → HRV/readiness trend + Pearson-correlation vs. training load), exposed both as a new `python main.py analytics` CLI command (writes `data/analytics-{date}.json`, so the CLAUDE.md agent-as-coach workflow can read it without the dashboard server running) and a new `GET /api/analytics` endpoint on the existing FastAPI app (for Phase 3 to consume).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Training-load aggregation (per-activity → per-day) | API/Backend (`coach/analytics.py`) | — | Pure computation over already-fetched JSON; no I/O of its own |
| ACWR (rolling-average / EWMA) | API/Backend (`coach/analytics.py`) | — | Same module, depends only on the daily load series |
| Fitness/fatigue curve (CTL/ATL/TSB) | API/Backend (`coach/analytics.py`) | — | Same time-series input as ACWR, different EWMA time constants |
| HRV/readiness trend + correlation | API/Backend (`coach/analytics.py`) | — | Consumes `wellness` list already fetched in Phase 1; branches on `wellness_source` |
| Sufficient-history guarantee (fetch enough days) | API/Backend (`main.py` CLI cmd / `coach/server.py` endpoint) | — | Orchestration concern, not a pure-function concern — belongs with the existing `fetch`/`/api/fetch` call sites, not inside the calculation module |
| Persisted analytics output (`data/analytics-*.json`) | Database/Storage (flat file, matching Phase 1's snapshot pattern) | — | Consistent with `data/snapshot-*.json`; no new datastore introduced |
| Chart-ready JSON shape for Phase 3 | API/Backend (response contract) | Browser/Client (Phase 3 consumes it) | Phase 2 only needs to guarantee JSON-serializable `{date, value}`-style series; rendering is explicitly Phase 3's job |

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-DS-01 | ACWR & Training Load Model — calculate ACWR, fatigue, and strain scores | Standard Stack + Architecture Patterns (`build_daily_load_series`, `rolling_average_acwr`/`ewma_acwr`, `fitness_fatigue_curve`) below; Common Pitfalls #1-#5 cover the load-formula fallback and history-length gotchas |
| REQ-DS-02 | HRV & Readiness Correlation — correlate HRV balance and readiness scores against training quality | Architecture Patterns (`hrv_readiness_trend`, `correlate_readiness_vs_load`); Common Pitfalls #6-#7 cover the Oura/Garmin field mismatch; Assumptions Log #A3 flags that "training quality" is undefined in REQUIREMENTS.md |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `statistics` (stdlib) | Python 3.10+ (ships with 3.12.10 in this env) | `correlation()`, `linear_regression()`, `fmean()`, `mean()`, `stdev()` for HRV/load correlation and CV | `[VERIFIED: confirmed via python -c "import statistics; print(statistics.correlation)"` in this environment — no install needed, matches project's stated Python 3.10+ floor] |
| `datetime` / `date` (stdlib) | stdlib | Building the continuous, zero-filled daily calendar needed for rolling windows | `[VERIFIED: already used throughout coach/*.py]` |
| `json` (stdlib) | stdlib | Reading `data/snapshot-*.json`, writing `data/analytics-*.json` | `[VERIFIED: existing pattern in coach/server.py, main.py]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `fastapi` | 0.135.2 (already installed, `requirements.txt` pins `>=0.110.0`) | New `GET /api/analytics` endpoint on the existing app | Already a project dependency from Phase 1 — no version bump needed `[VERIFIED: python -c "import fastapi; print(fastapi.__version__)"]` |
| `pytest` | 9.0.2 (already installed) | Unit tests for the new analytics module | Matches Phase 1's `tests/test_server.py` pattern `[VERIFIED: python -m pytest --version]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `statistics` for correlation/rolling stats | `pandas` + `numpy` | Pandas makes rolling windows and resampling more concise, but adds ~50MB+ of dependencies for a dataset of ≤60 daily rows — contradicts the project's "100% local, minimal deps" positioning (README badge, CLAUDE.md). `[ASSUMED — recommend against, but flag as Claude's Discretion for the planner/user to override if they'd rather standardize on pandas ahead of Phase 4's race-prediction modeling, which may benefit more from it.]` |
| Session-RPE (sRPE) as the primary training-load metric | Heart-rate-based TRIMP | TRIMP (Banister 1991) needs HRmax and resting HR per athlete, which no current data source (Strava/Oura/Garmin fetch code) collects. Building it would require a new athlete-profile input this phase doesn't otherwise need. `[CITED: iamcoach.ai TRIMP explainer, Banister TRIMP literature]` |
| Rolling-average (RA) ACWR | EWMA ACWR | EWMA (Williams et al. 2016) is shown to be a more sensitive injury-risk indicator than RA and avoids RA's "phantom load" cliff-edge (a big session abruptly drops out of the window 7 days later). Recommend EWMA as primary, but RA is simpler to explain to a solo user and is what most public ACWR explainers describe first — `[ASSUMED, needs confirmation]`, see Assumptions Log #A1. |

**Installation:**
No new packages required — `pip install -r requirements.txt` (already run in Phase 1) is sufficient.

**Version verification:**
```
python -c "import statistics; print(statistics.correlation)"   # confirmed present, Python 3.12.10
python -c "import fastapi, uvicorn; print(fastapi.__version__, uvicorn.__version__)"  # 0.135.2 0.42.0
python -m pytest --version   # pytest 9.0.2
```
All verified directly in the project's active environment on 2026-07-23 — no registry lookups needed since no new packages are being added.

## Package Legitimacy Audit

**No new external packages are introduced by this phase.** Every function needed (correlation, linear regression, rolling means, EWMA) is achievable with the Python 3.10+ standard library already required by this project (`main.py` enforces `sys.version_info < (3, 10)` at startup). The Package Legitimacy Gate is therefore not applicable — there is nothing to run `gsd-tools query package-legitimacy check` against.

If the planner or user later decides to adopt pandas/numpy (see "Alternatives Considered" above), that decision should re-trigger this gate before installation.

**Packages removed due to [SLOP] verdict:** none (nothing was proposed)
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
data/snapshot-*.json (Phase 1 output: activities[], wellness[], wellness_source)
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│ coach/analytics.py  (pure functions, no I/O)                │
│                                                              │
│  activities[] ──▶ build_daily_load_series()                 │
│                     │  (tiered fallback: sRPE → HR proxy →   │
│                     │   duration-only; zero-fills rest days) │
│                     ▼                                       │
│              daily_load: {date: float}                      │
│                     │                                       │
│         ┌───────────┼────────────────┐                      │
│         ▼           ▼                ▼                      │
│  rolling_average_   ewma_acwr()  fitness_fatigue_curve()     │
│  acwr()             (7d/28d EWMA)   (CTL/ATL/TSB,            │
│  (7d/28d ratio)                     Banister tau=7/42)       │
│         │           │                │                      │
│         └─────┬─────┴────────────────┘                      │
│               ▼                                             │
│      acwr_result: [{date, acute, chronic, ratio, zone}]      │
│                                                              │
│  wellness[] + wellness_source ──▶ hrv_readiness_trend()      │
│         (branches Oura contributor-score vs. Garmin raw-ms)  │
│               │                                              │
│               ▼                                             │
│      hrv_result: {rolling_7d, baseline_28d, cv, trend}       │
│               │                                              │
│      + daily_load  ──▶ correlate_readiness_vs_load()         │
│               ▼             (statistics.correlation,          │
│      correlation_result      min-N gated)                    │
└────────────────────────────────────────────────────────────┘
        │                                   │
        ▼                                   ▼
main.py `analytics` CLI                coach/server.py
(writes data/analytics-{date}.json)    GET /api/analytics
        │                                   │
        ▼                                   ▼
CLAUDE.md agent-as-coach reads         Phase 3 dashboard UI
the JSON file directly                 fetches JSON over HTTP
(no server needed — matches            (chart-ready {date,value}
 the project's primary CLI-only        series, same shape as the
 workflow)                             file output)
```

### Recommended Project Structure
```
coach/
├── analytics.py       # NEW — pure calculation functions (this phase)
├── server.py          # MODIFIED — add GET /api/analytics
├── prompt.py           # unchanged this phase (Phase 3/agent may consume analytics later)
├── strava.py / oura.py / garmin.py   # unchanged — already produce the inputs
main.py                 # MODIFIED — add `analytics` subcommand
tests/
└── test_analytics.py   # NEW — unit tests for coach/analytics.py
```

### Pattern 1: Tiered training-load fallback (per activity, per day)
**What:** Compute a single "load" score per activity using the best available signal, and record which tier fired so downstream consumers can flag low-confidence data.
**When to use:** Every activity in the `activities` list, before building the daily series.
**Example:**
```python
# coach/analytics.py — pattern, not verbatim source
def activity_load(activity: dict) -> tuple[float, str]:
    duration_min = activity.get("moving_time_min") or 0
    rpe = activity.get("perceived_exertion")
    avg_hr = activity.get("avg_hr")

    if rpe and duration_min:
        # Session-RPE (Foster et al., 2001): load = RPE x duration(min)
        return rpe * duration_min, "srpe"
    if avg_hr and duration_min:
        # HR-weighted proxy — NOT a validated TRIMP (no HRmax/HRrest available).
        # Documented as a relative proxy only.
        return avg_hr * duration_min / 100, "hr_proxy"
    # Duration-only fallback — the common case, since Strava rarely populates RPE.
    return float(duration_min), "duration_only"
```

### Pattern 2: Zero-filled continuous daily series before any rolling math
**What:** Build a dict/list covering every calendar day in range (including rest days as `0.0`), never just the days with activities.
**When to use:** Immediately before any rolling-average or EWMA calculation — this is the #1 correctness bug source for ACWR implementations.
**Example:**
```python
from datetime import date, timedelta

def fill_missing_days(daily_totals: dict[str, float], start: date, end: date) -> dict[str, float]:
    out = {}
    d = start
    while d <= end:
        key = d.isoformat()
        out[key] = daily_totals.get(key, 0.0)
        d += timedelta(days=1)
    return out
```

### Pattern 3: EWMA ACWR (Williams et al., 2016 formulation)
**What:** Exponentially weighted moving average for both acute and chronic loads, lambda = 2/(N+1).
**When to use:** Primary ACWR method (see Assumptions Log #A1 for the RA alternative).
**Example:**
```python
# Source: formulation described in Williams et al. 2016 (PubMed 28003238) and
# the public `ACWR` R package's EWMA() reference (rdrr.io/cran/ACWR/man/EWMA.html)
def ewma_series(daily_values: list[float], span_days: int) -> list[float]:
    lam = 2 / (span_days + 1)
    out = []
    prev = daily_values[0]
    for v in daily_values:
        prev = lam * v + (1 - lam) * prev
        out.append(prev)
    return out

def ewma_acwr(daily_series: dict[str, float], acute_days: int = 7, chronic_days: int = 28) -> list[dict]:
    dates = sorted(daily_series)
    values = [daily_series[d] for d in dates]
    acute = ewma_series(values, acute_days)
    chronic = ewma_series(values, chronic_days)
    out = []
    for i, d in enumerate(dates):
        ratio = acute[i] / chronic[i] if chronic[i] else None
        out.append({"date": d, "acute": round(acute[i], 1), "chronic": round(chronic[i], 1),
                    "acwr": round(ratio, 2) if ratio is not None else None,
                    "insufficient_history": i < chronic_days})
    return out
```

### Pattern 4: Banister-style fitness/fatigue curve (CTL/ATL/TSB) for the "strain/fatigue curves" deliverable
**What:** The same EWMA machinery as Pattern 3, but reported as an absolute difference (form/freshness) instead of a ratio — this is what the phase description's "strain/fatigue curves" phrase maps to in standard sports-science terminology (TrainingPeaks' Performance Management Chart: CTL ≈ fitness, ATL ≈ fatigue, TSB = CTL − ATL ≈ form).
**When to use:** Alongside ACWR, using the same `daily_load` series, with longer time constants (tau ≈ 42 days chronic / 7 days acute, per Banister's original impulse-response model).
**Example:**
```python
# Source: Banister impulse-response model, as popularized by TrainingPeaks'
# Performance Manager (trainingpeaks.com/learn/articles/the-science-of-the-performance-manager)
def fitness_fatigue_curve(daily_series: dict[str, float], fitness_tau: int = 42, fatigue_tau: int = 7) -> list[dict]:
    dates = sorted(daily_series)
    values = [daily_series[d] for d in dates]
    ctl = ewma_series(values, fitness_tau)
    atl = ewma_series(values, fatigue_tau)
    return [
        {"date": d, "ctl": round(ctl[i], 1), "atl": round(atl[i], 1), "tsb": round(ctl[i] - atl[i], 1)}
        for i, d in enumerate(dates)
    ]
```

### Pattern 5: Source-branching HRV/readiness trend (Oura vs. Garmin field mismatch)
**What:** Oura exposes `hrv_balance_contrib` as a normalized 0-100 contributor score; Garmin exposes `sleep_hrv_overnight_avg_ms` as raw milliseconds plus a categorical `hrv_status`. These are not interchangeable and must not be averaged together as if they were the same unit.
**When to use:** Any HRV trend/correlation function must branch on `wellness_source` before picking which field(s) to read.
**Example:**
```python
def hrv_readiness_trend(wellness: list[dict], wellness_source: str | None) -> dict:
    if wellness_source == "oura":
        field = "hrv_balance_contrib"
    elif wellness_source == "garmin":
        field = "sleep_hrv_overnight_avg_ms"
    else:
        return {"available": False, "reason": "no wellness source connected"}

    values = [(d["date"], d[field]) for d in wellness if d.get(field) is not None]
    if len(values) < 7:
        return {"available": False, "reason": f"fewer than 7 days of {field} data"}
    # ... rolling 7-day avg vs 28-day baseline + CV, per Plews/Buchheit weekly-average method
```

### Anti-Patterns to Avoid
- **Averaging only the days with training data:** Skipping rest days when computing chronic load inflates the average and produces falsely low ACWR ratios — always zero-fill (Pattern 2).
- **Presenting an HR-weighted proxy as "TRIMP":** Without athlete HRmax/HRrest, any HR × duration formula is a relative proxy, not the validated Banister TRIMP. Label it honestly in the output (`method: "hr_proxy"`), don't imply clinical validity.
- **Treating a coupled ACWR (acute load embedded in the chronic denominator) as automatically wrong:** Lolli et al.'s mathematical-coupling critique is real, but empirical comparisons show coupled vs. uncoupled ACWR correlate .88-.99 in practice — for a single-user hobby tool, coupled RA/EWMA (the conventional, simpler form) is an acceptable, well-precedented choice. Document the choice; don't silently pick one without a comment explaining why.
- **Assuming the latest snapshot has enough history:** See Common Pitfall #1 below — this is the most consequential anti-pattern for this specific codebase.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pearson correlation coefficient | A custom covariance/stdev correlation formula | `statistics.correlation(x, y)` (stdlib, Python 3.10+) | Already available, tested, avoids off-by-one/degrees-of-freedom bugs; `[VERIFIED: confirmed importable in this environment]` |
| Linear trend fitting | Manual least-squares loop | `statistics.linear_regression(x, y)` (stdlib, Python 3.10+) | Same rationale — no reason to hand-roll basic regression when stdlib has it |
| EWMA / rolling windows over ≤60 daily points | A hand-rolled deque-based rolling buffer with edge-case bugs at series start | The `ewma_series`/zero-fill pattern above (Patterns 2-3) — still hand-written, but following the standard, published formula (lambda = 2/(N+1)) rather than inventing a bespoke smoothing scheme | The formula is simple enough that a dependency (e.g. pandas `.ewm()`) isn't justified, but the *math itself* must follow the published Williams/Banister formulation, not an ad-hoc "average of last N and average of last N with more weight on recent" approximation, which produces different-enough numbers to mislead the athlete |

**Key insight:** The risk in this domain isn't "reinventing a library" (the math is genuinely simple) — it's reinventing the sports-science *formula* incorrectly (wrong lambda, un-zero-filled gaps, treating a proxy metric as a validated one) in a way that produces plausible-looking but wrong numbers for a training-load tool.

## Common Pitfalls

### Pitfall 1: Default snapshot history is far shorter than the chronic window needs
**What goes wrong:** `python main.py fetch` and `POST /api/fetch` both default `--days`/`days` to 7. A snapshot fetched with defaults has only 7 days of `activities`, but ACWR's chronic window needs 28 days (and ideally 28+7=35 to compute a ratio for "today" using a fully-populated chronic average).
**Why it happens:** Phase 1's default was tuned for "recent activities for a daily briefing," not for a rolling training-load model.
**How to avoid:** The analytics CLI command / `/api/analytics` endpoint must check the date range actually present in the source data and, if it's under the required minimum, re-fetch with `days=60` (the existing hard cap in both `FetchRequest` and the CLI's `--days` validation) rather than silently computing on 7 days of history.
**Warning signs:** ACWR values that look identical to a simple 7-day average, or a `chronic` value that equals `acute` (a giveaway that zero-filling ran over a too-short window).

### Pitfall 2: `perceived_exertion` is almost always null in real Strava payloads
**What goes wrong:** Building the training-load formula around sRPE as the primary/only method silently produces all-zero or all-duration-only loads for most users, since Strava's RPE field requires the athlete to manually log it in-app per activity.
**Why it happens:** `perceived_exertion` looks like a first-class Strava field (it's already extracted in `coach/strava.py`), so it's tempting to treat it as reliably populated.
**How to avoid:** Design the tiered fallback (Pattern 1) so duration-only is a fully-supported, expected common case — not a degraded edge case — and surface `method` per day/activity in the output so the UI (Phase 3) or the coach prompt can be honest about data quality (`[ASSUMED — this needs a runtime check against a real connected Strava account's data to confirm the null-rate; recommend a spot-check task]`).
**Warning signs:** All computed loads show `method: "duration_only"` in real usage.

### Pitfall 3: No HRmax/HRrest data exists anywhere in the current fetch pipeline for a real TRIMP
**What goes wrong:** Implementing "the standard TRIMP formula" from a tutorial without noticing it requires athlete-specific HRmax/HRrest constants that this codebase has no field for collecting.
**Why it happens:** Most TRIMP tutorials assume a fitness-platform context where the athlete profile already has these values.
**How to avoid:** Either (a) skip true TRIMP and use the HR-proxy documented in Pattern 1, clearly labeled, or (b) add HRmax/HRrest as new `.env`/setup-wizard fields — a scope decision the planner should make explicitly rather than silently picking (a) without noting the tradeoff.
**Warning signs:** A "TRIMP" implementation that doesn't reference HRmax or HRrest anywhere.

### Pitfall 4: Averaging Oura's 0-100 contributor score with Garmin's raw-ms HRV as if they were the same unit
**What goes wrong:** A single "HRV trend" function that reads a hardcoded field name assumes only one source is ever connected; if code is later reused across both branches without care, contributor-score deltas (usually single-digit point moves) get compared against ms deltas (can be tens of ms), producing meaningless "trend" magnitudes.
**Why it happens:** Both fields are informally "the HRV number" in casual conversation, but they are structurally different metrics computed by different vendors.
**How to avoid:** Branch explicitly on `wellness_source` (Pattern 5); never blend the two into one combined series.
**Warning signs:** A trend function that doesn't reference `wellness_source` at all.

### Pitfall 5: Silent division-by-zero / undefined ratio on the first N days of a series
**What goes wrong:** Early in a series (before the chronic window fills), `chronic` load is 0 or near-0, and computing `acute/chronic` either crashes (`ZeroDivisionError`) or produces `inf`/nonsensical spikes that get serialized into JSON and potentially charted by Phase 3.
**Why it happens:** Zero-filled rest days plus a short history window both push early chronic averages toward zero.
**How to avoid:** Always guard the division and emit `None`/`null` with an explicit `insufficient_history: true` flag (as in Pattern 3) rather than `0`, `inf`, or a crash.
**Warning signs:** JSON output containing `Infinity` or `NaN` (not valid JSON — will break Phase 3's chart parser), or a 500 error from `/api/analytics` on a fresh account with little history.

### Pitfall 6: Treating every Strava `type` as a running session for pace-based load
**What goes wrong:** Phase 2's description is running-focused, but `activities` includes every Strava activity type (the multi-sport classifier is explicitly deferred to Phase 4/REQ-DS-03). Computing distance-per-minute "pace" for a strength/CrossFit session (`type` != running variants) produces nonsensical numbers.
**Why it happens:** The existing `avg_pace_min_per_km` field in `coach/strava.py` is computed for *any* activity with distance+time, including e.g. a rowing or hiking activity.
**How to avoid:** Training-load aggregation (Pattern 1) should work generically across all activity types (duration/HR are type-agnostic), but any pace-based reporting should either filter to running types or be explicitly out of scope this phase — document the choice rather than let it fall out accidentally. `[ASSUMED — recommend generic load aggregation across all types for REQ-DS-01, explicitly deferring sport-specific weighting to Phase 4, per ROADMAP.md's phase split.]`
**Warning signs:** A "pace" or "quality" metric silently including strength-training sessions with a 0km distance, producing divide-by-zero or absurd pace values.

## Code Examples

### Correlating readiness vs. training load (REQ-DS-02)
```python
# Source: statistics module docs (docs.python.org/3/library/statistics.html#statistics.correlation),
# confirmed available in this project's Python 3.12.10 environment.
import statistics

def correlate_readiness_vs_load(
    wellness_by_date: dict[str, float],   # e.g. readiness_score or hrv field, by date
    load_by_date: dict[str, float],       # daily training load, by date
    min_points: int = 10,
) -> dict:
    common_dates = sorted(set(wellness_by_date) & set(load_by_date))
    if len(common_dates) < min_points:
        return {"available": False, "reason": f"only {len(common_dates)} overlapping days, need {min_points}+"}

    x = [wellness_by_date[d] for d in common_dates]
    y = [load_by_date[d] for d in common_dates]
    r = statistics.correlation(x, y)
    return {"available": True, "r": round(r, 3), "n": len(common_dates)}
```

### Minimum-history guard before computing ACWR (Pitfall 1 mitigation)
```python
MIN_HISTORY_DAYS = 35  # 28-day chronic window + 7-day acute lookback

def has_sufficient_history(activities: list[dict]) -> bool:
    if not activities:
        return False
    dates = sorted(a["date"] for a in activities if a.get("date"))
    if not dates:
        return False
    span = (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days
    return span >= MIN_HISTORY_DAYS
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Rolling-average (RA) ACWR (Hulin et al., original formulation) | Exponentially weighted moving average (EWMA) ACWR (Williams et al., 2016) | Sports-science consensus shifted ~2016 toward EWMA as more sensitive to injury risk, though RA remains widely used in consumer apps for simplicity | Recommend EWMA as primary here (more defensible, still simple to implement), but note RA is what most public explainers describe first and is easier for a solo user to sanity-check by hand — `[ASSUMED, see Assumptions Log #A1]` |
| Coupled ACWR (acute embedded in chronic denominator) | Uncoupled ACWR proposed by Lolli et al. (2017) to avoid mathematical coupling / spurious correlation | Debate ongoing since 2017; empirical studies (Pillitteri et al., others) show coupled/uncoupled correlate .88-.99 | For a single hobbyist tool, the practical difference is negligible — coupled (conventional) form recommended for simplicity, documented explicitly |

**Deprecated/outdated:** None specific to this phase — this is a stable, decades-old sports-science domain (Banister 1975, Foster 2001, Gabbett 2016) with no fast-moving framework/library churn to track.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | EWMA (not rolling-average) is the primary ACWR method | Standard Stack / Alternatives Considered, State of the Art | Low-to-medium — both are valid, well-precedented methods; if the user prefers RA for simplicity/transparency, this is a config-level swap, not a rewrite, since both share the zero-filled daily series (Pattern 2) as input |
| A2 | Training load uses a tiered sRPE → HR-proxy → duration-only fallback, with duration-only expected to be the common case | Architecture Patterns (Pattern 1), Common Pitfalls #2-#3 | Medium — if the planner instead assumes sRPE will "just work," resulting ACWR/CTL/ATL numbers may be flat/wrong for any account where `perceived_exertion` is never populated (likely most accounts) |
| A3 | "Training quality" (REQ-DS-02) is operationalized as same-day/next-day training load correlated against readiness/HRV, via Pearson r | Architecture Patterns (Pattern 5, correlate_readiness_vs_load) | Medium — REQUIREMENTS.md doesn't define "training quality"; the user may have meant pace, consistency, or subjective session rating instead of load. Recommend confirming this definition before/during planning rather than after building the correlation function |
| A4 | Both `python main.py analytics` (file output) and `GET /api/analytics` (HTTP) should exist, not just one | Summary, Architecture Diagram | Low — CLAUDE.md's documented primary workflow is CLI/file-based (agent reads `data/*.json` directly, no server needed); Phase 1's server is a secondary path. Building only the HTTP endpoint would strand the primary agent-as-coach workflow described in CLAUDE.md |
| A5 | Generic (sport-agnostic) load aggregation across all Strava activity types, deferring sport-specific weighting to Phase 4 | Common Pitfalls #6 | Low — matches ROADMAP.md's explicit REQ-DS-03/Phase 4 split, but worth confirming the planner doesn't try to pull multi-sport classification forward into Phase 2 |

**If this table is empty:** N/A — see rows above; all should be confirmed with the user before or during planning since no CONTEXT.md/discuss-phase captured these decisions.

## Open Questions

1. **Should HRmax/HRrest be added as new setup-wizard/`.env` inputs to enable a real TRIMP calculation?**
   - What we know: No current data source provides these; the HR-proxy in Pattern 1 is a reasonable stand-in.
   - What's unclear: Whether the user wants this precision now or is fine deferring it (possibly forever, given the project's "keep it simple" ethos).
   - Recommendation: Default to the HR-proxy/duration-only tiers for this phase; treat "real TRIMP" as a backlog item, not a Phase 2 requirement — REQ-DS-01 doesn't specify TRIMP.

2. **Does the coach prompt (`coach/prompt.py`) need to consume analytics output this phase, or is that Phase 3+'s job?**
   - What we know: CLAUDE.md's briefing flow currently reads `activities`/`wellness` directly from the snapshot; it doesn't yet reference any ACWR/HRV-trend computation.
   - What's unclear: Whether Phase 2 should also wire `analytics-*.json` into `prompt.build()` so the coach's briefing text can cite ACWR/HRV trend numbers, or whether that integration belongs to a later phase alongside the UI work.
   - Recommendation: Treat prompt-integration as optional/stretch for this phase since it's not covered by REQ-DS-01/REQ-DS-02 (which describe the calculation engine, not chat integration); flag explicitly to the user during planning.

3. **What should the exact ACWR "zone" thresholds be (sweet spot / undertraining / high-risk)?**
   - What we know: Gabbett's commonly-cited "sweet spot" is 0.8-1.3, with >1.5 flagged as high injury risk `[CITED: scienceforsport.com/acutechronic-workload-ratio]`.
   - What's unclear: Whether these generic team-sport-derived thresholds are appropriate for a solo recreational/competitive runner, or should be tunable.
   - Recommendation: Implement as named constants (not magic numbers inline) so they're trivially adjustable later without needing a rewrite.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ (for `statistics.correlation`/`linear_regression`) | All analytics math | ✓ | 3.12.10 | — |
| fastapi | New `/api/analytics` endpoint | ✓ | 0.135.2 | — |
| uvicorn | Serving the endpoint | ✓ | 0.42.0 | — |
| pytest | New `tests/test_analytics.py` | ✓ | 9.0.2 | — |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none — everything this phase needs is already installed in the active environment.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (already configured) |
| Config file | `pytest.ini` (`pythonpath = .`, `testpaths = tests`) |
| Quick run command | `pytest tests/test_analytics.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-DS-01 | Daily load aggregation picks the correct fallback tier (sRPE / HR-proxy / duration-only) per activity | unit | `pytest tests/test_analytics.py -k load -x` | ❌ Wave 0 |
| REQ-DS-01 | Zero-filling produces a continuous daily series with rest days at 0.0 | unit | `pytest tests/test_analytics.py -k fill_missing -x` | ❌ Wave 0 |
| REQ-DS-01 | ACWR (EWMA and/or RA) returns `insufficient_history: true` before the chronic window is full, and never divides by zero | unit | `pytest tests/test_analytics.py -k acwr -x` | ❌ Wave 0 |
| REQ-DS-01 | Fitness/fatigue curve (CTL/ATL/TSB) produces monotonically-sane values for a synthetic constant-load series | unit | `pytest tests/test_analytics.py -k fitness_fatigue -x` | ❌ Wave 0 |
| REQ-DS-02 | HRV/readiness trend branches correctly on `wellness_source` (Oura contributor score vs. Garmin raw ms) | unit | `pytest tests/test_analytics.py -k hrv -x` | ❌ Wave 0 |
| REQ-DS-02 | Correlation function returns `available: false` below `min_points`, and a valid `r` above it | unit | `pytest tests/test_analytics.py -k correlate -x` | ❌ Wave 0 |
| REQ-DS-01/02 | `GET /api/analytics` returns 200 with valid JSON given a sufficient snapshot, and a clear error/insufficient-history response given a sparse one | integration | `pytest tests/test_server.py -k analytics -x` | ❌ Wave 0 (extends existing `tests/test_server.py`) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_analytics.py -x`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_analytics.py` — new file, covers REQ-DS-01 and REQ-DS-02 unit behavior above
- [ ] Extend `tests/test_server.py` with analytics-endpoint cases (reuse the existing `TestClient(app)` + `patch("coach.config.DATA_DIR", tmp_path)` pattern already used for `/api/fetch`/`/api/chat`)
- [ ] No framework install needed — pytest/fastapi/TestClient already present and used identically in Phase 1's tests

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Server remains local-only, no new auth surface introduced (matches Phase 1: FastAPI app bound to `127.0.0.1` by default, no login) |
| V3 Session Management | No | No sessions introduced |
| V4 Access Control | No | Single-user local tool, no multi-tenant access control needed |
| V5 Input Validation | Yes | The new `/api/analytics` endpoint's only input is an optional `days`/query param — reuse the existing Pydantic `Field(default=7, ge=1, le=60)` bounding pattern already used by `FetchRequest`/`ChatRequest` in `coach/server.py` |
| V6 Cryptography | No | No new secrets, tokens, or crypto operations introduced by pure-calculation code |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed/adversarial snapshot JSON crashing the analytics endpoint (e.g. non-numeric `moving_time_min`) | Denial of Service | Defensive type/None checks in `build_daily_load_series` (already the pattern in `coach/garmin.py`'s `_safe()` wrapper) — a bad snapshot file should degrade gracefully (skip the malformed activity, don't 500 the whole endpoint) |
| Unbounded `days`/history parameter causing excessive computation | Denial of Service | Reuse the existing `ge=1, le=60` bound already enforced elsewhere in this codebase |

This phase introduces no new network egress, no new secrets, and no new authentication surface — it is a pure local-computation layer over already-local, already-fetched data. The main security-relevant discipline is input validation on the new endpoint's parameters and defensive parsing of snapshot JSON, both of which already have an established pattern in this codebase to follow.

## Sources

### Primary (HIGH confidence)
- Direct codebase reads: `coach/server.py`, `coach/strava.py`, `coach/oura.py`, `coach/garmin.py`, `main.py`, `coach/prompt.py`, `coach/config.py`, `tests/test_server.py`, `pytest.ini`, `requirements.txt` — all read directly in this session
- Direct environment verification in this project's active Python: `statistics.correlation`/`linear_regression`/`fmean` presence, `fastapi` 0.135.2, `uvicorn` 0.42.0, `pytest` 9.0.2, Python 3.12.10

### Secondary (MEDIUM confidence — cross-checked across multiple independent sources)
- Williams et al. 2016, "Calculating acute:chronic workload ratios using exponentially weighted moving averages provides a more sensitive indicator of injury likelihood than rolling averages" — pubmed.ncbi.nlm.nih.gov/28003238
- Lolli et al., "Mathematical coupling causes spurious correlation within the conventional acute-to-chronic workload ratio calculations" — semanticscholar.org/paper/82ac20419732a7838501199915536bb11bc66c7a
- Foster et al. 2001 session-RPE method — pmc.ncbi.nlm.nih.gov/articles/PMC5673663 (Frontiers review) and academia.edu/researchgate cross-references
- ScienceForSport, "Acute:Chronic Workload Ratio" (Gabbett sweet-spot zone thresholds) — scienceforsport.com/acutechronic-workload-ratio
- TrainingPeaks, "The Science of the TrainingPeaks Performance Manager" (CTL/ATL/TSB, Banister impulse-response model, EWMA formula g(t) = g(t-1)e^(-1/tau) + w(t)(1-e^(-1/tau))) — trainingpeaks.com/learn/articles/the-science-of-the-performance-manager
- Plews/Buchheit weekly-average HRV method and coefficient-of-variation interpretation — elitehrv.com/improving-hrv-data-interpretation-coefficient-variation, marcoaltini.substack.com/p/a-brief-history-of-heart-rate-variability-guided-training

### Tertiary (LOW confidence — background only, not load-bearing for any recommendation above)
- WHOOP's proprietary 0-21 Strain score methodology (whoop.com/us/en/thelocker/how-does-whoop-strain-work-101) — informed the choice of *terminology* ("strain") but WHOOP's exact algorithm is proprietary and requires continuous HR streaming data this project doesn't have; not used as a formula source

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified directly against the running environment, no new packages, no ambiguity
- Architecture: MEDIUM — module boundaries and CLI/API dual-exposure are well-grounded in the existing codebase's own patterns, but the exact function signatures are this researcher's design, not sourced from an existing implementation
- Pitfalls: MEDIUM-HIGH — the history-length gap (Pitfall 1) and the missing-RPE/TRIMP-inputs gap (Pitfalls 2-3) are derived directly from reading the actual Phase 1 fetch code, not assumed; the sports-science formulas (Pitfalls 4-5) are cross-checked against multiple independent published sources

**Research date:** 2026-07-23
**Valid until:** 2027-01-23 (sports-science formulas are stable/decades-old; the only fast-moving part — this project's own snapshot schema — should be re-checked if Phase 1's `coach/strava.py`/`oura.py`/`garmin.py` field names change before Phase 2 executes)
