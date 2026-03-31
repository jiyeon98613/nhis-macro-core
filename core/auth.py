# core/auth.py
"""
core/auth.py — 기기 인증 및 Vendor/Operator 검증
==================================================
현재 PC의 HWID와 Vendor.device_hwid를 대조하여
인가된 기기에서만 프로그램이 실행되도록 함.

engine의 AuthStep에서 호출.
"""

from typing import Optional

from core.db_manager import db
from core.models import Vendor, Operator, FrequentHospital, BusinessCertificate
from core.security import get_hwid, SecurityManager
import yaml


def load_hosp_code(config_path: str, key_path: str) -> str:
    """config.yaml에서 암호화된 병원 코드를 읽어 복호화하여 반환"""
    sm = SecurityManager(key_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return sm.decrypt_data(config['hospital']['target_code'])


def validate_device() -> Optional[Vendor]:
    """HWID 기반 기기 인증 — 인증 성공 시 Vendor 객체 반환, 실패 시 None"""
    session = db.get_onboarding_session()
    current_hwid = get_hwid()
    try:
        vendor = session.query(Vendor).filter(Vendor.device_hwid == current_hwid).first()
        if not vendor:
            return None
        return vendor
    finally:
        session.close()


def register_vendor(vendor_name: str, biz_num: str = None) -> Vendor:
    """신규 Vendor 등록 + 현재 PC HWID 바인딩"""
    session = db.get_onboarding_session()
    current_hwid = get_hwid()
    try:
        vendor = Vendor(
            vendor_name=vendor_name,
            biz_num=biz_num,
            device_hwid=current_hwid,
        )
        session.add(vendor)
        session.commit()
        session.refresh(vendor)
        return vendor
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_vendor_bc(vendor: Vendor) -> Optional[BusinessCertificate]:
    """Vendor의 사업자등록증 등록 여부 확인"""
    if not vendor.bc_id:
        return None
    session = db.get_onboarding_session()
    try:
        return session.query(BusinessCertificate).filter(
            BusinessCertificate.bc_id == vendor.bc_id
        ).first()
    finally:
        session.close()


def login_operator(phone_num: str, password: str) -> Optional[Operator]:
    """Operator 로그인 (phone_num + password 검증)"""
    from core.security import verify_password
    session = db.get_onboarding_session()
    try:
        op = session.query(Operator).filter(
            Operator.phone_num == phone_num,
            Operator.is_active == 1,
        ).first()
        if not op or not op.security:
            return None
        if verify_password(password, op.security.password_hash):
            return op
        return None
    finally:
        session.close()


def register_frequent_hospital(hosp_code: str, hosp_name: str) -> FrequentHospital:
    """단골병원(FrequentHospital) 등록"""
    session = db.get_onboarding_session()
    try:
        existing = session.query(FrequentHospital).filter(
            FrequentHospital.hosp_code == hosp_code
        ).first()
        if existing:
            return existing
        fh = FrequentHospital(hosp_code=hosp_code, hosp_name=hosp_name)
        session.add(fh)
        session.commit()
        session.refresh(fh)
        return fh
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
