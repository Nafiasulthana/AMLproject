from datetime import datetime
from sqlalchemy import Column, String, Numeric, Boolean, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role_id = Column(String(50), ForeignKey("roles.role_id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role")

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True)
    full_name = Column(String(150), nullable=False)
    national_id = Column(String(50), unique=True, nullable=False)
    kyc_status = Column(String(20), default="VERIFIED")
    risk_category = Column(String(20), default="LOW")
    occupation = Column(String(100))
    monthly_income = Column(Numeric(15, 2))
    expected_monthly_volume = Column(Numeric(15, 2))
    address = Column(String(255))
    city = Column(String(100))
    country = Column(String(100), default="India")
    created_at = Column(DateTime, default=datetime.utcnow)

    accounts = relationship("Account", back_populates="customer")
    behaviour_profile = relationship("CustomerBehaviourProfile", back_populates="customer", uselist=False)

class Account(Base):
    __tablename__ = "accounts"

    account_number = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False)
    account_type = Column(String(30), default="SAVINGS")
    balance = Column(Numeric(15, 2), default=10000.00)
    currency = Column(String(10), default="INR")
    status = Column(String(20), default="ACTIVE")
    opened_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="accounts")

class Transaction(Base):
    __tablename__ = "transactions"

    tx_id = Column(String(100), primary_key=True)
    sender_account = Column(String(50), ForeignKey("accounts.account_number"))
    receiver_account = Column(String(50), ForeignKey("accounts.account_number"))
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="INR")
    channel = Column(String(30), nullable=False)
    tx_type = Column(String(30), nullable=False)
    location = Column(String(100))
    ip_address = Column(String(45))
    device_id = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    flagged_typology = Column(String(50), default="NORMAL")

class CustomerBehaviourProfile(Base):
    __tablename__ = "behaviour_profiles"

    customer_id = Column(String(50), ForeignKey("customers.customer_id"), primary_key=True)
    avg_transaction_amount = Column(Numeric(15, 2), default=5000.00)
    monthly_transaction_volume = Column(Numeric(15, 2), default=50000.00)
    max_single_tx_amount = Column(Numeric(15, 2), default=25000.00)
    tx_count_30d = Column(Integer, default=10)
    frequent_counterparties = Column(Text)
    preferred_channels = Column(Text)
    typical_hours = Column(Text)
    risk_score = Column(Numeric(5, 2), default=10.00)
    updated_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="behaviour_profile")

class AMLRule(Base):
    __tablename__ = "aml_rules"

    rule_code = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    typology = Column(String(50), nullable=False)
    description = Column(Text)
    threshold_value = Column(Numeric(15, 2), default=0.00)
    risk_weight = Column(Numeric(5, 2), default=20.00)
    is_enabled = Column(Boolean, default=True)

class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(50), primary_key=True)
    tx_id = Column(String(100), ForeignKey("transactions.tx_id"))
    customer_id = Column(String(50), ForeignKey("customers.customer_id"))
    typology = Column(String(50), nullable=False)
    rule_risk = Column(Numeric(5, 2), default=0.0)
    behaviour_risk = Column(Numeric(5, 2), default=0.0)
    graph_risk = Column(Numeric(5, 2), default=0.0)
    ml_risk = Column(Numeric(5, 2), default=0.0)
    meta_risk_score = Column(Numeric(5, 2), nullable=False)
    priority = Column(String(20), default="MEDIUM")
    status = Column(String(30), default="PENDING")
    assigned_to = Column(String(50), ForeignKey("users.user_id"), nullable=True)
    shap_explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    lead_customer_id = Column(String(50), ForeignKey("customers.customer_id"))
    priority = Column(String(20), default="HIGH")
    status = Column(String(30), default="OPEN")
    correlated_typologies = Column(Text)
    meta_risk_score = Column(Numeric(5, 2), nullable=False)
    assigned_investigator = Column(String(50), ForeignKey("users.user_id"), nullable=True)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    notes = relationship("CaseNote", back_populates="case")
    evidence = relationship("CaseEvidence", back_populates="case")

class CaseNote(Base):
    __tablename__ = "case_notes"

    note_id = Column(String(50), primary_key=True)
    case_id = Column(String(50), ForeignKey("cases.case_id"))
    author_id = Column(String(50), ForeignKey("users.user_id"))
    author_name = Column(String(100))
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="notes")

class CaseEvidence(Base):
    __tablename__ = "case_evidence"

    evidence_id = Column(String(50), primary_key=True)
    case_id = Column(String(50), ForeignKey("cases.case_id"))
    title = Column(String(150), nullable=False)
    evidence_type = Column(String(50))
    file_path = Column(String(255))
    uploaded_by = Column(String(50), ForeignKey("users.user_id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="evidence")

class STRReport(Base):
    __tablename__ = "str_reports"

    report_id = Column(String(50), primary_key=True)
    case_id = Column(String(50), ForeignKey("cases.case_id"))
    fiu_ref_number = Column(String(100), unique=True, nullable=False)
    narrative_summary = Column(Text, nullable=False)
    status = Column(String(30), default="DRAFT")
    generated_by = Column(String(50), ForeignKey("users.user_id"))
    approved_by = Column(String(50), ForeignKey("users.user_id"), nullable=True)
    pdf_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True)
    username = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    target_entity = Column(String(100))
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
