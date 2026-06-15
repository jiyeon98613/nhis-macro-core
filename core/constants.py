# core/constants.py
"""
core/constants.py — 프로젝트 전역 상수
========================================
매직 스트링 제거를 위한 중앙 상수 관리 모듈.
문서 타입, 감사 로그 액션, 파일 상태 등을 정의.

사용법:
    from core.constants import DocType, AuditAction
    doc_type = DocType.PRESCRIPTION
"""

from enum import Enum


# 문서 타입 코드 (7종 — DocumentInfo.doc_type 전용, PLAN_ASSET_MODEL §8.5)
class DocType(str, Enum):
    PRESCRIPTION = "ps"
    SLEEP_REPORT = "sr"
    CONTRACT = "ct"
    TAX_INVOICE = "tx"
    RECEIPT = "rc"
    RETURN_RECEIPT = "rt"
    ETC = "etc"

    # 하위 호환 alias (PRESCRIPTION_POST/prscrpt_pass 제거)
    PRESCRIPTION_PRE = "ps"

    def __str__(self) -> str:
        return str(self.value)


# 감사 로그 액션 코드
class AuditAction:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAIL = "LOGIN_FAIL"
    DEVICE_AUTH_SUCCESS = "DEVICE_AUTH_SUCCESS"
    DEVICE_AUTH_FAIL = "DEVICE_AUTH_FAIL"
    WORKFLOW_COMPLETE = "WORKFLOW_COMPLETE"
    WORKFLOW_ERROR = "WORKFLOW_ERROR"
    PATIENT_CREATE = "PATIENT_CREATE"
    EXCEL_IMPORT_START = "EXCEL_IMPORT_START"
    CREATE_ADMIN = "CREATE_ADMIN"
    OCR_SCAN_START = "OCR_SCAN_START"
    OCR_SCAN_COMPLETE = "OCR_SCAN_COMPLETE"
    OCR_MANUAL_INPUT = "OCR_MANUAL_INPUT"
    SESSION_START = "SESSION_START"
    SESSION_RESUME_CHECK = "SESSION_RESUME_CHECK"
    MONTHLY_UPDATE_START = "MONTHLY_UPDATE_START"
    MONTHLY_UPDATE_COMPLETE = "MONTHLY_UPDATE_COMPLETE"
    BIZ_NUM_REGISTER = "BIZ_NUM_REGISTER"
    PATIENT_RRN_VIEW = "PATIENT_RRN_VIEW"   # 전체 주민번호 조회(admin) 감사


# 파일 상태
class FileStatus:
    COPIED = "COPIED"
    OCR_DONE = "OCR_DONE"
    OCR_FAILED = "OCR_FAILED"
    VERIFIED = "VERIFIED"
    FILTERED = "FILTERED"
    EXCEL = "EXCEL"   # Excel import stub (파일 없음, OCR pending 제외)


# 환자 등록 상태
class RegisterStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


# 운영자 역할
class Role:
    ADMIN = "ADMIN"
    STAFF = "STAFF"


# 승인 범위
class ApprovalScope:
    OCR_CONFIRM = "OCR_CONFIRM"
    BATCH_SAVE = "BATCH_SAVE"
    DELETE_LOG = "DELETE_LOG"
    FINAL_SUBMIT = "FINAL_SUBMIT"
    MONTHLY_UPDATE = "MONTHLY_UPDATE"


# OCR 엔진 종류
class OCRProvider:
    TESSERACT = "TESSERACT"
    NAVER = "NAVER"       # 미구현
    GOOGLE = "GOOGLE"     # 미구현
