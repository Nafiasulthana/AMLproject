-- Database Schema for Intelligent AML Fund Flow Tracking & Investigation Platform
-- Compatible with PostgreSQL and SQLite

CREATE TABLE IF NOT EXISTS roles (
    role_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

INSERT INTO roles (role_id, name, description) VALUES
('ADMIN', 'System Administrator', 'Full access to system health, configuration, ML models, and user management'),
('INVESTIGATOR', 'AML Investigator', 'Access to transaction monitoring, alert triaging, graph workspace, and case management'),
('OFFICER', 'Principal Officer', 'Senior approval role for case escalation, closing, and STR PDF report sign-off'),
('ANALYST', 'Compliance Analyst', 'Read-only access to risk dashboards, reports, and analytical metrics')
ON CONFLICT (role_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role_id VARCHAR(50) REFERENCES roles(role_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    national_id VARCHAR(50) UNIQUE NOT NULL,
    kyc_status VARCHAR(20) DEFAULT 'VERIFIED', -- VERIFIED, PENDING, REJECTED
    risk_category VARCHAR(20) DEFAULT 'LOW', -- LOW, MEDIUM, HIGH, CRITICAL
    occupation VARCHAR(100),
    monthly_income NUMERIC(15, 2),
    expected_monthly_volume NUMERIC(15, 2),
    address VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    account_number VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES customers(customer_id) ON DELETE CASCADE,
    account_type VARCHAR(30) DEFAULT 'SAVINGS', -- SAVINGS, CURRENT, OVERDRAFT, NRI
    balance NUMERIC(15, 2) DEFAULT 10000.00,
    currency VARCHAR(10) DEFAULT 'INR',
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, DORMANT, FROZEN
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    tx_id VARCHAR(100) PRIMARY KEY,
    sender_account VARCHAR(50) REFERENCES accounts(account_number),
    receiver_account VARCHAR(50) REFERENCES accounts(account_number),
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    channel VARCHAR(30) NOT NULL, -- UPI, NEFT, RTGS, ATM, CASH_DEPOSIT, MERCHANT
    tx_type VARCHAR(30) NOT NULL, -- DEBIT, CREDIT, TRANSFER
    location VARCHAR(100),
    ip_address VARCHAR(45),
    device_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    flagged_typology VARCHAR(50) DEFAULT 'NORMAL'
);

CREATE TABLE IF NOT EXISTS behaviour_profiles (
    customer_id VARCHAR(50) PRIMARY KEY REFERENCES customers(customer_id) ON DELETE CASCADE,
    avg_transaction_amount NUMERIC(15, 2) DEFAULT 5000.00,
    monthly_transaction_volume NUMERIC(15, 2) DEFAULT 50000.00,
    max_single_tx_amount NUMERIC(15, 2) DEFAULT 25000.00,
    tx_count_30d INT DEFAULT 10,
    frequent_counterparties TEXT, -- JSON array of account numbers
    preferred_channels TEXT, -- JSON array
    typical_hours TEXT, -- JSON array of active hours e.g. [9,10,11,14,15,16]
    risk_score NUMERIC(5, 2) DEFAULT 10.00,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aml_rules (
    rule_code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    typology VARCHAR(50) NOT NULL,
    description TEXT,
    threshold_value NUMERIC(15, 2) DEFAULT 0.00,
    risk_weight NUMERIC(5, 2) DEFAULT 20.00,
    is_enabled BOOLEAN DEFAULT TRUE
);

INSERT INTO aml_rules (rule_code, name, typology, description, threshold_value, risk_weight, is_enabled) VALUES
('R_STRUCTURING', 'CTR Avoidance Structuring', 'Structuring', 'Multiple transactions just below CTR reporting limit ($10,000 / ₹5,000,000)', 490000.00, 35.0, TRUE),
('R_LAYERING', 'Rapid High-Velocity Transfer', 'Layering', 'Quick movement of funds through multiple intermediate accounts within 30 minutes', 5.0, 30.0, TRUE),
('R_ROUNDTRIP', 'Circular Round Tripping', 'Round Tripping', 'Funds return to original source account via multi-hop path', 0.0, 40.0, TRUE),
('R_DORMANT', 'Dormant Account Sudden Spike', 'Dormant Account', 'High value transaction in an account inactive for > 180 days', 200000.00, 25.0, TRUE),
('R_SMURFING', 'Multi-Sender Consolidation', 'Smurfing', 'Numerous small deposits from separate senders into one aggregator account', 5.0, 30.0, TRUE),
('R_PROFILE_MISMATCH', 'Income Profile Mismatch', 'Profile Mismatch', 'Transaction amount exceeds 5x customer stated monthly income', 5.0, 20.0, TRUE),
('R_MONEY_MULE', 'Money Mule Rapid Pass-Through', 'Money Mule', 'Account receives large credit and immediately transfers > 95% out', 0.95, 35.0, TRUE)
ON CONFLICT (rule_code) DO NOTHING;

CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(50) PRIMARY KEY,
    tx_id VARCHAR(100) REFERENCES transactions(tx_id),
    customer_id VARCHAR(50) REFERENCES customers(customer_id),
    typology VARCHAR(50) NOT NULL,
    rule_risk NUMERIC(5, 2) DEFAULT 0.0,
    behaviour_risk NUMERIC(5, 2) DEFAULT 0.0,
    graph_risk NUMERIC(5, 2) DEFAULT 0.0,
    ml_risk NUMERIC(5, 2) DEFAULT 0.0,
    meta_risk_score NUMERIC(5, 2) NOT NULL,
    priority VARCHAR(20) DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
    status VARCHAR(30) DEFAULT 'PENDING', -- PENDING, UNDER_INVESTIGATION, CLOSED, ESCALATED, FALSE_POSITIVE
    assigned_to VARCHAR(50) REFERENCES users(user_id),
    shap_explanation TEXT, -- JSON string of SHAP feature contributions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cases (
    case_id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    lead_customer_id VARCHAR(50) REFERENCES customers(customer_id),
    priority VARCHAR(20) DEFAULT 'HIGH',
    status VARCHAR(30) DEFAULT 'OPEN', -- OPEN, IN_REVIEW, ESCALATED, CLOSED_STR, CLOSED_FALSE_POSITIVE
    correlated_typologies TEXT, -- JSON array of typologies
    meta_risk_score NUMERIC(5, 2) NOT NULL,
    assigned_investigator VARCHAR(50) REFERENCES users(user_id),
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_notes (
    note_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) REFERENCES cases(case_id) ON DELETE CASCADE,
    author_id VARCHAR(50) REFERENCES users(user_id),
    author_name VARCHAR(100),
    note_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS case_evidence (
    evidence_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) REFERENCES cases(case_id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    evidence_type VARCHAR(50), -- TRANSACTION_LOG, GRAPH_EXPORT, SHAP_REPORT, KYC_DOC
    file_path VARCHAR(255),
    uploaded_by VARCHAR(50) REFERENCES users(user_id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS str_reports (
    report_id VARCHAR(50) PRIMARY KEY,
    case_id VARCHAR(50) REFERENCES cases(case_id),
    fiu_ref_number VARCHAR(100) UNIQUE NOT NULL,
    narrative_summary TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'DRAFT', -- DRAFT, SUBMITTED, APPROVED, REJECTED
    generated_by VARCHAR(50) REFERENCES users(user_id),
    approved_by VARCHAR(50) REFERENCES users(user_id),
    pdf_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    username VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    target_entity VARCHAR(100),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
