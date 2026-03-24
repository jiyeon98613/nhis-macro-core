# core/auth_manager.py
"""
core/auth_manager.py — 운영자 로그인 세션 관리
================================================
이메일/비밀번호 기반 로그인을 처리하고,
프로그램 실행 중 현재 사용자 정보를 유지.

AuthManager.login() → AuthManager.get_current_user() 순서로 사용.
"""

from typing import Optional

from core.db_manager import db
from core.models import Operator, SecuritySetting
from core.security import verify_password
from core.constants import AuditAction

class AuthManager:
    """로그인 세션 관리 — 클래스 변수로 현재 사용자를 유지합니다."""

    __current_user: Optional[dict] = None

    @classmethod
    def login(cls) -> bool:
        """사용자로부터 ID/PW를 입력받아 로그인을 수행합니다."""
        print("\n" + "=" * 40)
        print("🔐 NHIS Macro 시스템 로그인")
        print("=" * 40)

        email = input("👉 이메일(ID): ").strip()
        password = input("👉 비밀번호: ").strip()

        session = db.get_onboarding_session()
        try:
            op = session.query(Operator).filter_by(email=email, is_active=1).first()
            if not op:
                print("❌ 등록되지 않았거나 비활성화된 계정입니다.")
                return False

            sec = session.query(SecuritySetting).filter_by(op_id=op.op_id).first()
            if sec and verify_password(password, sec.password_hash):
                cls.__current_user = {
                    "op_id": op.op_id,
                    "name": op.name,
                    "role": op.role,
                }
                db.log_event(op_id=op.op_id, action=AuditAction.LOGIN_SUCCESS, reason="System Access")
                print(f"✅ 인증 성공: {op.name}님 환영합니다.")
                return True
            else:
                print("❌ 비밀번호가 일치하지 않습니다.")
                db.log_event(op_id=op.op_id, action=AuditAction.LOGIN_FAIL, reason="Wrong Password")
                return False
        finally:
            session.close()

    @classmethod
    def get_current_user(cls) -> Optional[dict]:
        """읽기 전용 복사본 반환 — 원본 딕셔너리 수정 불가"""
        if cls.__current_user is None:
            return None
        return dict(cls.__current_user)

    @classmethod
    def logout(cls) -> None:
        """로그아웃은 명시적 메서드로만 가능"""
        cls.__current_user = None