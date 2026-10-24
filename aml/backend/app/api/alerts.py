import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Alert, Transaction, Customer, User, CustomerBehaviourProfile
from app.schemas.schemas import AlertResponse, AlertUpdateStatus

router = APIRouter(prefix="/alerts", tags=["Alerts Queue"])

@router.get("", response_model=List[AlertResponse])
def get_alerts_queue(
    priority: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert)
    if priority and priority != "ALL":
        query = query.filter(Alert.priority == priority)
    if status and status != "ALL":
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()

@router.get("/{alert_id}")
def get_alert_detail(alert_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    tx = db.query(Transaction).filter(Transaction.tx_id == alert.tx_id).first()
    customer = db.query(Customer).filter(Customer.customer_id == alert.customer_id).first()
    profile = db.query(CustomerBehaviourProfile).filter(CustomerBehaviourProfile.customer_id == alert.customer_id).first()

    shap_data = json.loads(alert.shap_explanation) if alert.shap_explanation else {}

    return {
        "alert": alert,
        "transaction": tx,
        "customer": customer,
        "behaviour_profile": profile,
        "shap_explanation": shap_data
    }

@router.put("/{alert_id}/status")
def update_alert_status(
    alert_id: str,
    payload: AlertUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = payload.status
    if payload.assigned_to:
        alert.assigned_to = payload.assigned_to
    elif not alert.assigned_to:
        alert.assigned_to = current_user.user_id

    db.commit()
    return {"message": "Alert status updated", "alert_id": alert_id, "status": alert.status}
