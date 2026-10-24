from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    username: str
    full_name: str
    role: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# User Schemas
class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str
    role_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionCreate(BaseModel):
    sender_account: str
    receiver_account: str
    amount: float
    channel: str = "NEFT" # UPI, NEFT, RTGS, ATM, CASH_DEPOSIT, MERCHANT
    tx_type: str = "TRANSFER"
    location: Optional[str] = "Mumbai, India"
    ip_address: Optional[str] = "192.168.1.10"
    device_id: Optional[str] = "DEV_MOB_992"
    flagged_typology: Optional[str] = "NORMAL"

class TransactionResponse(BaseModel):
    tx_id: str
    sender_account: str
    receiver_account: str
    amount: float
    currency: str
    channel: str
    tx_type: str
    location: Optional[str]
    ip_address: Optional[str]
    device_id: Optional[str]
    timestamp: datetime
    flagged_typology: str

    class Config:
        from_attributes = True

# Alert Schemas
class AlertResponse(BaseModel):
    alert_id: str
    tx_id: Optional[str]
    customer_id: Optional[str]
    typology: str
    rule_risk: float
    behaviour_risk: float
    graph_risk: float
    ml_risk: float
    meta_risk_score: float
    priority: str
    status: str
    assigned_to: Optional[str]
    shap_explanation: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AlertUpdateStatus(BaseModel):
    status: str
    assigned_to: Optional[str] = None

# Case Schemas
class CaseNoteCreate(BaseModel):
    note_text: str

class CaseNoteResponse(BaseModel):
    note_id: str
    case_id: str
    author_id: Optional[str]
    author_name: Optional[str]
    note_text: str
    created_at: datetime

    class Config:
        from_attributes = True

class CaseResponse(BaseModel):
    case_id: str
    title: str
    lead_customer_id: Optional[str]
    priority: str
    status: str
    correlated_typologies: Optional[str]
    meta_risk_score: float
    assigned_investigator: Optional[str]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_investigator: Optional[str] = None
    summary: Optional[str] = None

# STR Schemas
class STRCreate(BaseModel):
    case_id: str
    narrative_summary: str

class STRResponse(BaseModel):
    report_id: str
    case_id: str
    fiu_ref_number: str
    narrative_summary: str
    status: str
    generated_by: Optional[str]
    approved_by: Optional[str]
    pdf_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Simulation Controls Schema
class SimulationConfig(BaseModel):
    is_running: bool = False
    speed_multiplier: int = 1 # 1x to 50x
    selected_typology: str = "MIXED" # NORMAL, STRUCTURING, LAYERING, ROUND_TRIP, SMURFING, DORMANT, MULE
