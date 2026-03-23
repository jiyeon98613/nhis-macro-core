from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship, declarative_base  
from sqlalchemy.sql import func
from core.db_manager import Base
from datetime import datetime

Base = declarative_base()
# =================================================================
# 1. Onboarding Data (기준 정보 - onboarding.db)
# =================================================================

class Hospital(Base):
    """요양기관(병원) 마스터 정보"""
    __tablename__ = "hospitals"

    hosp_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_code = Column(String, unique=True, nullable=False) # 요양기관번호
    hosp_name = Column(String, nullable=False)
    device_hwid = Column(String, nullable=True)             # 승인된 PC 식별값
    created_at = Column(DateTime, server_default=func.now())

class Doctor(Base):
    """처방의 마스터 정보"""
    __tablename__ = "doctors"

    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_id = Column(Integer, ForeignKey("hospitals.hosp_id"))
    doc_name = Column(String, nullable=False)
    license_num = Column(String, unique=True, nullable=False) # 의사면허번호
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

class Manufacturer(Base):
    """양압기 제조/수입사 (예: 레즈메드, 필립스, 로벤스타인 등)"""
    __tablename__ = "manufacturers"

    man_id = Column(Integer, primary_key=True, autoincrement=True)
    man_name = Column(String, nullable=False, unique=True)
    country = Column(String) # 제조국
    created_at = Column(DateTime, server_default=func.now())

class Vendor(Base):
    """양압기 렌탈 및 유지관리업체 (소매상)"""
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_name = Column(String, nullable=False)
    biz_num = Column(String, unique=True) # 사업자등록번호
    manager_name = Column(String)         # 담당자 성함
    contact = Column(String)              # 연락처
    is_hospital_internal = Column(Boolean, default=False) # 병원 자체 관리 여부
    created_at = Column(DateTime, server_default=func.now())

class Device(Base):
    """양압기 기기 마스터 정보"""
    __tablename__ = "devices"

    dev_id = Column(Integer, primary_key=True, autoincrement=True)
    man_id = Column(Integer, ForeignKey("manufacturers.man_id")) # 제조사 연결
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id")) # 관리업체 연결
    serial_num = Column(String, unique=True, nullable=False)      # 기기번호
    device_type = Column(String)  # CPAP, APAP, BiPAP
    model_name = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class Operator(Base):
    """시스템 운영자 계정"""
    __tablename__ = "operators"

    op_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_id = Column(Integer, ForeignKey("hospitals.hosp_id"))
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True)
    role = Column(String(20)) # ADMIN, STAFF
    is_active = Column(Integer, default=1)
    security = relationship("SecuritySetting", back_populates="operator", uselist=False)

# =================================================================
# 2. Runtime Data (실행 정보 - runtime.db)
# =================================================================

class Patient(Base):
    """환자 기본 인적사항 및 고정 정보"""
    __tablename__ = "patients"

    pat_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_name = Column(String, nullable=False)
    chart_num = Column(String, unique=True, nullable=False)
    reg_num_front = Column(String(6))
    reg_num_back = Column(String(7))
    phone_num = Column(String)
    address = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class PatientDocument(Base):
    """문서 파일 메타데이터 및 저장 경로 관리"""
    __tablename__ = "patient_documents"

    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"))
    doc_type = Column(String)      # ps(처방전), sr(보고서), ct(계약서), tx(세금), rc(영수증), rt(반납)
    directory = Column(String)     # 파일 저장 폴더 경로
    generated_filename = Column(String, unique=True)
    issue_date = Column(String)    # 파일명 추출 날짜(YYYYMMDD)
    file_status = Column(String)   # COPIED, OCR_DONE, FILTERED
    created_at = Column(DateTime, server_default=func.now())

class Prescription(Base):
    """처방전 상세 데이터 (PS)"""
    __tablename__ = "prescriptions"

    ps_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    issue_date = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    duration = Column(Integer)
    
    device_type = Column(String)
    pressure_val1 = Column(Float) # CPAP(압력), APAP(min), BiPAP(IPAP)
    pressure_val2 = Column(Float) # APAP(max), BiPAP(EPAP)
    
    is_post_compliance = Column(Boolean)    # 순응 후 처방 여부
    comp_eval_start_date = Column(DateTime) # 30일 사용 시작일
    comp_eval_pass_date = Column(DateTime)  # 30일 통과일
    comp_over_4h_days = Column(Integer)     # 4시간 이상 사용일수
    
    doctor_name = Column(String)
    doctor_license = Column(String)
    hosp_name = Column(String)
    hosp_code = Column(String)

class SleepReport(Base):
    """수면보고서 데이터 (SR)"""
    __tablename__ = "sleep_reports"

    sr_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    device_serial = Column(String)
    avg_usage_time = Column(Float)
    pressure_val1 = Column(Float) 
    pressure_val2 = Column(Float) 
    ahi = Column(Float)

class Contract(Base):
    """임대차 계약서 데이터 (CT)"""
    __tablename__ = "contracts"

    ct_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    device_serial = Column(String)

class ReturnReceipt(Base):
    """기기 반납 확인서 (RT)"""
    __tablename__ = "return_receipts"

    rt_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    return_date = Column(DateTime)

class TaxInvoice(Base):
    """세금계산서 데이터 (TX)"""
    __tablename__ = "tax_invoices"

    ti_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"))
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"), nullable=True)
    ti_approval_num = Column(String)
    ti_issue_date = Column(DateTime)
    registration_num = Column(String) # 주민/사업자번호
    total_amount = Column(Integer)
    attachment_path = Column(String)

class Receipt(Base):
    """현금영수증 데이터 (RC)"""
    __tablename__ = "receipts"

    rc_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"))
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"), nullable=True)
    rcpt_approval_num = Column(String)
    rcpt_issue_date = Column(DateTime)
    registration_num = Column(String)
    total_amount = Column(Integer)
    attachment_path = Column(String)

class Consumable(Base):
    """소모품 지급 이력"""
    __tablename__ = "consumables"

    c_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"))
    c_type = Column(String)        
    c_detail_type = Column(String) 
    c_price = Column(Integer)
    purchase_date = Column(DateTime)

class Travel(Base):
    """해외여행 이력"""
    __tablename__ = "travels"

    t_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"))
    depart_date = Column(DateTime) # 출국일
    entry_date = Column(DateTime)  # 입국일
    return_record_path = Column(String)

class MonthlyUpdate(Base):
    """환자별 월간 변동 및 문서 연결 마스터"""
    __tablename__ = "monthly_updates"

    mu_id = Column(Integer, primary_key=True, autoincrement=True)
    pat_id = Column(Integer, ForeignKey("patients.pat_id"))
    yyyymm = Column(String(6), nullable=False)
    
    comp_status = Column(String, default="PASS")     
    register_status = Column(String, default="ACTIVE") 
    
    # 문서 및 비용 증빙 연결
    tax_id = Column(Integer, ForeignKey("tax_invoices.ti_id"), nullable=True)
    rcpt_id = Column(Integer, ForeignKey("receipts.rc_id"), nullable=True)
    ps_id = Column(Integer, ForeignKey("prescriptions.ps_id"), nullable=True)
    sr_id = Column(Integer, ForeignKey("sleep_reports.sr_id"), nullable=True)
    ct_id = Column(Integer, ForeignKey("contracts.ct_id"), nullable=True)
    rt_id = Column(Integer, ForeignKey("return_receipts.rt_id"), nullable=True)
    
    consumable_id = Column(Integer, ForeignKey("consumables.c_id"), nullable=True)
    travel_id = Column(Integer, ForeignKey("travels.t_id"), nullable=True)
    
    split_claim_count = Column(Integer, default=1) 

class Claim(Base):
    """최종 청구 생성 데이터"""
    __tablename__ = "claims"

    claim_id = Column(Integer, primary_key=True, autoincrement=True)
    mu_id = Column(Integer, ForeignKey("monthly_updates.mu_id"))
    billing_month = Column(String(6), index=True)
    billing_rate = Column(Integer, default=50) 
    total_amount = Column(Integer)
    status = Column(String, default="READY") 

class ExtractedData(Base):
    """OCR 추출 데이터 임시 버퍼"""
    __tablename__ = "extracted_data"

    data_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("patient_documents.doc_id"))
    raw_key = Column(String)
    raw_value = Column(String)
    confidence = Column(Float)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    op_id = Column(Integer, ForeignKey('operators.op_id')) # 누가(Operator ID)
    action = Column(String(100))                          # 무엇을(작업명)
    target_id = Column(Integer, nullable=True)            # 누구에게(환자 ID)
    reason = Column(String(500))                          # 왜/상세내용
    access_time = Column(DateTime, default=datetime.now)

class SecuritySetting(Base):
    __tablename__ = 'security_settings'
    
    id = Column(Integer, primary_key=True)
    op_id = Column(Integer, ForeignKey('operators.op_id'), unique=True, nullable=False) # 운영자와 연결
    password_hash = Column(String(255), nullable=False)
    password_set_at = Column(DateTime, default=datetime.now)
    # 관계 설정
    operator = relationship("Operator", back_populates="security")

class SystemLog(Base):
    """프로그램 내부 오류 및 실행 상태 로깅용 테이블"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20))     # INFO, ERROR, WARNING
    step_name = Column(String(100)) # 어느 단계에서 발생했는지
    message = Column(Text)         # 에러 메시지 내용
    created_at = Column(DateTime, default=datetime.now)