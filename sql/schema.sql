
        -- [1] hospitals
        CREATE TABLE IF NOT EXISTS hospitals (
            hosp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hosp_code TEXT UNIQUE NOT NULL,
            hosp_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- [2] doctors
        CREATE TABLE IF NOT EXISTS doctors (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            hosp_id INTEGER,
            doc_name TEXT NOT NULL,
            license_num TEXT UNIQUE NOT NULL,
            FOREIGN KEY (hosp_id) REFERENCES hospitals(hosp_id)
        );

        -- [3] operators
        CREATE TABLE IF NOT EXISTS operators (
            op_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            is_active INTEGER DEFAULT 1,
            role TEXT
        );

        -- [4] security_settings
        CREATE TABLE IF NOT EXISTS security_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password_hash TEXT NOT NULL,
            password_set_at TEXT NOT NULL,
            last_login_at TEXT
        );

        -- [5] document_templates
        CREATE TABLE IF NOT EXISTS document_templates (
            template_id TEXT PRIMARY KEY,
            hosp_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            confidence_policy TEXT NOT NULL, -- MANUAL_REQUIRED / AUTO_WITH_REVIEW
            created_at TEXT NOT NULL,
            approved INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (hosp_id) REFERENCES hospitals(hosp_id)
        );

        -- [6] document_fields
        CREATE TABLE IF NOT EXISTS document_fields (
            field_id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            field_name TEXT NOT NULL,
            extract_method TEXT NOT NULL, -- OCR, regex, keyword
            extract_rule TEXT,
            region_x1 INTEGER, region_y1 INTEGER,
            region_x2 INTEGER, region_y2 INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (template_id) REFERENCES document_templates(template_id)
        );

        -- [7] approvals
        CREATE TABLE IF NOT EXISTS approvals (
            approval_id TEXT PRIMARY KEY,
            scope TEXT NOT NULL, -- hospital_info, document_template, batch_save 등
            target_id TEXT NOT NULL,
            approved_by INTEGER NOT NULL,
            approved_at TEXT NOT NULL,
            detail TEXT,
            FOREIGN KEY (approved_by) REFERENCES operators(op_id)
        );

        -- [8] audit_logs
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            operator_id INTEGER NOT NULL,
            action TEXT NOT NULL,          -- LOGIN, CREATE, UPDATE, DELETE, EXPORT
            target TEXT NOT NULL,          -- 테이블명 혹은 서비스명
            target_id TEXT,                -- 변경된 대상의 PK
            detail TEXT,                   -- JSON 형태의 긴 텍스트 저장 가능
            FOREIGN KEY (operator_id) REFERENCES operators(op_id)
        );
