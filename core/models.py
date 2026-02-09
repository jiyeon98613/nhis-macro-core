from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from core.db_manager import Base

class Hospital(Base):
    __tablename__ = "hospitals"

    hosp_id = Column(Integer, primary_key=True, default=1)
    hosp_code = Column(String, unique=True, nullable=False)
    hosp_name = Column(String, nullable=False)
    device_hwid = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Operator(Base):
    __tablename__ = "operators"

    op_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    role = Column(String) # ADMIN, STAFF 등
    
    
class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    operator_name = Column(String)    # 누가
    action = Column(String)           # 어떤 행동을 (LOGIN, INSERT, UPDATE...)
    target_table = Column(String)     # 어디에 (hospitals, doctors...)
    details = Column(Text)            # 상세 내용 (JSON 형태 등)
    created_at = Column(DateTime, server_default=func.now()) # 언제
    
    
class Doctor(Base):
    __tablename__ = "doctors"

    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    hosp_id = Column(Integer, ForeignKey("hospitals.hosp_id")) # 외래키 연결
    hosp_code = Column(String(20))
    doc_name = Column(String, nullable=False)
    license_num = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class SecuritySetting(Base):
    __tablename__ = "security_settings"

    # id=1로 고정하여 단 하나의 설정만 존재하게 함
    id = Column(Integer, primary_key=True, default=1)
    password_hash = Column(String, nullable=False)
    password_set_at = Column(DateTime, server_default=func.now())
    last_login_at = Column(DateTime)

class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    temp_id = Column(Integer, primary_key=True, autoincrement=True)
    temp_name = Column(String, nullable=False)
    description = Column(Text)
    
class Field(Base):
    __tablename__ = "document_fields"
    
    field_id = Column(Integer, primary_key=True, autoincrement= True)
    temp_id = Column(Integer, ForeignKey("document_templates.temp_id")) # 어떤 템플릿의 필드인가
    field_name = Column(String, nullable=False)   # 예: '환자성명', '생년월일'
    field_type = Column(String)                   # 예: TEXT, DATE, NUMBER
    is_required = Column(Integer, default=1)      # 필수 여부 (1: 필수, 0: 선택)
    
class Approval(Base):
    __tablename__ = "approvals"

    appr_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer)                      # 연관된 문서 ID (나중에 문서 테이블 추가 시 FK 설정)
    approver_id = Column(Integer, ForeignKey("operators.op_id")) # 승인자
    status = Column(String, default="PENDING")    # PENDING, APPROVED, REJECTED
    comment = Column(Text)                        # 승인/반려 의견
    created_at = Column(DateTime, server_default=func.now())
    