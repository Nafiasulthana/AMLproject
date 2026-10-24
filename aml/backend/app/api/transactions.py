from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Transaction, User
from app.schemas.schemas import TransactionCreate, TransactionResponse
from app.engine.pipeline import pipeline

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/recent", response_model=List[TransactionResponse])
def get_recent_transactions(limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(limit).all()

@router.post("/process")
def process_manual_transaction(tx: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tx_dict = tx.model_dump()
    result = pipeline.process_transaction(tx_dict, db)
    return result
