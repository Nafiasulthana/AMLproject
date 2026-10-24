[README (1).md](https://github.com/user-attachments/files/33900029/README.1.md)
<div align="center">

# AMLSentinel

### Intelligent Graph-Based AML Fund Flow Tracking & Investigation Platform

An end-to-end Anti-Money-Laundering (AML) investigation platform: real-time transaction monitoring, a four-layer hybrid risk engine (rules + behavioural analytics + graph topology + machine learning), SHAP explainability, case management, and FIU-IND-style Suspicious Transaction Report (STR) generation.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-SHAP-EB6B00)
![Database](https://img.shields.io/badge/DB-PostgreSQL%20%7C%20SQLite-336791?logo=postgresql&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-optional-008CC1?logo=neo4j&logoColor=white)

</div>

---

## Table of Contents

1. [Overview](#1-overview)
2. [Key Features](#2-key-features)
3. [System Architecture](#3-system-architecture)
4. [Detection Methodology](#4-detection-methodology)
5. [Machine Learning Model](#5-machine-learning-model)
6. [Tech Stack](#6-tech-stack)
7. [Project Structure](#7-project-structure)
8. [Getting Started](#8-getting-started)
9. [Configuration](#9-configuration)
10. [Using the Platform](#10-using-the-platform)
11. [Roles & Access Control](#11-roles--access-control)
12. [API Reference](#12-api-reference)
13. [Data Model](#13-data-model)
14. [Transaction Simulator](#14-transaction-simulator)
15. [Testing](#15-testing)
16. [Security Notes](#16-security-notes)
17. [Current Scope, Known Limitations & Roadmap](#17-current-scope-known-limitations--roadmap)
18. [Troubleshooting](#18-troubleshooting)
19. [Disclaimer](#19-disclaimer)
20. [Author](#20-author)

---

## 1. Overview

Banks must detect and report suspicious activity such as structuring, layering, round-tripping, smurfing, mule accounts and dormant-account abuse. Rule-only systems generate large volumes of low-value alerts and give investigators little context. **AMLSentinel** addresses this by combining four independent risk signals into a single, explainable **Meta-Risk Score**, then turning high-risk alerts into correlated investigation cases and, finally, reviewable STR documents.

**What the platform does, end to end:**

1. **Ingests** transactions from a built-in real-time simulator or a REST endpoint.
2. **Scores** every transaction with a rule engine, a behavioural engine, a graph engine and an XGBoost + Isolation Forest model.
3. **Explains** each alert with per-feature SHAP attributions, so an analyst can see *why* it fired.
4. **Correlates** alerts for the same customer into a single multi-typology investigation case.
5. **Supports investigation** through an alert queue, interactive account graph, fund-flow tracer and case notes.
6. **Produces** a draft STR as a PDF, with a mandatory human approval step by a Principal Officer.

---

## 2. Key Features

| Area | Capability |
|---|---|
| **Detection pipeline** | Seven-typology rule engine, statistical behaviour profiling, graph-topology analysis and ML scoring, fused into one 0–100 score with CRITICAL / HIGH / MEDIUM / LOW priority bands |
| **Explainable AI** | Exact TreeSHAP feature attributions per alert, rendered as a contribution breakdown in the UI, plus an Isolation Forest anomaly score |
| **Case correlation** | Alerts for the same lead customer are merged into one open case; typologies accumulate and the highest risk score is retained |
| **Investigation workbench** | Alert queue with filters, investigation workspace, interactive account graph (React Flow), multi-hop fund-flow view, case notes and status workflow |
| **STR generation** | Boxed-field regulatory-style PDF (ReportLab) with FIU reference number, narrative, correlated typologies, page numbering, and a Draft → Approved workflow |
| **Real-time simulator** | Multi-threaded generator with 1×–50× speed control and typology injection (structuring, layering, round-trip, smurfing, dormant, profile mismatch) |
| **Role-based access** | JWT authentication with four roles (Admin, Investigator, Principal Officer, Compliance Analyst) enforced on the API |
| **Admin tooling** | System health, live rule weight tuning, user listing and on-demand ML retraining |
| **Resilient by design** | Automatic fallback from PostgreSQL to SQLite and from Neo4j to an in-memory graph engine, so the platform runs with zero external services |

---

## 3. System Architecture

```mermaid
flowchart TB
    subgraph Client["Frontend (React 18 + TypeScript + Vite)"]
        UI["Dashboard · Alert Queue · Investigation · Graph · Fund Flow · Cases · STR · Simulator · Admin"]
    end

    subgraph API["Backend (FastAPI)"]
        R["REST API /api/v1 + JWT + RBAC"]
        P["AML Pipeline"]
        SIM["Transaction Simulator (background thread)"]
    end

    subgraph Engines["Detection engines"]
        RE["Rule Engine"]
        BE["Behaviour Engine"]
        GE["Graph Engine"]
        ML["XGBoost + IsolationForest + SHAP"]
        RK["Hybrid Meta-Risk Engine"]
        CE["Correlation Engine"]
    end

    subgraph Storage["Storage"]
        DB[("PostgreSQL, or SQLite fallback")]
        G[("In-memory graph, Neo4j optional")]
        M[["Model artifacts (JSON / PKL)"]]
        PDF[["STR PDFs"]]
    end

    UI -- "HTTP /api (Vite proxy)" --> R
    SIM --> P
    R --> P
    P --> RE & BE & GE
    RE & BE & GE --> RK
    ML --> RK
    M --> ML
    GE --- G
    RK --> CE
    CE --> DB
    R --> DB
    R --> PDF
```

### Transaction processing pipeline

```mermaid
flowchart LR
    A["Transaction<br/>(simulator or API)"] --> B["Schema validation<br/>(Pydantic)"]
    B --> C["Rule Engine"]
    B --> D["Behaviour Engine"]
    B --> E["Graph Engine"]
    C --> F["Feature assembly<br/>(17 ML features)"]
    D --> F
    E --> F
    F --> G["XGBoost + Isolation Forest<br/>+ SHAP"]
    C --> H["Hybrid Meta-Risk Score"]
    D --> H
    E --> H
    G --> H
    H -->|"score >= 35"| I["Alert"]
    I --> J["Correlation Engine"]
    J --> K["Investigation Case"]
    K --> L["STR draft → Officer approval → PDF"]
```

The orchestration lives in [`backend/app/engine/pipeline.py`](backend/app/engine/pipeline.py). For a deeper walkthrough see [`docs/architecture.md`](docs/architecture.md).

---

## 4. Detection Methodology

Each layer produces a 0–100 risk score. The scores are combined as:

```
Meta-Risk = 0.30 × Rule  +  0.25 × Behaviour  +  0.25 × Graph  +  0.20 × ML
```

| Meta-Risk Score | Priority | Outcome |
|---|---|---|
| ≥ 80 | **CRITICAL** | Alert + case |
| ≥ 60 | **HIGH** | Alert + case |
| ≥ 35 | **MEDIUM** | Alert + case |
| < 35 | LOW | Transaction recorded, no alert |

### 4.1 Rule Engine

Weights below are the seeded defaults and can be adjusted at runtime through the Admin API.

| Rule | Typology | Trigger in the engine | Default weight |
|---|---|---|---|
| `R_STRUCTURING` | Structuring / CTR avoidance | Amount in **₹480,000 – ₹499,999** (just under ₹500,000) | 35 |
| `R_DORMANT` | Dormant-account spike | Sender account status is `DORMANT` and amount > ₹50,000 | 25 |
| `R_PROFILE_MISMATCH` | Income profile mismatch | Amount exceeds **3.5×** the customer's declared monthly income | 20 |
| `R_LAYERING` | Layering | Transaction carries a `LAYERING` typology hint | 30 |
| `R_MONEY_MULE` | Money-mule pass-through | Transaction carries a `MONEY_MULE` typology hint | 35 |
| `R_ROUNDTRIP` | Round tripping | Transaction carries a `ROUND_TRIP` typology hint | 40 |
| `R_SMURFING` | Smurfing | Transaction carries a `SMURFING` typology hint | 30 |

> **How typology hints work.** Structuring, dormant and profile-mismatch rules evaluate each transaction on its own data. Layering, mule, round-trip and smurfing rules are driven by the optional `flagged_typology` field supplied by the transaction source (the simulator, or the API caller). Behaviour and graph checks always run independently of any hint.

The combined rule score is capped at 100.

### 4.2 Behaviour Intelligence Engine

Compares each transaction against the customer's stored behaviour profile (average amount, historical maximum, preferred channels):

- **Amount z-score** against the profile mean (standard deviation estimated as 40% of the mean, minimum 1,000). A z-score above 3 adds up to 45 points.
- **Historical-maximum breach**: amount more than 2× the largest previous single transaction adds 30 points.
- **Channel anomaly**: use of a channel outside the customer's preferred set adds 15 points.

### 4.3 Graph Intelligence Engine

Every transaction is added to an account-to-account graph and metrics are recomputed for the sender and receiver:

- **Fan-in aggregation**: receiver with ≥ 4 distinct senders adds 30 points (smurfing / mule collection signature).
- **Low money retention**: retention ratio < 15% with more than ₹100,000 moved out adds 35 points (pass-through / layering signature).
- **Round-trip cycle**: funds returning to the originating account via a reciprocal flow adds 40 points.

Also computed and passed to the ML model: degree centrality, a degree-derived betweenness approximation, money-retention ratio and hop count.

### 4.4 Hybrid ML + Explainability Layer

An XGBoost classifier (17 features) produces a suspicion probability and an Isolation Forest provides an unsupervised anomaly score. The ML risk component is:

```
ML Risk = 0.7 × XGBoost probability + 0.3 × Isolation-Forest anomaly score
```

SHAP's `TreeExplainer` then decomposes the XGBoost prediction into per-feature contributions (in percentage points). Each contribution is mapped to a readable label and an impact level, and stored with the alert so the UI can display it later without recomputation.

### 4.5 Cross-Typology Correlation Engine

When an alert is raised, the engine looks for an existing open case (`OPEN`, `IN_REVIEW`, `ESCALATED`) for the same lead customer. If one exists, the new typology is appended, the case keeps the highest meta-risk score seen, and it is promoted to `CRITICAL` when that score reaches 80. Otherwise a new case is opened automatically.

---

## 5. Machine Learning Model

### Dataset

The model is trained on a **synthetic** dataset of 2,000 transactions (`data/phase1_aml_dataset.csv`, seed 42, 14.8% suspicious). The generator deliberately avoids label leakage: features are sampled without knowledge of the label, rule flags are *derived* from those features, and the label is drawn from a noisy Bernoulli of a weighted risk score. This keeps class overlap realistic, so metrics are meaningful rather than inflated.

### Training procedure ([`database/ml/train_model.py`](database/ml/train_model.py))

1. **Feature engineering**: 11 raw features plus 6 engineered ones (`high_risk_flag_count`, `risk_flag_any`, `z_score_retention_ratio`, `unretained_amount`, `graph_activity_score`, `velocity_pass_through`), 17 in total.
2. **Class imbalance**: weighted XGBoost (`scale_pos_weight` ≈ 5.75); SMOTE is evaluated for comparison when `imbalanced-learn` is installed.
3. **Hyper-parameter search**: 972 combinations scored by 5-fold stratified cross-validation (selection score = 0.7·F1 + 0.3·PR-AUC).
4. **Threshold optimisation**: out-of-fold probabilities are swept over 0.15–0.50, maximising `0.6·recall + 0.4·F1 − 0.5·max(0, FPR − 0.30)`. This is a deliberately **recall-first** objective, since a missed suspicious transaction is costlier than an extra alert to triage. The selected threshold is **0.25**.
5. **Unsupervised layer**: Isolation Forest (200 trees, contamination 0.15).
6. **Artefacts** written to `database/ml/models/` and 7 evaluation plots to `reports/figures/`.

Selected hyper-parameters: `n_estimators=120`, `max_depth=5`, `learning_rate=0.03`, `min_child_weight=2`, `subsample=0.8`, `colsample_bytree=0.8`, `reg_alpha=1.0`, `reg_lambda=1.0`.

### Results (held-out test set: 400 transactions, 59 suspicious)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| Logistic Regression (balanced) | 0.7425 | 0.3406 | 0.7966 | 0.4772 | **0.8617** | **0.5455** |
| Random Forest | 0.8650 | 0.6000 | 0.2542 | 0.3571 | 0.8336 | 0.4885 |
| LightGBM | 0.8750 | 0.5957 | 0.4746 | 0.5283 | 0.8231 | 0.4926 |
| CatBoost | 0.8400 | 0.4658 | 0.5763 | 0.5152 | 0.8383 | 0.4795 |
| XGBoost baseline (6 raw features, threshold 0.50) | 0.7750 | 0.3524 | 0.6271 | 0.4512 | 0.8030 | 0.4359 |
| **XGBoost tuned (17 features, threshold 0.25)** | 0.7075 | 0.3117 | **0.8136** | 0.4507 | 0.8414 | 0.5044 |

**Reading the results honestly:**

- The tuned XGBoost model has the **highest recall (81.4%)** of every candidate and cuts missed suspicious transactions from **22 to 11** versus the baseline, at the cost of 38 additional false positives. Precision is about 31% at this operating point, which is expected for a recall-first triage model.
- On this synthetic data a scaled logistic regression is competitive on the ranking metrics (ROC-AUC, PR-AUC). XGBoost is the model wired into the pipeline because it supports exact TreeSHAP explanations and is tuned for the recall-oriented operating point.
- 5-fold CV on the training split (threshold 0.50): F1 0.540 ± 0.049, ROC-AUC 0.872 ± 0.030, recall 0.747 ± 0.084, PR-AUC 0.559 ± 0.070.
- Confusion matrix at threshold 0.25: **TN 235 · FP 106 · FN 11 · TP 48**. Brier score 0.128, log-loss 0.391.
- Most influential features by gain: `z_score_amount` (0.30), `high_risk_flag_count` (0.13), `risk_flag_any` (0.12), `z_score_retention_ratio` (0.09), `layering_flag` (0.05).
- **These figures come from synthetic data** and demonstrate the methodology; they are not a claim about production performance.

<table>
  <tr>
    <td align="center"><img src="reports/figures/confusion_matrix.png" width="380" alt="Confusion matrix"/><br/><sub>Confusion matrix (threshold 0.25)</sub></td>
    <td align="center"><img src="reports/figures/roc_curve.png" width="380" alt="ROC curve"/><br/><sub>ROC curve</sub></td>
  </tr>
  <tr>
    <td align="center"><img src="reports/figures/precision_recall_curve.png" width="380" alt="Precision-recall curve"/><br/><sub>Precision–recall curve</sub></td>
    <td align="center"><img src="reports/figures/feature_importance.png" width="380" alt="Feature importance"/><br/><sub>Gain-based feature importance</sub></td>
  </tr>
</table>

Threshold-sweep plots (`threshold_vs_recall.png`, `threshold_vs_precision.png`, `threshold_vs_f1.png`) are also in [`reports/figures/`](reports/figures/).

---

## 6. Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python, FastAPI, Uvicorn, SQLAlchemy 2, Pydantic 2, PyJWT |
| **Machine learning** | XGBoost, scikit-learn (Isolation Forest, Logistic Regression, Random Forest), SHAP, pandas, NumPy; optional LightGBM, CatBoost, imbalanced-learn |
| **Databases** | PostgreSQL (primary) with automatic SQLite fallback; Neo4j driver with in-memory graph fallback |
| **Reporting** | ReportLab (PDF generation) |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router 6, React Flow (graph), Recharts (charts), Axios, Lucide icons |

---

## 7. Project Structure

```
aml/
├── backend/
│   ├── run.py                    # Uvicorn entry point (port 8000, hot reload)
│   ├── requirements.txt
│   └── app/
│       ├── main.py               # FastAPI app, CORS, router registration, startup lifecycle
│       ├── api/                  # auth · dashboard · transactions · alerts · cases · graph
│       │                         # fund_flow · str_reports · simulation · admin
│       ├── core/                 # config · database (+seed data) · security (JWT) · RBAC · graph client
│       ├── engine/               # rule · behaviour · graph · risk (hybrid) · correlation · pipeline
│       ├── models/               # SQLAlchemy ORM models
│       └── schemas/              # Pydantic request / response schemas
├── frontend/
│   ├── vite.config.ts            # Dev server :5173, proxies /api → :8000
│   └── src/
│       ├── pages/                # Dashboard, Alerts, Investigation, Graph, Fund Flow, Cases, STR, Simulator, Admin, Login
│       ├── components/           # layout, dashboard, graph (React Flow), SHAP modal
│       ├── context/              # AuthContext (JWT session + demo role switcher)
│       └── services/api.ts       # Axios client with bearer-token interceptor
├── database/
│   ├── schema.sql                # Reference DDL for all tables
│   └── ml/
│       ├── train_model.py        # Training, tuning, evaluation, plots
│       ├── explainer.py          # Inference, Isolation Forest blend, SHAP
│       ├── synthetic_generator.py
│       ├── test_explainer_sanity.py
│       └── models/               # xgboost_aml.json · isolation_forest.pkl · metadata JSON
├── simulation/simulator.py       # Real-time transaction generator
├── neo4j/schema.cypher           # Constraints, indexes and a graph query library
├── data/phase1_aml_dataset.csv   # Synthetic training data (2,000 rows)
├── reports/figures/              # Evaluation plots (STR PDFs are also written under reports/)
├── docs/architecture.md
├── tests/                        # ML lifecycle + STR download tests
└── train_model.py                # CLI shortcut to (re)train the model
```

> `ml/` (repo root) and `database/ml/` are merged into a single `ml` namespace package through the `sys.path` set-up in `backend/app/main.py` and `train_model.py`. Run the backend from `backend/` and training from the repo root, as shown below.

---

## 8. Getting Started

### Prerequisites

- **Python 3.10+** (verified on 3.12)
- **Node.js 18+** and npm (verified on Node 22)
- *Optional:* PostgreSQL and/or Neo4j. **Neither is required.** The platform falls back to SQLite and an in-memory graph automatically.

### 1. Clone

```bash
git clone https://github.com/<your-username>/<repository>.git
cd <repository>/aml        # the folder that contains backend/ and frontend/
```

### 2. Start the backend

```bash
cd backend
python -m venv venv

# Activate the virtual environment
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows (CMD / PowerShell)

pip install -r requirements.txt
python run.py
```

The API is now live at **http://localhost:8000**, with interactive Swagger docs at **http://localhost:8000/docs**.

On first start the backend creates the database tables and seeds 4 users, 7 customers and accounts, 7 AML rules and behaviour profiles. A pre-trained model ships in `database/ml/models/`, so no training step is needed.

You will see log warnings that PostgreSQL and/or Neo4j are unavailable. **This is expected** and means the SQLite and in-memory fallbacks are active.

### 3. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** and sign in with a demo account (see below). The Vite dev server proxies `/api` to the backend on port 8000.

### 4. Try it

1. Sign in as `investigator` / `inv123`.
2. Open **Transaction Simulator**, choose a typology (or `MIXED`) and speed, then press **Start**.
3. Watch the **Dashboard** and **Alert Queue** populate, then open an alert to see its SHAP breakdown.

### Demo accounts

| Role | Username | Password |
|---|---|---|
| AML Investigator | `investigator` | `inv123` |
| Principal Officer | `officer` | `officer123` |
| System Admin | `admin` | `admin123` |
| Compliance Analyst | `analyst` | `analyst123` |

The login page offers one-click role buttons and the header has a role switcher for demos. **These credentials are for local demonstration only.** See [Security Notes](#16-security-notes).

### Re-training the model (optional)

```bash
# from the repository root (the folder containing train_model.py)
python train_model.py
```

This regenerates `database/ml/models/*`, `reports/figures/*` and the metadata file. The hyper-parameter search covers 972 configurations with 5-fold cross-validation, so **expect several minutes** depending on CPU cores. Admins can also trigger it from the Admin Panel, which runs synchronously inside the request.

### Production build of the frontend

```bash
cd frontend
npm run build        # outputs static files to frontend/dist
```

Serve `dist/` from any static host and forward `/api` to the backend (for example with an Nginx reverse proxy).

---

## 9. Configuration

Settings are read from **environment variables** (a `.env` file is *not* loaded automatically, so export variables in your shell or process manager).

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | built-in development key | JWT signing key and password-hash salt source. **Always override outside local use** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720` (12 h) | JWT lifetime |
| `DATABASE_URL` | built from `POSTGRES_*` | Full SQLAlchemy URL; overrides the individual settings below |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | `postgres` / `postgres` | PostgreSQL credentials |
| `POSTGRES_SERVER` / `POSTGRES_PORT` / `POSTGRES_DB` | `localhost` / `5432` / `aml_db` | PostgreSQL location |
| `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` | `bolt://localhost:7687` / `neo4j` / `password` | Neo4j connection (optional) |

**Using PostgreSQL**

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/aml_db"
python run.py
```

If the connection fails, the backend logs a warning and silently continues on SQLite (`backend/aml_sqlite.db`). Check the startup log or **Admin → System Health** to confirm which database is active. Reference DDL for every table is in [`database/schema.sql`](database/schema.sql); tables are also created automatically on startup.

---

## 10. Using the Platform

A typical investigation follows this path:

| Step | Page | What happens |
|---|---|---|
| 1 | **Transaction Simulator** | Start the live feed; choose speed (1×–50×) and a typology to inject |
| 2 | **Dashboard** | KPI tiles, risk-level distribution, typology breakdown, volume trend, recent alerts |
| 3 | **Alert Queue** | Filter by priority and status; open **SHAP** to see which features drove the score |
| 4 | **Investigation Workspace** | Review an alert with its transaction, customer profile and behaviour profile alongside the account graph |
| 5 | **Graph Explorer** | Interactive account network, with accounts coloured by KYC risk category |
| 6 | **Fund Flow** | Trace money between a source and sink account across intermediate hops, with per-hop amount, channel and mule indicators |
| 7 | **Case Management** | Review correlated cases, add investigator notes, change status or priority |
| 8 | **STR Reports** | Generate a draft STR from a case, have a Principal Officer approve it, download the PDF |
| 9 | **Admin Panel** | Check service health, tune rule weights, review users, retrain the model |

---

## 11. Roles & Access Control

Authentication uses JWT bearer tokens. Role checks enforced **by the API**:

| Capability | Admin | Officer | Investigator | Analyst |
|---|:-:|:-:|:-:|:-:|
| Dashboards, alerts, cases, graph, simulator (authenticated access) | ✓ | ✓ | ✓ | ✓ |
| View AML rules | ✓ | ✓ | ✓ | |
| Generate STR draft | ✓ | ✓ | ✓ | |
| **Approve STR** | ✓ | ✓ | | |
| System health | ✓ | ✓ | | |
| Edit rule weights, list users, retrain ML | ✓ | | | |

The frontend additionally hides navigation entries that a role does not need (for example the Analyst role sees a read-oriented subset).

---

## 12. API Reference

Base path: `/api/v1`. All endpoints except login require `Authorization: Bearer <token>`. Full interactive documentation is generated at `/docs`.

| Group | Method & Path | Description |
|---|---|---|
| **Auth** | `POST /auth/login` | Exchange username and password for a JWT |
| | `GET /auth/me` | Current user |
| **Dashboard** | `GET /dashboard/metrics` | KPIs, risk and typology distributions, graph stats, recent alerts |
| **Transactions** | `GET /transactions/recent` | Latest transactions (`limit`) |
| | `POST /transactions/process` | Run a transaction through the full detection pipeline |
| **Alerts** | `GET /alerts` | Alert queue (`priority`, `status`, `limit`) |
| | `GET /alerts/{alert_id}` | Alert with transaction, customer, behaviour profile and SHAP data |
| | `PUT /alerts/{alert_id}/status` | Update status or assignee |
| **Cases** | `GET /cases` | List cases (`status`, `priority`) |
| | `GET /cases/{case_id}` | Case with lead customer, notes and evidence |
| | `PUT /cases/{case_id}` | Update status, priority, investigator, summary |
| | `POST /cases/{case_id}/notes` | Add an investigator note |
| **Graph** | `GET /graph/topology` | Nodes and edges for visualisation |
| | `GET /graph/expand/{account_number}` | Graph metrics for one account |
| **Fund flow** | `GET /fund-flow/trace` | Multi-hop trace (`source_acc`, `sink_acc`) |
| **STR** | `GET /str` | List reports |
| | `POST /str/generate` | Create a draft STR and PDF from a case |
| | `POST /str/{report_id}/approve` | Approve (Officer / Admin) |
| | `GET /str/{report_id}/download` | Download the PDF |
| **Simulation** | `GET /simulation/status` | Running state, speed, typology, recent transactions |
| | `POST /simulation/start` · `pause` · `resume` · `stop` | Control the generator |
| | `POST /simulation/configure` | Set `speed_multiplier` (1–50) and `selected_typology` |
| **Admin** | `GET /admin/health` | Service status |
| | `GET /admin/rules` · `PUT /admin/rules/{rule_code}` | View and update rules (`threshold`, `weight`, `enabled`) |
| | `POST /admin/retrain-ml` | Retrain and hot-reload the model |
| | `GET /admin/users` | List users |

**Example: score a transaction from the command line**

```bash
BASE=http://localhost:8000/api/v1

TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"investigator","password":"inv123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST $BASE/transactions/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
        "sender_account": "ACC_1001",
        "receiver_account": "ACC_1003",
        "amount": 495000,
        "channel": "CASH_DEPOSIT",
        "flagged_typology": "STRUCTURING"
      }'
```

The response includes `meta_risk_score`, `priority`, `alert_generated`, `alert_id`, `case_id`, the triggered rules, behaviour and graph details, and the SHAP explanation (abridged):

```json
{
  "tx_id": "TX_74A8CFEAE2",
  "meta_risk_score": 36.54,
  "priority": "MEDIUM",
  "alert_generated": true,
  "alert_id": "ALT_5B9B2DE5",
  "case_id": "CASE_CBBB66C6",
  "rule_details": { "triggered_rules": [{ "rule_code": "R_STRUCTURING", "weight": 35.0 }] },
  "shap_explanation": { "xgb_probability": 67.5, "anomaly_score": 76.6, "shap_values": ["..."] }
}
```

*(Values are illustrative; scores depend on current graph state and model.)*

---

## 13. Data Model

Thirteen relational tables (see [`database/schema.sql`](database/schema.sql) and `backend/app/models/models.py`):

| Table | Purpose |
|---|---|
| `roles`, `users` | Authentication and RBAC |
| `customers`, `accounts` | KYC data, declared income and expected volume, account status and balance |
| `transactions` | Every processed transaction with channel, device, IP and typology tag |
| `behaviour_profiles` | Per-customer baselines used by the behaviour engine |
| `aml_rules` | Rule catalogue: code, typology, threshold, weight, enabled flag |
| `alerts` | Component scores (rule, behaviour, graph, ML), meta score, priority, status, serialized SHAP explanation |
| `cases`, `case_notes`, `case_evidence` | Investigation cases, notes and evidence records |
| `str_reports` | Draft/approved STRs, FIU reference number, PDF path, approver |
| `audit_logs` | Schema provided for audit trails (see roadmap) |

Graph data is held by the in-memory engine as `(account) –[transaction]→ (account)` edges. [`neo4j/schema.cypher`](neo4j/schema.cypher) defines the equivalent Neo4j constraints and indexes, along with a library of Cypher queries (fan-in/out and retention, 2–5 hop cycle detection, smurfing aggregation, multi-hop source-to-sink tracing).

---

## 14. Transaction Simulator

[`simulation/simulator.py`](simulation/simulator.py) runs in a background thread and pushes generated transactions through the same pipeline as the REST API.

- **Speed:** 1×–50× (interval of `2.5 / speed` seconds, minimum 0.1 s).
- **Typologies:** `MIXED` (≈40% normal, remainder spread across attack patterns), `STRUCTURING`, `LAYERING`, `ROUND_TRIP`, `DORMANT`, `SMURFING`, `PROFILE_MISMATCH`, or normal traffic.
- **Channels:** UPI, NEFT, RTGS, ATM, cash deposit, merchant.
- **Controls:** start, pause, resume, stop, reconfigure, all available from the UI or the API.

---

## 15. Testing

```bash
# from the repository root, with the backend virtual environment active
pip install httpx                                   # required by FastAPI's TestClient

python -m unittest tests.test_str_pdf_download      # login → generate STR → 401 without token → PDF download
python database/ml/test_explainer_sanity.py         # model loads; suspicious ≫ normal; SHAP values are real
python -m unittest tests.test_ml_lifecycle          # model load/failure paths, no retrain on startup,
                                                    # feature-order consistency, reproducibility
```

> `tests.test_ml_lifecycle` **retrains the model** (several times, including a reproducibility check), so it is slow by design. Running tests from the repository root creates a local SQLite file and STR PDFs in the working directory.

---

## 16. Security Notes

This is a demonstration platform. Before any real deployment:

- **Replace the demo credentials** and set a strong `SECRET_KEY` (the shipped default is public).
- **Upgrade password hashing.** Passwords are currently stored as a salted SHA-256 digest for zero-dependency local use. `passlib[bcrypt]` is already in the requirements and should be adopted.
- **Restrict CORS.** The API currently allows all origins for local development.
- **Terminate TLS** in front of the API and serve the frontend over HTTPS.
- **Do not expose** the simulator and admin endpoints publicly. Several non-admin endpoints require authentication but not a specific role.

---

## 17. Current Scope, Known Limitations & Roadmap

AMLSentinel is a complete, working reference implementation. The points below describe where the current build deliberately simplifies, and what comes next.

**Current scope**

- **Synthetic data.** Training data, customers and traffic are simulated. Model metrics demonstrate method, not production accuracy.
- **Graph analytics run in-process.** The graph engine is a lightweight in-memory implementation (degree, fan-in/out, retention, reciprocal-flow detection, degree-based betweenness approximation). It resets on restart. Neo4j connectivity is detected and reported, and the Cypher query library is provided, but scoring does not yet execute those queries.
- **Fund-flow trace is illustrative.** The multi-hop view is built from a templated three-hop chain anchored on the most recent matching transaction, rather than a path search over the transaction graph.
- **Typology hints.** Layering, mule, round-trip and smurfing rules depend on the `flagged_typology` hint from the transaction source.
- **Dashboard demo figures.** Some KPI tiles add fixed baseline offsets and the volume trend is sample data.
- **Rule administration.** Rule *weights* are tunable at runtime. Stored *thresholds* are not yet read by the engine (they are fixed in code), and disabling a rule reverts it to its default weight rather than suppressing it.
- **STR output** is a draft document with a generated reference number. No submission to FIU-IND / FINnet is performed.

**Roadmap**

- [ ] Execute graph metrics and cycle detection in Neo4j using the drafted Cypher queries
- [ ] Replace the templated fund-flow trace with true source-to-sink path search
- [ ] Enforce rule enable/disable and thresholds from the database
- [ ] bcrypt password hashing, per-endpoint role enforcement, restricted CORS
- [ ] Populate `audit_logs` and add evidence attachments to cases
- [ ] Asynchronous model retraining job with progress reporting
- [ ] Pin dependency versions, add CI, and containerise with Docker Compose (app + PostgreSQL + Neo4j)
- [ ] Validate on labelled real-world or benchmark AML data with drift monitoring

---

## 18. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `ModuleNotFoundError: No module named 'matplotlib'` (or `seaborn`) on backend start | The training module is imported at startup and needs plotting libraries. Run `pip install matplotlib seaborn` (they are included in the updated `requirements.txt`) |
| `XGBoost model not found … train the model first` | Model files are missing from `database/ml/models/`. From the repo root run `python train_model.py` |
| `InconsistentVersionWarning` about `IsolationForest` | The bundled Isolation Forest pickle was saved with an older scikit-learn. It still loads, but you can regenerate it for your environment with `python train_model.py` |
| Log says PostgreSQL failed and SQLite is used | Expected when PostgreSQL is not running or the driver is not found. Provide an explicit `DATABASE_URL` with the `postgresql+psycopg2://` prefix, and verify with Admin → System Health |
| Neo4j connection warning at startup | Expected without Neo4j. The in-memory graph engine is used |
| Frontend shows network errors / 401 | Ensure the backend is running on port 8000 and sign in again (tokens expire after 12 hours) |
| `npm run dev` fails after copying the project between OSes | Delete `frontend/node_modules` and run `npm install` again (native binaries are platform-specific) |
| `TestClient` import error when running tests | `pip install httpx` |

---

## 19. Disclaimer

AMLSentinel is an educational and portfolio project built on **synthetic data**. The STR layout, form number and FIU reference are illustrative and are **not** an official FIU-IND filing format; the platform does not file reports with any regulator. It must not be used as the sole basis for real compliance or enforcement decisions.

---

## 20. Author

**Nafia** — Final Year Project: graph-based AML fund-flow tracking and investigation.

<!-- Add: GitHub · LinkedIn · email. Add screenshots under docs/images/ and embed them in Section 10. -->
