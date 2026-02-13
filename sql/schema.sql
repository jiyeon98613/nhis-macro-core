-- [1] hospitals (요양기관 정보)
CREATE TABLE IF NOT EXISTS hospitals (
    hosp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hosp_code TEXT UNIQUE NOT NULL,    -- 요양기관번호 8자리
    hosp_name TEXT NOT NULL,
    device_hwid TEXT,                  -- 승인된 기기 식별값
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- [2] doctors (의사 면허 정보)
CREATE TABLE IF NOT EXISTS doctors (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hosp_id INTEGER,
    hosp_code TEXT NOT NULL,           -- 빠른 조회를 위한 역정규화
    doc_name TEXT NOT NULL,
    license_num TEXT UNIQUE NOT NULL,
    is_active INTEGER DEFAULT 1,       -- 의사 활성 상태 (1: 활성, 0: 퇴사 등)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hosp_id) REFERENCES hospitals(hosp_id)
);

-- [3] operators (청구 담당자/관리자)
CREATE TABLE IF NOT EXISTS operators (
    op_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hosp_id INTEGER,                   -- 병원 소속 정보 추가
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT,                         -- ADMIN, MANAGER, STAFF
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hosp_id) REFERENCES hospitals(hosp_id)
);

-- [4] security_settings (시스템 보안)
CREATE TABLE IF NOT EXISTS security_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    password_hash TEXT NOT NULL,
    password_set_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME
);

-- [5] document_templates (문서 양식 정의 - 6종 대응)
CREATE TABLE IF NOT EXISTS document_templates (
    temp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hosp_id INTEGER NOT NULL,
    temp_name TEXT NOT NULL,           -- 예: 'ResMed_S10_Report'
    doc_type TEXT NOT NULL,            -- ps, rp, ct, tx, cs, rt (6종 식별자)
    vendor_name TEXT,                  -- 제조사 (ResMed, Philips 등)
    identifier_keyword TEXT,           -- 양식 식별용 고유 키워드
    confidence_policy TEXT NOT NULL,   -- MANUAL_REQUIRED / AUTO_WITH_REVIEW
    approved INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hosp_id) REFERENCES hospitals(hosp_id)
);

-- [6] document_fields (추출 데이터 필드 정의)
CREATE TABLE IF NOT EXISTS document_fields (
    field_id INTEGER PRIMARY KEY AUTOINCREMENT,
    temp_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,          -- start_date, reg_num 등
    field_type TEXT NOT NULL,          -- DATE, TEXT, NUMBER
    extract_method TEXT NOT NULL,      -- OCR, REGEX, KEYWORD
    extract_rule TEXT,                 -- 정규표현식 패턴 등
    is_required INTEGER DEFAULT 1,     -- 필수 필드 여부
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (temp_id) REFERENCES document_templates(temp_id)
);

-- [7] approvals (관리자 승인 기록 - 법적 책임 소재)
CREATE TABLE IF NOT EXISTS approvals (
    approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,               -- BATCH_SAVE, DELETE_LOG, FINAL_SUBMIT
    target_id TEXT NOT NULL,           -- 승인 대상의 PK (예: claim_id)
    approved_by INTEGER NOT NULL,
    approved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    detail TEXT,                       -- 상세 사유 또는 로그
    FOREIGN KEY (approved_by) REFERENCES operators(op_id)
);

-- [8] audit_logs (감사 로그 - 영구 보관용)
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    operator_id INTEGER NOT NULL,
    action TEXT NOT NULL,              -- LOGIN, DATA_MODIFIED, FILE_EXPORT
    target TEXT NOT NULL,              -- 대상 테이블 또는 파일명
    target_id TEXT,
    detail TEXT,
    FOREIGN KEY (operator_id) REFERENCES operators(op_id)
);