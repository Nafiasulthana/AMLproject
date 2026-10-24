# Intelligent Graph-Based AML Fund Flow Tracking and Investigation Platform

## Overview
This platform is a Final Year Project designed for enterprise banking AML investigation teams. It features real-time simulated banking transactions, multi-stage detection pipeline, Neo4j graph topological analysis, XGBoost machine learning risk classification, SHAP explainable AI attribution, and an interactive React Flow investigation workbench.

## Quick Start Guide

### 1. Backend Server Setup & Launch
Navigate to the `backend/` directory, create a fresh virtual environment for your operating system, and install dependencies:
```bash
cd backend
python -m venv venv

# Activate virtual environment:
# On Linux / macOS:
source venv/bin/activate
# On Windows (PowerShell / CMD):
venv\Scripts\activate

# Install dependencies and start the backend:
pip install -r requirements.txt
python run.py
```
*(Alternatively, from repository root run `pip install -r aml/backend/requirements.txt` inside your virtual environment)*

The FastAPI backend will run on `http://localhost:8000`. API Swagger documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Launch
Navigate to the `frontend/` directory:
```bash
cd frontend
npm install
npm run dev
```

The React Vite application will open at `http://localhost:5173`.

---

## User Credentials & Roles

| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| **AML Investigator** | `investigator` | `inv123` | Alert triaging, graph visualization, fund flow tracing, case updates |
| **System Admin** | `admin` | `admin123` | System health, rule threshold tuning, ML retraining, user administration |
| **Principal Officer** | `officer` | `officer123` | Case escalation review, STR final approval and PDF generation |
| **Compliance Analyst** | `analyst` | `analyst123` | Read-only dashboards, metric review, analytics |

---

## Engine Architecture Pipeline

1. **Validation Engine**: Schema checking & transaction parameter normalization.
2. **Rule Engine**: 12+ AML rules (Structuring, Layering, Round Tripping, Dormant Reactivation, Smurfing, Profile Mismatch).
3. **Behaviour Intelligence Engine**: Z-Score statistical deviation against historical customer profile (avg amount, volume, timing, channels).
4. **Graph Intelligence Engine**: Neo4j Cypher algorithms (Degree Centrality, PageRank, Money Retention Ratio, Circular Hop Trace).
5. **Hybrid Meta-Risk Engine**: Score = `(Rule * 0.30) + (Behaviour * 0.25) + (Graph * 0.25) + (ML * 0.20)`.
6. **XGBoost + SHAP Explainability Engine**: Calculates feature attribution waterfall per transaction alert.
7. **Cross-Typology Correlation Engine**: Groups correlated alerts across customer network into unified High-Confidence Cases.
8. **Real-Time Transaction Simulator**: Multi-threaded generator with speed multiplier (1x-50x) and typology injection controls.
