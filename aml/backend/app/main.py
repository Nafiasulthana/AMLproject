import os
import sys
import logging
from contextlib import asynccontextmanager

# Add root directory and backend directory to PYTHONPATH
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
database_dir = os.path.join(root_dir, "database")
if database_dir not in sys.path:
    sys.path.insert(0, database_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from ml.explainer import explainer

# API Routers
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.transactions import router as transactions_router
from app.api.alerts import router as alerts_router
from app.api.cases import router as cases_router
from app.api.graph import router as graph_router
from app.api.fund_flow import router as fund_flow_router
from app.api.str_reports import router as str_router
from app.api.simulation import router as simulation_router
from app.api.admin import router as admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Database & Seed Data...")
    init_db()
    logger.info("Initializing ML Model Engine...")
    try:
        explainer.load_model(raise_if_missing=True)
        logger.info("XGBoost AML model engine loaded and ready.")
    except Exception as e:
        logger.error(f"ML Model initialization notice: {e}")
        logger.error("XGBoost model not found. Please train the model first using the training command: python train_model.py")
    yield
    logger.info("Shutting down AML Backend Platform Services.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(transactions_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(graph_router, prefix=settings.API_V1_STR)
app.include_router(fund_flow_router, prefix=settings.API_V1_STR)
app.include_router(str_router, prefix=settings.API_V1_STR)
app.include_router(simulation_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "status": "ONLINE",
        "docs_url": "/docs",
        "version": "1.0.0"
    }
