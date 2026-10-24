import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import RequireRole
from app.models.models import AMLRule, User
from app.core.neo4j_client import is_neo4j_connected
from ml.train_model import train_and_save_model
from ml.explainer import explainer

router = APIRouter(prefix="/admin", tags=["Admin Panel"])

@router.get("/health")
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["ADMIN", "OFFICER"]))
):
    model_path = os.path.join(explainer.model_dir, "xgboost_aml.json")
    model_exists = os.path.exists(model_path) and explainer.model is not None
    return {
        "status": "HEALTHY",
        "services": {
            "relational_database": "ONLINE",
            "neo4j_graph_database": "ONLINE (LIVE)" if is_neo4j_connected else "ONLINE (IN-MEMORY ENGINE ACTIVE)",
            "ml_model_engine": "READY (XGBoost Loaded)" if model_exists else "PENDING_TRAIN",
            "transaction_simulator": "READY"
        }
    }

@router.get("/rules")
def get_aml_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["ADMIN", "OFFICER", "INVESTIGATOR"]))
):
    return db.query(AMLRule).all()

@router.put("/rules/{rule_code}")
def update_aml_rule(
    rule_code: str,
    threshold: float,
    weight: float,
    enabled: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(RequireRole(["ADMIN"]))
):
    rule = db.query(AMLRule).filter(AMLRule.rule_code == rule_code).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.threshold_value = threshold
    rule.risk_weight = weight
    rule.is_enabled = enabled
    db.commit()
    return {"message": "AML Rule updated successfully", "rule_code": rule_code}

@router.post("/retrain-ml")
def retrain_ml_model(current_user: User = Depends(RequireRole(["ADMIN"]))):
    try:
        model, feature_cols, metrics = train_and_save_model()
        explainer.load_model()
        return {
            "message": "XGBoost AML model retrained successfully",
            "features": feature_cols,
            "metrics": metrics
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Model retraining failed: {ex}")

@router.get("/users")
def get_system_users(db: Session = Depends(get_db), current_user: User = Depends(RequireRole(["ADMIN"]))):
    users = db.query(User).all()
    return [
        {
            "user_id": u.user_id,
            "username": u.username,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role_id,
            "is_active": u.is_active
        } for u in users
    ]
