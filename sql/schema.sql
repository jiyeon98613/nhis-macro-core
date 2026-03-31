-- ============================================================
-- Onboarding DB (admin_master / onboarding.db)
-- ============================================================

-- [1] business_certificates (사업자등록증 — Vendor/기관용)
CREATE TABLE IF NOT EXISTS business_certificates (
    bc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    biz_num TEXT UNIQUE NOT NULL,
    company_name TEXT,
    rep_name TEXT,
    address TEXT,
    biz_type TEXT,
    biz_item TEXT,
    email TEXT,
    doc_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- [2] frequent_hospitals (자주 사용하는 요양기관 — 자동완성용)
CREATE TABLE IF NOT EXISTS frequent_hospitals (
    fh_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hosp_code TEXT UNIQUE NOT NULL,
    hosp_name TEXT NOT NULL,
    bc_id INTEGER,
    reg_doc_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bc_id) REFERENCES business_certificates(bc_id)
);

-- [3] manufacturers (양압기 제조/수입사)
CREATE TABLE IF NOT EXISTS manufacturers (
    man_id INTEGER PRIMARY KEY AUTOINCREMENT,
    man_name TEXT UNIQUE NOT NULL,
    country TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- [4] vendors (양압기 렌탈 업체 — PC 인증 대상)
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL,
    biz_num TEXT UNIQUE,
    bc_id INTEGER,
    device_hwid TEXT,
    manager_name TEXT,
    contact TEXT,
    is_hospital_internal INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bc_id) REFERENCES business_certificates(bc_id)
);

-- [5] devices (양압기 기기)
CREATE TABLE IF NOT EXISTS devices (
    dev_id INTEGER PRIMARY KEY AUTOINCREMENT,
    man_id INTEGER,
    vendor_id INTEGER,
    serial_num TEXT UNIQUE NOT NULL,
    device_type TEXT,
    model_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (man_id) REFERENCES manufacturers(man_id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
);

-- [6] operators (시스템 운영자)
CREATE TABLE IF NOT EXISTS operators (
    op_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hosp_code TEXT,
    name TEXT NOT NULL,
    phone_num TEXT UNIQUE,
    email TEXT,
    role TEXT,
    is_active INTEGER DEFAULT 1
);

-- [7] security_settings
CREATE TABLE IF NOT EXISTS security_settings (
    id INTEGER PRIMARY KEY,
    op_id INTEGER UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    password_set_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    password_snooze_until DATETIME,
    FOREIGN KEY (op_id) REFERENCES operators(op_id)
);

-- [8] audit_logs
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    op_id INTEGER,
    action TEXT,
    target_id INTEGER,
    reason TEXT,
    access_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (op_id) REFERENCES operators(op_id)
);

-- [9] approvals
CREATE TABLE IF NOT EXISTS approvals (
    approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,
    target_id TEXT NOT NULL,
    approved_by INTEGER NOT NULL,
    approved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    detail TEXT,
    FOREIGN KEY (approved_by) REFERENCES operators(op_id)
);

-- [10] document_templates
CREATE TABLE IF NOT EXISTS document_templates (
    temp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hosp_code TEXT,
    temp_name TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    vendor_name TEXT,
    identifier_keyword TEXT,
    confidence_policy TEXT NOT NULL,
    approved INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- [11] document_fields
CREATE TABLE IF NOT EXISTS document_fields (
    field_id INTEGER PRIMARY KEY AUTOINCREMENT,
    temp_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    field_type TEXT NOT NULL,
    extract_method TEXT NOT NULL,
    extract_rule TEXT,
    is_required INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (temp_id) REFERENCES document_templates(temp_id)
);
