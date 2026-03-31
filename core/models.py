"""
core/models.py — SQLAlchemy ORM 모델 정의
=============================================
- OnboardingBase: 병원·의사·운영자·사업자등록 등 기준 정보 (onboarding.db)
- RuntimeBase: 환자·문서·청구 등 실행 데이터 (runtime.db)

테이블 추가/변경 시 반드시 양쪽 Base 소속을 확인해야함.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, ForeignKey,
    Text, Float, Boolean, Index, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.db_manager import OnboardingBase, RuntimeBase

# =================================================================
# 1. Onboarding Data (기준 정보 - onboarding.db)
# =================================================================


class BusinessCertificate(OnboardingBase):
    """사업자등록증 정보 — Vendor/기관용 (환자용은 PatientBC)"""
    __tablename__ = "business_certificates"

    bc_id = Column(Integer, primary_key=True, autoincrement=True)
    biz_num = Column(String, unique=True, nullable=False)   # 사업자등록번호 ("-" 없이)
    company_name = Column(String)       # 상호
    rep_name = Column(String)           # 대표자 성명
    address = Column(String)            # 사업장 주소
    biz_type = Column(String)           # 업태
    biz_item = Column(String)           # 종목
    email = Column(String)              # 이메일
    doc_path = Column(String, nullable=True)   # 사업자등록증 이미지/PDF 경로
    created_at = Column(DateTime, server_default=func.now())


class FrequentHospital(OnboardingBase):
    """자주 사용하는 요양기관 즐겨찾기 — 처방전 입력 자동완성용"""
    __tablename__ = "frequent_hospitals"

    fh_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_code = Column(String, unique=True, nullable=False)   # 요양기관번호
    hosp_name = Column(String, nullable=False)
    bc_id = Column(Integer, ForeignKey("business_certificates.bc_id"), nullable=True)
    reg_doc_path = Column(String, nullable=True)              # 요양기관 등록 서류 경로
    created_at = Column(DateTime, server_default=func.now())


class Manufacturer(OnboardingBase):
    """양압기 제조/수입사 (예: 레즈메드, 필립스, 로벤스타인 등)"""
    __tablename__ = "manufacturers"

    man_id = Column(Integer, primary_key=True, autoincrement=True)
    man_name = Column(String, nullable=False, unique=True)
    country = Column(String)            # 제조국
    created_at = Column(DateTime, server_default=func.now())


class Vendor(OnboardingBase):
    """양압기 렌탈 및 유지관리업체 (소매상)
    사업자 상세정보(대표자·주소·업태·종목·이메일)는
    BusinessCertificate(bc_id)에서 조회.
    """
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_name = Column(String, nullable=False)                # 상호 (조회 편의용)
    biz_num = Column(String, unique=True)                       # 사업자번호 (매칭 편의용)
    bc_id = Column(Integer, ForeignKey("business_certificates.bc_id"), nullable=True)
    device_hwid = Column(String, nullable=True)                 # 승인된 PC 식별값 (기기 인증용)
    manager_name = Column(String)                               # 담당자 성함
    contact = Column(String)                                    # 연락처
    is_hospital_internal = Column(Boolean, default=False)       # 병원 자체 관리 여부
    created_at = Column(DateTime, server_default=func.now())


class Device(OnboardingBase):
    """양압기 기기 마스터 정보"""
    __tablename__ = "devices"

    dev_id = Column(Integer, primary_key=True, autoincrement=True)
    man_id = Column(Integer, ForeignKey("manufacturers.man_id"))     # 제조사 연결
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"))     # 관리업체 연결
    serial_num = Column(String, unique=True, nullable=False)         # 기기번호
    device_type = Column(String)   # CPAP, APAP, BiPAP
    model_name = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class Operator(OnboardingBase):
    """시스템 운영자 계정"""
    __tablename__ = "operators"

    op_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_code = Column(String, nullable=True)                # 소속 요양기관코드 (cross-DB: frequent_hospitals)
    name = Column(String(50), nullable=False)
    phone_num = Column(String(20), unique=True)    # 로그인 ID (전화번호)
    email = Column(String(100))                    # 선택 입력
    role = Column(String(20))                      # ADMIN, STAFF
    is_active = Column(Integer, default=1)
    security = relationship("SecuritySetting", back_populates="operator", uselist=False)


class AuditLog(OnboardingBase):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    op_id = Column(Integer, ForeignKey("operators.op_id"))    # 누가
    action = Column(String(100))                               # 무엇을
    target_id = Column(Integer, nullable=True)                 # 누구에게(환자 ID 등)
    reason = Column(String(500))                               # 왜/상세
    access_time = Column(DateTime, server_default=func.now())


class SecuritySetting(OnboardingBase):
    __tablename__ = "security_settings"

    id = Column(Integer, primary_key=True)
    op_id = Column(Integer, ForeignKey("operators.op_id"), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    password_set_at = Column(DateTime, server_default=func.now())
    password_snooze_until = Column(DateTime, nullable=True)
    operator = relationship("Operator", back_populates="security")


class Approval(OnboardingBase):
    """관리자 승인 기록 (법적 책임 소재)"""
    __tablename__ = "approvals"

    approval_id = Column(Integer, primary_key=True, autoincrement=True)
    scope = Column(String, nullable=False)        # BATCH_SAVE, DELETE_LOG, FINAL_SUBMIT, …
    target_id = Column(String, nullable=False)     # 승인 대상의 PK
    approved_by = Column(Integer, ForeignKey("operators.op_id"), nullable=False)
    approved_at = Column(DateTime, server_default=func.now())
    detail = Column(Text)


class DocumentTemplate(OnboardingBase):
    """문서 양식 정의 (6종 대응) — OCR 추출의 기준점"""
    __tablename__ = "document_templates"

    temp_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_code = Column(String, nullable=True)                  # 요양기관코드 (cross-DB: frequent_hospitals)
    temp_name = Column(String, nullable=False)          # 예: 'ResMed_S10_Report'
    doc_type = Column(String, nullable=False)            # ps, sr, ct, tx, rc, rt
    vendor_name = Column(String)                         # 제조사 (ResMed, Philips 등)
    identifier_keyword = Column(String)                  # 양식 식별용 고유 키워드
    confidence_policy = Column(String, nullable=False)   # MANUAL_REQUIRED / AUTO_WITH_REVIEW
    approved = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    fields = relationship("DocumentField", back_populates="template")


class DocumentField(OnboardingBase):
    """양식별 추출 필드 정의 — 각 필드의 위치/패턴 정보"""
    __tablename__ = "document_fields"

    field_id = Column(Integer, primary_key=True, autoincrement=True)
    temp_id = Column(Integer, ForeignKey("document_templates.temp_id"), nullable=False)
    field_name = Column(String, nullable=False)          # start_date, reg_num 등
    field_type = Column(String, nullable=False)          # DATE, TEXT, NUMBER
    extract_method = Column(String, nullable=False)      # OCR, REGEX, KEYWORD
    extract_rule = Column(String)                        # 정규표현식 패턴 등
    is_required = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    template = relationship("DocumentTemplate", back_populates="fields")


# =================================================================
# 2. Runtime Data (실행 정보 - runtime.db)
# =================================================================


class SystemLog(RuntimeBase):
    """프로그램 내부 오류 및 실행 상태 로깅"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20))          # INFO, ERROR, WARNING
    step_name = Column(String(100))     # 어느 단계에서 발생했는지
    message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class Patient(RuntimeBase):
    """환자 기본 인적사항 및 고정 정보"""
    __tablename__ = "patients"

    pat_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_name = Column(String, nullable=False, index=True)
    chart_num = Column(String, unique=True, nullable=False)
    reg_num_front = Column(String(6), index=True)
    reg_num_back = Column(String(7))
    phone_num = Column(String)
    address = Column(String)
    birth_date = Column(Date, nullable=True)               # 생년월일
    uses_biz_num = Column(Boolean, default=False)          # 사업자번호 청구 여부
    biz_num = Column(String, nullable=True)                # 매칭 편의용 (PatientBC와 동기화)
    pbc_id = Column(Integer, ForeignKey("patient_business_certificates.pbc_id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PatientBC(RuntimeBase):
    """환자 사업자등록 관련 데이터 — 사업자번호로 청구하는 환자 전용"""
    __tablename__ = "patient_business_certificates"

    pbc_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), nullable=False, index=True)
    biz_num = Column(String, unique=True, nullable=False)   # 사업자등록번호
    company_name = Column(String)       # 상호
    rep_name = Column(String)           # 대표자 성명
    address = Column(String)            # 사업장 주소
    biz_type = Column(String)           # 업태
    biz_item = Column(String)           # 종목
    email = Column(String)
    doc_path = Column(String, nullable=True)   # 사업자등록증 이미지/PDF 경로
    created_at = Column(DateTime, server_default=func.now())


class DocumentInfo(RuntimeBase):
    """문서 파일 메타데이터 및 저장 경로 관리 (구 PatientDocument)"""
    __tablename__ = "patient_documents"    # 기존 테이블명 유지 (FK 호환)
    # 하위 호환: from core.models import PatientDocument 가능
    # → 파일 하단의 PatientDocument = DocumentInfo 참조

    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), nullable=True, index=True)
    doc_type = Column(String, index=True)    # ps, sr, ct, tx, rc, rt, bc(사업자등록증)
    directory = Column(String)               # 파일 저장 폴더 경로
    generated_filename = Column(String, unique=True)
    issue_date = Column(String)              # 파일명 추출 날짜 (YYYYMMDD)
    file_status = Column(String)             # COPIED, OCR_DONE, FILTERED
    created_at = Column(DateTime, server_default=func.now())


class Prescription(RuntimeBase):
    """처방전 상세 데이터 (PS)"""
    __tablename__ = "prescriptions"

    ps_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    issue_date = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    duration = Column(Integer)

    device_type = Column(String)             # CPAP, APAP, BiPAP
    pressure_val1 = Column(Float)            # CPAP(압력), APAP(min), BiPAP(IPAP)
    pressure_val2 = Column(Float)            # APAP(max), BiPAP(EPAP)

    is_post_compliance = Column(Boolean)     # 순응 후 처방 여부
    comp_eval_start_date = Column(DateTime)  # 30일 사용 시작일
    comp_eval_pass_date = Column(DateTime)   # 30일 통과일
    comp_over_4h_days = Column(Integer)      # 4시간 이상 사용일수

    doctor_name = Column(String)
    doctor_license = Column(String)
    hosp_name = Column(String)
    hosp_code = Column(String)


class SleepReport(RuntimeBase):
    """수면보고서 데이터 (SR)"""
    __tablename__ = "sleep_reports"

    sr_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    report_start_date = Column(DateTime, nullable=True)   # 보고서 대상 시작일
    report_end_date = Column(DateTime, nullable=True)     # 보고서 대상 종료일
    device_serial = Column(String)
    avg_usage_time = Column(Float)
    pressure_val1 = Column(Float)
    pressure_val2 = Column(Float)
    ahi = Column(Float)


class Contract(RuntimeBase):
    """양압기 계약서 데이터 (CT)"""
    __tablename__ = "contracts"

    ct_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    device_serial = Column(String)


class ReturnReceipt(RuntimeBase):
    """기기 반납 확인서 (RT)"""
    __tablename__ = "return_receipts"

    rt_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    return_date = Column(DateTime)


class TaxInvoice(RuntimeBase):
    """세금계산서 데이터 (TX)"""
    __tablename__ = "tax_invoices"

    ti_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"), nullable=True)
    ti_approval_num = Column(String)
    ti_issue_date = Column(DateTime)
    registration_num = Column(String)        # 주민/사업자번호
    total_amount = Column(Integer)
    attachment_path = Column(String)


class Receipt(RuntimeBase):
    """현금영수증 데이터 (RC)"""
    __tablename__ = "receipts"

    rc_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"), nullable=True)
    rcpt_approval_num = Column(String)
    rcpt_issue_date = Column(DateTime)
    registration_num = Column(String)
    total_amount = Column(Integer)
    attachment_path = Column(String)


class Consumable(RuntimeBase):
    """소모품 지급 이력"""
    __tablename__ = "consumables"

    c_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    c_type = Column(String)               # 마스크, 튜브, 필터, …
    c_detail_type = Column(String)         # 세부 유형
    c_price = Column(Integer)              # 금액 (건보=*0.8, 본인=*0.2 로 계산)
    c_note = Column(String, nullable=True) # "신규", "마스크 교체 1회" 등
    purchase_date = Column(DateTime)


class Travel(RuntimeBase):
    """해외여행 이력"""
    __tablename__ = "travels"

    t_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    depart_date = Column(DateTime)         # 출국일
    entry_date = Column(DateTime)          # 입국일
    return_record_path = Column(String)


class MonthlyUpdate(RuntimeBase):
    """환자별 월간 변동 및 문서 연결 마스터"""
    __tablename__ = "monthly_updates"
    __table_args__ = (
        UniqueConstraint("pat_id", "target_month", name="uq_mu_pat_month"),
        Index("ix_mu_target_month", "target_month"),
    )

    mu_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    target_month = Column(String(7), nullable=False)   # "2026-03"

    comp_status = Column(String, default="PASS")          # STARTED / IN_PROGRESS / PASS
    register_status = Column(String, default="ACTIVE")    # ACTIVE / TERMINATED

    # 문서 및 비용 증빙 연결 (해당 월에 사용된 원본 레코드)
    tax_id = Column(Integer, ForeignKey("tax_invoices.ti_id"), nullable=True)
    rcpt_id = Column(Integer, ForeignKey("receipts.rc_id"), nullable=True)
    ps_id = Column(Integer, ForeignKey("prescriptions.ps_id"), nullable=True)
    sr_id = Column(Integer, ForeignKey("sleep_reports.sr_id"), nullable=True)
    ct_id = Column(Integer, ForeignKey("contracts.ct_id"), nullable=True)
    rt_id = Column(Integer, ForeignKey("return_receipts.rt_id"), nullable=True)
    consumable_id = Column(Integer, ForeignKey("consumables.c_id"), nullable=True)
    travel_id = Column(Integer, ForeignKey("travels.t_id"), nullable=True)

    # 청구 분할
    split_claim_count = Column(Integer, default=1)
    # → claims.claim_id (순환 FK 회피: FK 제약 없이 Integer로 저장)
    claim_id_1 = Column(Integer, nullable=True)
    claim_id_2 = Column(Integer, nullable=True)
    claim_id_3 = Column(Integer, nullable=True)

    status = Column(String, default="PENDING")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Claim(RuntimeBase):
    """최종 청구 생성 데이터 — 분할 시 환자 1인당 최대 3건/월
    병원/의사 정보는 ps_id → prescriptions 테이블에서 직접 조회.
    """
    __tablename__ = "claims"
    __table_args__ = (
        Index("ix_claims_target_month", "target_month"),
    )

    claim_id = Column(Integer, primary_key=True, autoincrement=True)
    mu_id = Column(Integer, ForeignKey("monthly_updates.mu_id"))
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    ps_id = Column(Integer, ForeignKey("prescriptions.ps_id"), nullable=True)
    target_month = Column(String(7), nullable=False)   # "2026-03"

    # 청구 기간 (분할 시 부분 기간)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    period_days = Column(Integer, nullable=True)
    split_reason = Column(String, nullable=True)       # FULL / RX_BEFORE / RX_AFTER
                                                       # / TRAVEL_BEFORE / TRAVEL_AFTER

    billing_rate = Column(Integer, default=50)         # 50 or 80

    # 기본 청구액 (일할계산 적용된 값)
    base_total = Column(Integer)
    base_insurance = Column(Integer)
    base_self_pay = Column(Integer)

    # 해외출국 공제
    travel_deduct_days = Column(Integer, default=0)
    travel_deduct_amount = Column(Integer, default=0)

    # 반납월 공제 → 본인부담금 전환
    return_deduct_to_self = Column(Integer, default=0)

    # 최종 금액
    total_amount = Column(Integer)
    final_insurance = Column(Integer)
    final_self_pay = Column(Integer)

    # 첨부파일 tracking (쉼표구분 doc_type 목록)
    required_docs = Column(String, default="")         # "PS,SR" / "SR,TX,RC,CT" 등
    attached_docs = Column(String, default="")         # 첨부 완료된 doc types
    sr_count_required = Column(Integer, default=0)     # 필요 수면보고서 수 (순응통과달: 2)
    sr_count_attached = Column(Integer, default=0)     # 첨부 완료 장수

    status = Column(String, default="READY")
    created_at = Column(DateTime, server_default=func.now())

    prescription = relationship("Prescription", foreign_keys=[ps_id], lazy="joined")


class PatientAlert(RuntimeBase):
    """환자관리사항 — 자동감지(처방전만료·순응90일·여행 등) + 수동등록"""
    __tablename__ = "patient_alerts"
    __table_args__ = (
        Index("ix_alert_target_month", "target_month"),
    )

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"), index=True)
    alert_type = Column(String)           # RX_EXPIRY / COMP_90D / TRAVEL / MASK_REPLACE / …
    target_month = Column(String(7))      # "2026-03" (대시보드에 표시할 월)
    description = Column(String)
    due_date = Column(Date, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ExtractedData(RuntimeBase):
    """OCR 추출 데이터 임시 버퍼"""
    __tablename__ = "extracted_data"

    data_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"), index=True)
    raw_key = Column(String)
    raw_value = Column(String)
    confidence = Column(Float)
    is_confirmed = Column(Integer, default=0)


class WorkflowSession(RuntimeBase):
    """워크플로우 세션 진행상황 추적"""
    __tablename__ = "workflow_sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    op_id = Column(Integer, nullable=False, index=True)
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="RUNNING")         # RUNNING / COMPLETED / FAILED
    current_step = Column(String(100), nullable=True)
    completed_steps = Column(Text, default="")
    error_message = Column(Text, nullable=True)


# ── 하위 호환 alias ──
PatientDocument = DocumentInfo   # 기존 코드에서 import PatientDocument 계속 사용 가능
Hospital = FrequentHospital      # 기존 코드에서 import Hospital 계속 사용 가능
