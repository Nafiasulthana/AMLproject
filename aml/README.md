# AML Fund Flow Tracking and Investigation Platform

An enterprise banking AML investigation platform featuring real-time simulated banking transactions, multi-stage detection pipeline, Neo4j graph topological analysis, XGBoost machine learning risk classification, and SHAP explainable AI attribution.

## Setup Instructions

### 1. Backend Setup

Create a fresh virtual environment on your operating system and install dependencies:

```bash
cd backend
python -m venv venv

# Activate virtual environment:
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies:
pip install -r requirements.txt
# Alternatively, from root: pip install -r aml/backend/requirements.txt

python run.py
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

For more documentation, see [docs/architecture.md](docs/architecture.md).
