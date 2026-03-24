# core/auth.py
"""
core/auth.py — 기기 인증 및 병원 코드 복호화
=============================================
config.yaml의 암호화된 병원 코드를 복호화하고,
현재 PC의 HWID가 등록된 기기인지 검증.

engine의 AuthStep에서 호출.
"""

from typing import Optional

from core.db_manager import db
from core.models import Hospital
from core.security import get_hwid, SecurityManager
import yaml


def load_hosp_code(config_path: str, key_path: str) -> str:
    """config.yaml에서 암호화된 병원 코드를 읽어 복호화하여 반환"""
    sm = SecurityManager(key_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return sm.decrypt_data(config['hospital']['target_code'])


def validate_license(hosp_code: str) -> Optional[Hospital]:
    """HWID 기반 기기 인증 — 인증 성공 시 Hospital 객체 반환, 실패 시 None"""
    session = db.get_onboarding_session()
    current_hwid = get_hwid()
    try:
        hosp = session.query(Hospital).filter(Hospital.hosp_code == hosp_code).first()
        if not hosp:
            print("❌ 인증 에러: 등록되지 않은 병원 코드입니다.")
            return None
        if hosp.device_hwid != current_hwid:
            print("🛑 보안 경고: 인증되지 않은 기기에서 실행되었습니다. (불법 복제 의심)")
            return None
        print(f"✅ 기기 인증 완료: {hosp.hosp_name}")
        return hosp
    finally:
        session.close()
