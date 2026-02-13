from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from core.db_manager import Base

# ==========================================
# 1. Onboarding Data (기준 정보 - onboarding.db)
# ==========================================

class Hospital(Base):
    __tablename__ = "hospitals"

    hosp_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_code = Column(String, unique=True, nullable=False) # 요양기관번호
    hosp_name = Column(String, nullable=False)
    device_hwid = Column(String, nullable=True)             # 승인된 PC 식별값
    created_at = Column(DateTime, server_default=func.now())

class Doctor(Base):
    __tablename__ = "doctors"

    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_id = Column(Integer, ForeignKey("hospitals.hosp_id"))
    hosp_code = Column(String) # 빠른 조회를 위한 역정규화
    doc_name = Column(String, nullable=False)
    license_num = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Integer, default=1)

class Operator(Base):
    __tablename__ = "operators"

    op_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    role = Column(String) # ADMIN, MANAGER, STAFF
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    hosp_id = Column(Integer, ForeignKey("hospitals.hosp_id")) # [추가] 병원 소속 정보

class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    temp_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_id = Column(Integer, ForeignKey("hospitals.hosp_id"))
    temp_name = Column(String, nullable=False)   # 예: '레즈메드_수면보고서_v1'
    doc_type = Column(String, nullable=False)    # PRESCRIPTION, REPORT, CONTRACT
    vendor_name = Column(String)                 # ResMed, Philips 등
    identifier_keyword = Column(String)          # 양식 식별 키워드
    created_at = Column(DateTime, server_default=func.now())

class Field(Base):
    __tablename__ = "document_fields"
    
    field_id = Column(Integer, primary_key=True, autoincrement=True)
    temp_id = Column(Integer, ForeignKey("document_templates.temp_id"))
    field_name = Column(String, nullable=False)   # 예: 'start_date', 'pressure'
    field_type = Column(String)                   # TEXT, DATE, NUMBER
    extract_method = Column(String)               # OCR, REGEX
    extract_rule = Column(String)                 # 정규식 패턴 등
    is_required = Column(Integer, default=1)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    operator_name = Column(String)
    action = Column(String)     # LOGIN, APPROVE, DELETE_LOG
    target_table = Column(String)
    details = Column(Text)      # 상세 변경 내용 (JSON)
    created_at = Column(DateTime, server_default=func.now())

class SecuritySetting(Base):
    __tablename__ = "security_settings"

    id = Column(Integer, primary_key=True) # 항상 1번만 사용
    password_hash = Column(String, nullable=False)
    password_set_at = Column(DateTime, server_default=func.now())
    last_login_at = Column(DateTime)
    
# ==========================================
# 2. Runtime Data (실행 정보 - runtime.db)
# ==========================================

class Patient(Base):
    __tablename__ = "patients"

    pat_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_name = Column(String, nullable=False)
    chart_num = Column(String, unique=True, nullable=False)
    # [상태] 시스템 로직이 판단하여 업데이트
    status = Column(String, default="ACTIVE") #TEMP # ACTIVE, PAUSE(분할), STOP
    compliance_status = Column(String, default="BEFORE") # BEFORE, ING(분할), PASS
    # [데이터군 A: 파일에서 추출됨]
    # [인적 사항 캐싱] 청구 시 매번 파일이나 EMR을 뒤지지 않도록 저장
    # FileScan -> OCR -> Validation 후 여기에 저장
    compliance_start_date = Column(DateTime, nullable=True) # 순응 시작일
    compliance_pass_date = Column(DateTime, nullable=True)  # 순응 통과일
    reg_num_front = Column(String(6))  # 주민번호 앞자리
    reg_num_back = Column(String(7))   # 주민번호 뒷자리 (보안을 위해 별도 관리)
    phone_num = Column(String)         # 연락처
    address = Column(String)           # 주소
    biz_num = Column(String)           # 사업자등록번호 (필요 시)
    # [데이터군 B: 관리자가 직접 입력]
    # 프로그램 설정창에서 관리자가 입력
    pause_start_date = Column(DateTime, nullable=True)
    pause_end_date = Column(DateTime, nullable=True)
    
    updated_at = Column(DateTime, onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"))
    billing_month = Column(String, nullable=False) # '2024-02'
    claim_type = Column(String)                    # NORMAL, SPLIT_TRAVEL, SPLIT_RE_PRESC, SPLIT_C_BEFORE
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    copay_rate = Column(Integer)                   # 50 or 20 (건보부담 50% / 80%)
    total_amount = Column(Integer)                 # 계산된 총액
    status = Column(String, default="READY")       # READY, DONE, ERROR
    created_at = Column(DateTime, server_default=func.now())

class PatientDocument(Base):
    __tablename__ = "patient_documents"

    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"))
    generated_filename = Column(String, unique=True, nullable=False) # [사용자 규칙 반영] 예: 0001ps20260202
    doc_type = Column(String)     # ps(처방전), rp(보고서), ct(계약서)
    issue_date = Column(String)    # 파일명에 들어간 날짜 (20260202)
    managed_path = Column(String)  # 실제 저장 위치
    file_status = Column(String)   # COPIED, OCR_DONE, ERROR
    created_at = Column(DateTime, server_default=func.now())

class ExtractedData(Base):
    """추출된 값 저장 (어떤 문서에서 나왔는지 doc_id와 연결)"""
    __tablename__ = "extracted_data"

    data_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id")) 
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    doctor_id = Column(Integer, ForeignKey("doctors.doc_id"), nullable=True) # 처방전용
    field_id = Column(Integer)     # Field 테이블의 ID와 매칭
    value = Column(String)         # 실제 추출된 값
    # 데이터의 신뢰도 (OCR 결과가 불확실할 경우 대비)
    confidence = Column(Float)     # 0.0 ~ 1.0 (OCR 엔진이 준 점수)
    is_confirmed = Column(Integer, default=0) # 관리자가 눈으로 확인했는지 여부 (법적 책임)
    updated_at = Column(DateTime, onupdate=func.now())