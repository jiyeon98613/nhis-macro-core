"""
core/models.py — SQLAlchemy ORM 모델 정의
=============================================
- OnboardingBase: 병원·의사·운영자·사업자등록 등 기준 정보 (onboarding.db)
- RuntimeBase: 환자·문서·청구 등 실행 데이터 (runtime.db)

PK/FK: UUID String(36), default=lambda: str(uuid.uuid4())
"""

import uuid

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, ForeignKey,
    Text, Float, Boolean, Index, UniqueConstraint, CheckConstraint, Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.db_manager import OnboardingBase, RuntimeBase
from core.org_context import get_default_org_id
from core.constants import DocType


def _uuid_pk() -> Column:
    return Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


class OrgMixin:
    # tenant 식별자. 기본값은 core.org_context (앱 시작 시 config 값 주입, 미주입 시 fallback).
    org_id = Column(String, default=lambda: get_default_org_id())


class AuditMixin:
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class CreatedAtMixin:
    created_at = Column(DateTime, server_default=func.now())


# =================================================================
# 1. Onboarding Data (기준 정보 - onboarding.db)
# =================================================================


class FrequentHospital(OrgMixin, AuditMixin, OnboardingBase):
    """자주 사용하는 요양기관 즐겨찾기 — 처방전 입력 자동완성용"""
    __tablename__ = "frequent_hospitals"

    fh_id = _uuid_pk()
    hosp_code = Column(String, unique=True, nullable=False)
    hosp_name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Manufacturer(OrgMixin, AuditMixin, OnboardingBase):
    """양압기 제조/수입사"""
    __tablename__ = "manufacturers"

    man_id = _uuid_pk()
    man_name = Column(String, nullable=False, unique=True)
    country = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class Vendor(OrgMixin, AuditMixin, OnboardingBase):
    """양압기 렌탈 및 유지관리업체"""
    __tablename__ = "vendors"

    vendor_id = _uuid_pk()
    vendor_name = Column(String, nullable=False)
    device_hwid = Column(String, nullable=True)
    manager_name = Column(String)
    contact = Column(String)
    biz_num = Column(String, unique=True, nullable=False)
    company_name = Column(String)
    rep_name = Column(String)
    address = Column(String)
    biz_type = Column(String)
    biz_item = Column(String)
    email = Column(String)
    bc_doc_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ManManagerList(OrgMixin, AuditMixin, CreatedAtMixin, OnboardingBase):
    """제조사 담당자"""
    __tablename__ = "man_manager_list"

    man_manager_id = _uuid_pk()
    man_id = Column(String(36), ForeignKey("manufacturers.man_id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    dept = Column(String, nullable=True)        # sales/repair/etc (앱검증)
    email = Column(String, nullable=True)


class Operator(OrgMixin, AuditMixin, CreatedAtMixin, OnboardingBase):
    """시스템 운영자 계정"""
    __tablename__ = "operators"

    op_id = _uuid_pk()
    vendor_id = Column(String(36), ForeignKey("vendors.vendor_id"), nullable=True)
    name = Column(String(50), nullable=False)
    phone_num = Column(String(20), unique=True)
    email = Column(String(100))
    role = Column(String(20))
    is_active = Column(Integer, default=1)
    security = relationship("SecuritySetting", back_populates="operator", uselist=False)


class AuditLog(OrgMixin, AuditMixin, CreatedAtMixin, OnboardingBase):
    __tablename__ = "audit_logs"

    log_id = _uuid_pk()
    op_id = Column(String(36), ForeignKey("operators.op_id"))
    action = Column(String(100))
    target_id = Column(String(36), nullable=True)
    reason = Column(String(500))
    access_time = Column(DateTime, server_default=func.now())


class SecuritySetting(OrgMixin, AuditMixin, CreatedAtMixin, OnboardingBase):
    __tablename__ = "security_settings"

    ss_id = _uuid_pk()
    op_id = Column(String(36), ForeignKey("operators.op_id"), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    password_set_at = Column(DateTime, server_default=func.now())
    password_snooze_until = Column(DateTime, nullable=True)
    operator = relationship("Operator", back_populates="security")


class Approval(OrgMixin, AuditMixin, CreatedAtMixin, OnboardingBase):
    """관리자 승인 기록"""
    __tablename__ = "approvals"

    approval_id = _uuid_pk()
    scope = Column(String, nullable=False)
    target_id = Column(String(36), nullable=False)
    approved_by = Column(String(36), ForeignKey("operators.op_id"), nullable=False)
    approved_at = Column(DateTime, server_default=func.now())
    detail = Column(Text)


class DocumentTemplate(OrgMixin, AuditMixin, OnboardingBase):
    """문서 양식 정의 (6종 대응)"""
    __tablename__ = "document_templates"
    __table_args__ = (
        UniqueConstraint("org_id", "doc_type", "identifier_keyword", name="uq_doctemp_org_type_keyword"),
    )

    temp_id = _uuid_pk()
    hosp_code = Column(String, nullable=True)
    temp_name = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)
    vendor_name = Column(String)
    identifier_keyword = Column(String)
    confidence_policy = Column(String, nullable=False)
    approved = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    fields = relationship("DocumentField", back_populates="template")


class DocumentField(OrgMixin, AuditMixin, OnboardingBase):
    """양식별 추출 필드 정의"""
    __tablename__ = "document_fields"

    field_id = _uuid_pk()
    temp_id = Column(String(36), ForeignKey("document_templates.temp_id"), nullable=False)
    field_name = Column(String, nullable=False)
    field_type = Column(String, nullable=False)
    extract_method = Column(String, nullable=False)
    extract_rule = Column(String)
    is_required = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    template = relationship("DocumentTemplate", back_populates="fields")


# =================================================================
# 2. Runtime Data (실행 정보 - runtime.db)
# =================================================================


class SystemLog(OrgMixin, AuditMixin, RuntimeBase):
    """프로그램 내부 오류 및 실행 상태 로깅"""
    __tablename__ = "system_logs"

    id = _uuid_pk()
    level = Column(String(20))
    step_name = Column(String(100))
    message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class Patient(OrgMixin, AuditMixin, RuntimeBase):
    """환자 기본 인적사항 및 고정 정보"""
    __tablename__ = "patients"
    __table_args__ = (
        # 테넌트-로컬: 차트번호는 병원마다 독립 채번 → org 범위 내 유일
        UniqueConstraint("org_id", "chart_num", name="uq_patient_org_chart"),
    )

    pat_id = _uuid_pk()
    pat_name = Column(String, nullable=False, index=True)
    chart_num = Column(String, nullable=False)
    reg_num_front = Column(String(6), index=True)
    reg_num_back = Column(String(7))
    phone_num = Column(String)
    # 소프트 방침(CHECK 미적용 확정, 2026-06-13): DB CHECK 제약을 추가하지 않는다.
    #   사유: OCR 자동등록/엑셀 임포트 시 잘못된 폰을 막지 않고 정규화값 그대로 저장 →
    #   대시보드에서 phone_valid=False(빨강)로 가시화·수동 보정. NOT NULL 아님(빈값 허용).
    #   형식 검증은 표시 계층(patients.list_patients의 phone_valid)만 담당, 저장은 무조건 허용.
    address = Column(String)
    address_detail = Column(String(200), nullable=True)
    birth_date = Column(Date, nullable=True)
    uses_biz_num = Column(Boolean, default=False)
    biz_num = Column(String, nullable=True)
    pbc_id = Column(String(36), ForeignKey("patient_business_certificates.pbc_id"), nullable=True)
    is_auto_registered = Column(Boolean, default=False, nullable=False)
    # True = OCR 승인 시 자동생성 신환. chart_num = "AUTO-{pat_id[:8]}" (임시).
    created_at = Column(DateTime, server_default=func.now())


class PatientBC(OrgMixin, AuditMixin, RuntimeBase):
    """환자 사업자등록 관련 데이터"""
    __tablename__ = "patient_business_certificates"

    pbc_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), nullable=False, index=True)
    biz_num = Column(String, unique=True, nullable=False)
    company_name = Column(String)
    rep_name = Column(String)
    address = Column(String)
    biz_type = Column(String)
    biz_item = Column(String)
    email = Column(String)
    doc_path = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class DocumentInfo(OrgMixin, AuditMixin, RuntimeBase):
    """문서 파일 메타데이터 및 저장 경로 관리"""
    __tablename__ = "patient_documents"
    __table_args__ = (
        # 테넌트-로컬: 생성 파일명은 스토리지가 org별로 분리됨 → org 범위 내 유일
        UniqueConstraint("org_id", "generated_filename", name="uq_docinfo_org_filename"),
    )

    doc_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), nullable=True, index=True)
    doc_type = Column(
        SQLEnum(DocType, values_callable=lambda e: [m.value for m in e], native_enum=False),
        index=True,
    )
    directory = Column(String)
    generated_filename = Column(String)
    issue_date = Column(String)
    file_status = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class Prescription(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """처방전 상세 데이터 (PS)"""
    __tablename__ = "prescriptions"

    ps_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(String(36), ForeignKey("patient_documents.doc_id"))
    issue_date = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    duration = Column(Integer)
    device_type = Column(String)
    pressure_val1 = Column(Float)
    pressure_val2 = Column(Float)
    is_post_compliance = Column(Boolean)
    comp_eval_start_date = Column(DateTime)
    comp_eval_pass_date = Column(DateTime)
    comp_over_4h_days = Column(Integer)
    doctor_name = Column(String)
    doctor_license = Column(String)
    hosp_name = Column(String)
    hosp_code = Column(String)
    disease_code = Column(String, nullable=True)
    disease_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    serial_num = Column(String, nullable=True)
    specialist_num = Column(String, nullable=True)
    superseded_by_ps_id = Column(String(36), ForeignKey("prescriptions.ps_id"), nullable=True)
    superseded_date = Column(Date, nullable=True)


class SleepReport(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """수면보고서 데이터 (SR)"""
    __tablename__ = "sleep_reports"

    sr_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(String(36), ForeignKey("patient_documents.doc_id"))
    report_start_date = Column(DateTime, nullable=True)
    report_end_date = Column(DateTime, nullable=True)
    device_serial = Column(String)
    avg_usage_time = Column(Float)
    pressure_val1 = Column(Float)
    pressure_val2 = Column(Float)
    ahi = Column(Float)
    manufacturer = Column(String, nullable=True)
    usage_days = Column(Integer, nullable=True)
    total_days = Column(Integer, nullable=True)
    over_4h_days = Column(Integer, nullable=True)
    mode = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    linked_ps_id = Column(String(36), ForeignKey("prescriptions.ps_id"), nullable=True, index=True)
    report_month = Column(String(7), nullable=True)
    compliance_status = Column(String(20), nullable=True)


class Contract(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """양압기 계약서 데이터 (CT)"""
    __tablename__ = "contracts"

    ct_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(String(36), ForeignKey("patient_documents.doc_id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    device_serial = Column(String)
    rental_fee = Column(Integer, nullable=True)
    device_dn = Column(Integer, nullable=True)
    model_name = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    mask_fee = Column(Integer, nullable=True)
    contact = Column(String, nullable=True)


class ReturnReceipt(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """기기 반납 확인서 (RT)"""
    __tablename__ = "return_receipts"

    rt_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(String(36), ForeignKey("patient_documents.doc_id"))
    return_date = Column(DateTime)
    device_serial = Column(String, nullable=True)
    valid_until = Column(Date, nullable=True)
    billing_restarted_at = Column(DateTime, nullable=True)
    restarted_by_op_id = Column(String(36), nullable=True)


class TaxInvoice(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """세금계산서 데이터 (TX)"""
    __tablename__ = "tax_invoices"

    ti_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(String(36), ForeignKey("patient_documents.doc_id"), nullable=True)
    ti_approval_num = Column(String)
    ti_issue_date = Column(DateTime)
    registration_num = Column(String)
    total_amount = Column(Integer)
    attachment_path = Column(String)


class Receipt(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """현금영수증 데이터 (RC)"""
    __tablename__ = "receipts"

    rc_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    doc_id = Column(String(36), ForeignKey("patient_documents.doc_id"), nullable=True)
    rcpt_approval_num = Column(String)
    rcpt_issue_date = Column(DateTime)
    registration_num = Column(String)
    total_amount = Column(Integer)
    attachment_path = Column(String)


class ProductCatalog(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """제조사별 제품 모델 마스터 (기기·소모품 통합 카탈로그, runtime.db)"""
    __tablename__ = "product_catalog"
    __table_args__ = (
        UniqueConstraint("org_id", "man_id", "model_name", name="uq_catalog_org_man_model"),
        Index("ix_product_catalog_man_id", "man_id"),
    )

    catalog_id = _uuid_pk()
    man_id = Column(String(36), nullable=True)   # cross-DB soft-ref → manufacturers
    category = Column(String, nullable=False)   # DEVICE | CONSUMABLE (앱검증)
    kind = Column(String, nullable=False)       # APAP/CPAP/BiPAP/MASK/TUBE/FILTER… (앱검증)
    model_name = Column(String, nullable=False)
    nhis_code = Column(String, nullable=True)
    replace_cycle_days = Column(Integer, nullable=True)
    default_price = Column(Integer, nullable=True)


class ProductInstance(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """제품 개체 (시리얼 단위). 기존 devices/Device 대체."""
    __tablename__ = "product_instances"

    instance_id = _uuid_pk()
    catalog_id = Column(String(36), ForeignKey("product_catalog.catalog_id"), nullable=False)
    sn = Column(String, nullable=True)          # 소모품은 NULL 허용
    dn = Column(String, nullable=True)
    vendor_id = Column(String(36), nullable=True, index=True)  # cross-DB soft-ref → vendors
    purchased_date = Column(Date, nullable=True)
    manufactured_date = Column(Date, nullable=True)


class Travel(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """해외여행 이력"""
    __tablename__ = "travels"
    __table_args__ = (
        Index("ix_travel_pat_dates", "pat_id", "depart_date", "entry_date"),
    )

    t_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    depart_date = Column(DateTime)
    entry_date = Column(DateTime)
    return_record_path = Column(String)
    rt_id = Column(String(36), ForeignKey("return_receipts.rt_id"), nullable=True)


class AssignedHistory(OrgMixin, AuditMixin, RuntimeBase):
    """기기·소모품 배정 이력 (device_assignments/DeviceAssignment 대체)"""
    __tablename__ = "assigned_history"
    __table_args__ = (
        Index("ix_ah_instance_id", "instance_id"),
        Index("ix_ah_pat_id", "pat_id"),
        Index("ix_ah_pat_assigned_date", "pat_id", "assigned_date"),
    )

    assigned_history_id = _uuid_pk()
    instance_id = Column(
        String(36), ForeignKey("product_instances.instance_id"), nullable=False,
    )
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), nullable=False)
    ct_id = Column(String(36), ForeignKey("contracts.ct_id"), nullable=True)
    assigned_date = Column(Date, nullable=False)
    returned_date = Column(Date, nullable=True)
    rt_id = Column(String(36), ForeignKey("return_receipts.rt_id"), nullable=True)


class CareHistory(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """기기·소모품 관리 이력 (세척·수리 등)"""
    __tablename__ = "care_history"
    __table_args__ = (
        Index("ix_ch_instance_id", "instance_id"),
        CheckConstraint(
            "((resp_manufacturer_id IS NOT NULL) + (resp_vendor_id IS NOT NULL)) = 1",
            name="ck_care_resp_exactly_one",
        ),
        CheckConstraint(
            "((handler_operator_id IS NOT NULL) + (handler_man_manager_id IS NOT NULL)) = 1",
            name="ck_care_handler_exactly_one",
        ),
    )

    care_history_id = _uuid_pk()
    instance_id = Column(
        String(36), ForeignKey("product_instances.instance_id"), nullable=False,
    )
    care_type = Column(String, nullable=False)         # manufacturer_repaired/sterilized… (앱검증)
    care_date = Column(Date, nullable=True)
    resp_manufacturer_id = Column(String(36), nullable=True)   # cross-DB soft-ref
    resp_vendor_id = Column(String(36), nullable=True)         # cross-DB soft-ref
    handler_operator_id = Column(String(36), nullable=True)    # cross-DB soft-ref
    handler_man_manager_id = Column(String(36), nullable=True)  # cross-DB soft-ref
    note = Column(String, nullable=True)


class MonthlyUpdate(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """환자별 월간 변동 및 문서 연결 마스터"""
    __tablename__ = "monthly_updates"
    __table_args__ = (
        UniqueConstraint("pat_id", "billing_month", name="uq_mu_pat_month"),
        Index("ix_mu_billing_month", "billing_month"),
    )

    mu_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    billing_month = Column(String(7), nullable=False)
    comp_status = Column(String, default="PASS")
    register_status = Column(String, default="ACTIVE")
    split_claim_count = Column(Integer, default=1)
    claim_id_1 = Column(String(36), nullable=True)
    claim_id_2 = Column(String(36), nullable=True)
    claim_id_3 = Column(String(36), nullable=True)
    status = Column(String, default="PENDING")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    records = relationship("MonthlyRecord", back_populates="monthly_update", lazy="select")


class MonthlyRecord(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """MonthlyUpdate ↔ 문서/배정/여행 M:N 정션 (PLAN_ASSET_MODEL §8.5)"""
    __tablename__ = "monthly_records"
    __table_args__ = (
        CheckConstraint(
            "((doc_id IS NOT NULL) + (assigned_history_id IS NOT NULL) + (travel_id IS NOT NULL)) = 1",
            name="ck_monthly_record_exactly_one",
        ),
        UniqueConstraint("mu_id", "doc_id", name="uq_mr_mu_doc"),
        UniqueConstraint("mu_id", "assigned_history_id", name="uq_mr_mu_assignment"),
        UniqueConstraint("mu_id", "travel_id", name="uq_mr_mu_travel"),
        Index("ix_monthly_records_mu_id", "mu_id"),
    )

    record_id = _uuid_pk()
    mu_id = Column(String(36), ForeignKey("monthly_updates.mu_id"), nullable=False)
    doc_id = Column(String(36), ForeignKey("patient_documents.doc_id"), nullable=True)
    assigned_history_id = Column(
        String(36), ForeignKey("assigned_history.assigned_history_id"), nullable=True,
    )
    travel_id = Column(String(36), ForeignKey("travels.t_id"), nullable=True)
    monthly_update = relationship("MonthlyUpdate", back_populates="records")


class OcrSession(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """PS/SR OCR workflow 다단계 진행 상태 추적 (Sprint 1, D2).

    한 업로드 문서(doc_id)당 하나의 OCR 처리 세션. status 로 단계 진행을 추적한다.
    상태 흐름:
        bbox_pending → local_pending → mask_pending → external_pending
                     → external_review → completed
        (각 단계 거부 시 *_rejected, NAVER 실패 시 external_failed 로 종료)

    ⚠️ cross-DB 참조 규약(기존 컨벤션 준수):
        operators / frequent_hospitals 는 onboarding.db, OcrSession 은 runtime.db →
        해당 참조는 ForeignKey 가 아니라 plain String(36) 으로 저장(soft ref).
        runtime.db 내부(patient_documents/patients/prescriptions/sleep_reports/monthly_updates)만 진짜 FK.
    """
    __tablename__ = "ocr_sessions"

    session_id = _uuid_pk()
    # 업로드 문서 1건 = 세션 1건 (runtime FK)
    doc_id = Column(String(36), ForeignKey("patient_documents.doc_id"),
                    nullable=False, index=True)

    status = Column(String(40), nullable=False, default="bbox_pending", index=True)

    # Step1: 관리자 조정 박스 (원본 픽셀좌표 JSON). null이면 yaml 기본 + anchor transform 사용
    adjusted_bboxes = Column(Text, nullable=True)

    # Step3: 로컬 OCR(EasyOCR) 결과 + 관리자 교정 + 환자/병원 매칭
    local_results = Column(Text, nullable=True)        # JSON {region: text}
    local_corrections = Column(Text, nullable=True)    # JSON 관리자 수정분
    local_reviewed_by = Column(String(36), nullable=True)   # → operators.op_id (onboarding, soft ref)
    local_reviewed_at = Column(DateTime, nullable=True)
    matched_pat_id = Column(String(36), ForeignKey("patients.pat_id"), nullable=True)
    pat_match_score = Column(Float, nullable=True)
    matched_fh_id = Column(String(36), nullable=True)       # → frequent_hospitals.fh_id (onboarding, soft ref)

    # Step5: 마스킹
    masked_image_path = Column(String, nullable=True)
    mask_reviewed_by = Column(String(36), nullable=True)    # → operators.op_id (soft ref)
    mask_reviewed_at = Column(DateTime, nullable=True)

    # Step6: NAVER CLOVA 외부 OCR + 검토
    external_called_at = Column(DateTime, nullable=True)
    external_response_time = Column(Float, nullable=True)
    external_results = Column(Text, nullable=True)          # JSON
    external_corrections = Column(Text, nullable=True)
    external_reviewed_by = Column(String(36), nullable=True)  # → operators.op_id (soft ref)
    external_reviewed_at = Column(DateTime, nullable=True)

    # 최종 산출물 추적 (runtime FK)
    final_prescription_id = Column(String(36), ForeignKey("prescriptions.ps_id"), nullable=True)
    final_sleep_report_id = Column(String(36), ForeignKey("sleep_reports.sr_id"), nullable=True)
    final_mu_id = Column(String(36), ForeignKey("monthly_updates.mu_id"), nullable=True)  # MU 자동생성(D3) 추적
    # updated_at / created_by / updated_by / deleted_at = AuditMixin, created_at = CreatedAtMixin (중복정의 금지)


class Claim(OrgMixin, AuditMixin, RuntimeBase):
    """최종 청구 생성 데이터"""
    __tablename__ = "claims"
    __table_args__ = (
        Index("ix_claims_billing_month", "billing_month"),
    )

    claim_id = _uuid_pk()
    mu_id = Column(String(36), ForeignKey("monthly_updates.mu_id"))
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    ps_id = Column(String(36), ForeignKey("prescriptions.ps_id"), nullable=True)
    billing_month = Column(String(7), nullable=False)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    period_days = Column(Integer, nullable=True)
    split_reason = Column(String, nullable=True)
    billing_rate = Column(Integer, default=50)
    base_total = Column(Integer)
    base_insurance = Column(Integer)
    base_self_pay = Column(Integer)
    travel_deduct_days = Column(Integer, default=0)
    travel_deduct_amount = Column(Integer, default=0)
    return_deduct_to_self = Column(Integer, default=0)
    total_amount = Column(Integer)
    final_insurance = Column(Integer)
    final_self_pay = Column(Integer)
    status = Column(String, default="READY")
    created_at = Column(DateTime, server_default=func.now())
    prescription = relationship("Prescription", foreign_keys=[ps_id])
    docs = relationship("ClaimDoc", back_populates="claim", lazy="select")


class ClaimDoc(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """청구별 첨부문서 추적"""
    __tablename__ = "claim_docs"

    cd_id = _uuid_pk()
    claim_id = Column(String(36), ForeignKey("claims.claim_id"), nullable=False, index=True)
    doc_type = Column(String(10), nullable=False)
    ps_id = Column(String(36), ForeignKey("prescriptions.ps_id"), nullable=True)
    sr_id = Column(String(36), ForeignKey("sleep_reports.sr_id"), nullable=True)
    ct_id = Column(String(36), ForeignKey("contracts.ct_id"), nullable=True)
    rt_id = Column(String(36), ForeignKey("return_receipts.rt_id"), nullable=True)
    is_required = Column(Boolean, default=True)
    is_attached = Column(Boolean, default=False)
    attached_at = Column(DateTime, nullable=True)
    required_reason = Column(String(50), nullable=True)
    claim = relationship("Claim", back_populates="docs")

    __table_args__ = (
        UniqueConstraint("claim_id", "doc_type", "ps_id", "sr_id", name="uq_claim_doc"),
    )


class PatientAlert(OrgMixin, AuditMixin, RuntimeBase):
    """환자관리사항"""
    __tablename__ = "patient_alerts"
    __table_args__ = (
        Index("ix_alert_billing_month", "billing_month"),
    )

    alert_id = _uuid_pk()
    pat_id = Column(String(36), ForeignKey("patients.pat_id"), index=True)
    alert_type = Column(String)
    billing_month = Column(String(7))
    description = Column(String)
    due_date = Column(Date, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ExtractedData(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """OCR 추출 데이터 임시 버퍼"""
    __tablename__ = "extracted_data"

    data_id = _uuid_pk()
    doc_id = Column(String(36), ForeignKey("patient_documents.doc_id"), index=True)
    raw_key = Column(String)
    raw_value = Column(String)
    confidence = Column(Float)
    is_confirmed = Column(Integer, default=0)


class WorkflowSession(OrgMixin, AuditMixin, CreatedAtMixin, RuntimeBase):
    """워크플로우 세션 진행상황 추적"""
    __tablename__ = "workflow_sessions"

    session_id = _uuid_pk()
    op_id = Column(String(36), nullable=False, index=True)
    started_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="RUNNING")
    current_step = Column(String(100), nullable=True)
    completed_steps = Column(Text, default="")
    error_message = Column(Text, nullable=True)


class WorkflowStepLog(OrgMixin, AuditMixin, RuntimeBase):
    """워크플로우 단계별 실행 로그"""
    __tablename__ = "workflow_step_logs"

    log_id = _uuid_pk()
    session_id = Column(String(36), ForeignKey("workflow_sessions.session_id"),
                        nullable=False, index=True)
    step_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ExcelImportSession(OrgMixin, AuditMixin, RuntimeBase):
    """Excel 환자 명단 임포트 세션"""
    __tablename__ = "excel_import_sessions"

    session_id = _uuid_pk()
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    first_data_row = Column(Integer, nullable=False)
    sample_patient_json = Column(Text, nullable=False)
    header_candidates_json = Column(Text, nullable=True)
    column_mapping_json = Column(Text, nullable=True)
    preview_rows_json = Column(Text, nullable=True)
    anomalies_json = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="preview", index=True)
    created_by_op_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by_op_id = Column(String(36), nullable=True)
    success_count = Column(Integer, nullable=True)
    failed_count = Column(Integer, nullable=True)
    failed_detail_json = Column(Text, nullable=True)


# ── 하위 호환 alias ──
PatientDocument = DocumentInfo
Hospital = FrequentHospital
