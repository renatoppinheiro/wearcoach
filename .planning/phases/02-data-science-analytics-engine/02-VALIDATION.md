---
phase: 2
slug: data-science-analytics-engine
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-23
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 (already configured) |
| **Config file** | `pytest.ini` (`pythonpath = .`, `testpaths = tests`) |
| **Quick run command** | `pytest tests/test_analytics.py -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_analytics.py -x`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-XX | 01 | 1 | REQ-DS-01 | — | Daily load aggregation picks the correct fallback tier (sRPE / HR-proxy / duration-only) per activity | unit | `pytest tests/test_analytics.py -k load -x` | ❌ W0 | ⬜ pending |
| 02-01-XX | 01 | 1 | REQ-DS-01 | — | Zero-filling produces a continuous daily series with rest days at 0.0 | unit | `pytest tests/test_analytics.py -k fill_missing -x` | ❌ W0 | ⬜ pending |
| 02-01-XX | 01 | 1 | REQ-DS-01 | — | ACWR returns `insufficient_history: true` before the chronic window is full, never divides by zero | unit | `pytest tests/test_analytics.py -k acwr -x` | ❌ W0 | ⬜ pending |
| 02-01-XX | 01 | 1 | REQ-DS-01 | — | Fitness/fatigue curve (CTL/ATL/TSB) produces monotonically-sane values for a synthetic constant-load series | unit | `pytest tests/test_analytics.py -k fitness_fatigue -x` | ❌ W0 | ⬜ pending |
| 02-02-XX | 02 | 1 | REQ-DS-02 | — | HRV/readiness trend branches correctly on `wellness_source` (Oura contributor score vs. Garmin raw ms) | unit | `pytest tests/test_analytics.py -k hrv -x` | ❌ W0 | ⬜ pending |
| 02-02-XX | 02 | 1 | REQ-DS-02 | — | Correlation function returns `available: false` below `min_points`, valid `r` above it | unit | `pytest tests/test_analytics.py -k correlate -x` | ❌ W0 | ⬜ pending |
| 02-02-XX | 02 | 2 | REQ-DS-01/02 | T-2-01 | `GET /api/analytics` returns 200 with valid JSON given a sufficient snapshot, and a clear error/insufficient-history response given a sparse one; malformed snapshot fields degrade gracefully instead of 500ing | integration | `pytest tests/test_server.py -k analytics -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_analytics.py` — new file, covers REQ-DS-01 and REQ-DS-02 unit behavior above
- [ ] Extend `tests/test_server.py` with analytics-endpoint cases (reuse the existing `TestClient(app)` + `patch("coach.config.DATA_DIR", tmp_path)` pattern already used for `/api/fetch`/`/api/chat`)
- [ ] No framework install needed — pytest/fastapi/TestClient already present and used identically in Phase 1's tests

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
