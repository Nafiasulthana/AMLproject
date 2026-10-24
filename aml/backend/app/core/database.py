import os
import sqlite3
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Attempt PostgreSQL connection, fallback to SQLite if PostgreSQL is unavailable
try:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})
    # Test connection
    with engine.connect() as conn:
        pass
    logger.info("Connected successfully to PostgreSQL database.")
except Exception as e:
    logger.warning(f"PostgreSQL connection failed ({e}). Falling back to SQLite database at {settings.SQLITE_URL}")
    engine = create_engine(settings.SQLITE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables and default seed data."""
    from app.models.models import Role, User, Customer, Account, AMLRule, CustomerBehaviourProfile
    from app.core.security import hash_password

    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed Roles
        roles_data = [
            ("ADMIN", "System Administrator", "Full access to system health, configuration, ML models, and user management"),
            ("INVESTIGATOR", "AML Investigator", "Access to transaction monitoring, alert triaging, graph workspace, and case management"),
            ("OFFICER", "Principal Officer", "Senior approval role for case escalation, closing, and STR PDF report sign-off"),
            ("ANALYST", "Compliance Analyst", "Read-only access to risk dashboards, reports, and analytical metrics")
        ]
        for r_id, r_name, r_desc in roles_data:
            existing = db.query(Role).filter(Role.role_id == r_id).first()
            if not existing:
                db.add(Role(role_id=r_id, name=r_name, description=r_desc))
        db.commit()

        # Seed Users
        users_data = [
            ("USR_ADMIN", "admin", "admin@bankaml.com", hash_password("admin123"), "System Admin", "ADMIN"),
            ("USR_INV1", "investigator", "investigator@bankaml.com", hash_password("inv123"), "Sarah Jenkins (Senior Investigator)", "INVESTIGATOR"),
            ("USR_OFF1", "officer", "officer@bankaml.com", hash_password("officer123"), "Marcus Vance (Principal Officer)", "OFFICER"),
            ("USR_ANA1", "analyst", "analyst@bankaml.com", hash_password("analyst123"), "Elena Rostova (Compliance Analyst)", "ANALYST")
        ]
        for u_id, u_name, u_email, u_pass, u_full, u_role in users_data:
            existing = db.query(User).filter(User.username == u_name).first()
            if not existing:
                db.add(User(
                    user_id=u_id, username=u_name, email=u_email,
                    hashed_password=u_pass, full_name=u_full, role_id=u_role
                ))
        db.commit()

        # Seed Rules
        rules_data = [
            ("R_STRUCTURING", "CTR Avoidance Structuring", "Structuring", "Multiple transactions just below CTR reporting limit ($10,000 / ₹490,000)", 490000.00, 35.0),
            ("R_LAYERING", "Rapid High-Velocity Transfer", "Layering", "Quick movement of funds through multiple intermediate accounts within 30 minutes", 5.0, 30.0),
            ("R_ROUNDTRIP", "Circular Round Tripping", "Round Tripping", "Funds return to original source account via multi-hop path", 0.0, 40.0),
            ("R_DORMANT", "Dormant Account Sudden Spike", "Dormant Account", "High value transaction in an account inactive for > 180 days", 200000.00, 25.0),
            ("R_SMURFING", "Multi-Sender Consolidation", "Smurfing", "Numerous small deposits from separate senders into one aggregator account", 5.0, 30.0),
            ("R_PROFILE_MISMATCH", "Income Profile Mismatch", "Profile Mismatch", "Transaction amount exceeds 5x customer stated monthly income", 5.0, 20.0),
            ("R_MONEY_MULE", "Money Mule Rapid Pass-Through", "Money Mule", "Account receives large credit and immediately transfers > 95% out", 0.95, 35.0)
        ]
        for r_code, r_name, r_typ, r_desc, r_thresh, r_weight in rules_data:
            existing = db.query(AMLRule).filter(AMLRule.rule_code == r_code).first()
            if not existing:
                db.add(AMLRule(
                    rule_code=r_code, name=r_name, typology=r_typ,
                    description=r_desc, threshold_value=r_thresh, risk_weight=r_weight, is_enabled=True
                ))
        db.commit()

        # Seed Initial Customers & Accounts
        if db.query(Customer).count() == 0:
            customers_seed = [
                ("CUST_101", "Acme Global Exports", "IND100982", "VERIFIED", "HIGH", "Import Export", 2500000.00, 15000000.00, "Financial District", "Mumbai", "India"),
                ("CUST_102", "Vikram Malhotra", "IND887211", "VERIFIED", "LOW", "Software Engineer", 180000.00, 200000.00, "Indiranagar", "Bengaluru", "India"),
                ("CUST_103", "Apex Shell Holdings", "IND998124", "PENDING", "CRITICAL", "Consulting", 50000.00, 50000000.00, "Connaught Place", "New Delhi", "India"),
                ("CUST_104", "Priya Sharma", "IND441299", "VERIFIED", "LOW", "Teacher", 65000.00, 70000.00, "Salt Lake", "Kolkata", "India"),
                ("CUST_105", "Nexus Logistics Pvt Ltd", "IND331900", "VERIFIED", "MEDIUM", "Logistics", 1200000.00, 8000000.00, "Gachibowli", "Hyderabad", "India"),
                ("CUST_106", "Rajesh Gupta (Dormant Mule)", "IND552199", "VERIFIED", "HIGH", "Unemployed", 15000.00, 20000.00, "Civil Lines", "Nagpur", "India"),
                ("CUST_107", "Starlight Traders", "IND662910", "VERIFIED", "HIGH", "Wholesale Electronics", 800000.00, 12000000.00, "Chandni Chowk", "Delhi", "India")
            ]
            for c_id, c_name, c_nat, c_kyc, c_risk, c_occ, c_inc, c_exp, c_addr, c_city, c_country in customers_seed:
                db.add(Customer(
                    customer_id=c_id, full_name=c_name, national_id=c_nat,
                    kyc_status=c_kyc, risk_category=c_risk, occupation=c_occ,
                    monthly_income=c_inc, expected_monthly_volume=c_exp,
                    address=c_addr, city=c_city, country=c_country
                ))
            db.commit()

            accounts_seed = [
                ("ACC_1001", "CUST_101", "CURRENT", 8500000.00, "ACTIVE"),
                ("ACC_1002", "CUST_102", "SAVINGS", 34000.00, "ACTIVE"),
                ("ACC_1003", "CUST_103", "CURRENT", 12500000.00, "ACTIVE"),
                ("ACC_1004", "CUST_104", "SAVINGS", 12000.00, "ACTIVE"),
                ("ACC_1005", "CUST_105", "CURRENT", 4200000.00, "ACTIVE"),
                ("ACC_1006", "CUST_106", "SAVINGS", 950000.00, "DORMANT"),
                ("ACC_1007", "CUST_107", "CURRENT", 3100000.00, "ACTIVE")
            ]
            for a_num, c_id, a_type, bal, st in accounts_seed:
                db.add(Account(
                    account_number=a_num, customer_id=c_id, account_type=a_type, balance=bal, status=st
                ))
                # Seed Behaviour profile
                db.add(CustomerBehaviourProfile(
                    customer_id=c_id,
                    avg_transaction_amount=5000.0 if st == "SAVINGS" else 150000.0,
                    monthly_transaction_volume=50000.0 if st == "SAVINGS" else 2000000.0,
                    max_single_tx_amount=25000.0 if st == "SAVINGS" else 1000000.0,
                    tx_count_30d=8,
                    frequent_counterparties="[]",
                    preferred_channels='["UPI", "NEFT"]',
                    typical_hours='[9, 10, 11, 14, 15, 16, 17]',
                    risk_score=15.0
                ))
            db.commit()

    except Exception as ex:
        logger.error(f"Error seeding initial database: {ex}")
        db.rollback()
    finally:
        db.close()
