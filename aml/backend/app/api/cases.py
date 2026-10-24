import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Case, CaseNote, CaseEvidence, Customer, User
from app.schemas.schemas import CaseResponse, CaseUpdate, CaseNoteCreate, CaseNoteResponse

router = APIRouter(prefix="/cases", tags=["Case Management"])

@router.get("", response_model=List[CaseResponse])
def get_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Case)
    if status and status != "ALL":
        query = query.filter(Case.status == status)
    if priority and priority != "ALL":
        query = query.filter(Case.priority == priority)
    return query.order_by(Case.updated_at.desc()).all()

@router.get("/{case_id}")
def get_case_detail(case_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case_obj = db.query(Case).filter(Case.case_id == case_id).first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found")
    
    lead_customer = db.query(Customer).filter(Customer.customer_id == case_obj.lead_customer_id).first()
    notes = db.query(CaseNote).filter(CaseNote.case_id == case_id).order_by(CaseNote.created_at.desc()).all()
    evidence = db.query(CaseEvidence).filter(CaseEvidence.case_id == case_id).order_by(CaseEvidence.uploaded_at.desc()).all()

    return {
        "case": case_obj,
        "lead_customer": lead_customer,
        "notes": notes,
        "evidence": evidence
    }

@router.put("/{case_id}")
def update_case(
    case_id: str,
    update_data: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case_obj = db.query(Case).filter(Case.case_id == case_id).first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if update_data.status:
        case_obj.status = update_data.status
    if update_data.priority:
        case_obj.priority = update_data.priority
    if update_data.assigned_investigator:
        case_obj.assigned_investigator = update_data.assigned_investigator
    if update_data.summary:
        case_obj.summary = update_data.summary

    case_obj.updated_at = datetime.utcnow()
    db.commit()
    return case_obj

@router.post("/{case_id}/notes", response_model=CaseNoteResponse)
def add_case_note(
    case_id: str,
    note: CaseNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case_obj = db.query(Case).filter(Case.case_id == case_id).first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Case not found")

    new_note = CaseNote(
        note_id=f"NOTE_{uuid.uuid4().hex[:8].upper()}",
        case_id=case_id,
        author_id=current_user.user_id,
        author_name=current_user.full_name,
        note_text=note.note_text,
        created_at=datetime.utcnow()
    )
    db.add(new_note)
    case_obj.updated_at = datetime.utcnow()
    db.commit()
    return new_note
