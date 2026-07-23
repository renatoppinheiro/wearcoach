# Requirements Specification — wearcoach Dashboard & Data Science Suite

**Document Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-07-22

---

## 1. Overview & Vision

`wearcoach` is expanding from CLI-only briefings and `.wiki/` knowledge management to include an interactive local web dashboard and data science suite inspired by `stravator`. The system provides real-time coaching, interactive data visualizations, ACWR training load curves, HRV readiness trends, and multi-sport workload classification.

---

## 2. Requirements Index

### 2.1 Core Infrastructure & Web Server
- **[REQ-INF-01] Local Web Server**: Provide a local HTTP web server (`python main.py dashboard`) to host the interactive frontend and REST API.
- **[REQ-INF-02] Snapshot Integration**: Serve data directly from local `data/snapshot-*.json` files without duplicate data stores.

### 2.2 Data Science & Analytics Engine
- **[REQ-DS-01] ACWR & Training Load Model**: Calculate Acute:Chronic Workload Ratio (ACWR), fatigue, and strain scores.
- **[REQ-DS-02] HRV & Readiness Correlation**: Correlate HRV balance and readiness scores against training quality.
- **[REQ-DS-03] CrossFit & Multi-Sport Classifier**: Classify non-running activities (CrossFit, strength, HIIT) and quantify overall strain.
- **[REQ-DS-04] Race & Pace Predictors**: Estimate race completion times and track fitness progress over time.

### 2.3 Dashboard UI & Interactive Charting
- **[REQ-UI-01] Dynamic Chart Block Parser**: Parse ````chart```` JSON blocks in LLM responses and render inline interactive charts.
- **[REQ-UI-02] Real-time Coaching Chat**: Responsive web interface to converse with the coach and view daily briefings.
- **[REQ-UI-03] Visual Analytics Page**: Dedicated views for acute:chronic workload, HRV trends, heart rate zones, and activity logs.

---

## 3. Requirement Traceability & Prioritization

| ID | Title | Priority | Phase Target |
| :--- | :--- | :--- | :--- |
| **REQ-INF-01** | Local Web Server | High | Phase 1 |
| **REQ-INF-02** | Snapshot Integration | High | Phase 1 |
| **REQ-DS-01** | ACWR & Training Load Model | High | Phase 2 |
| **REQ-DS-02** | HRV & Readiness Correlation | High | Phase 2 |
| **REQ-UI-01** | Dynamic Chart Block Parser | High | Phase 3 |
| **REQ-UI-02** | Real-time Coaching Chat & Analytics UI | Medium | Phase 3 |
| **REQ-DS-03** | CrossFit & Multi-Sport Classifier | Medium | Phase 4 |
| **REQ-DS-04** | Race & Pace Predictors | Medium | Phase 4 |
