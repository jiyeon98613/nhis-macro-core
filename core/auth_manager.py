# core/auth_manager.py
"""
core/auth_manager.py — 운영자 로그인 세션 관리
================================================
전화번호/비밀번호 기반 로그인을 처리하고,
프로그램 실행 중 현재 사용자 정보를 유지.
비밀번호 만료(365일) 시 변경 안내, 스누즈(180일) 지원.

AuthManager.login() → AuthManager.get_current_user() 순서로 사용.
"""

from datetime import datetime, timedelta
from typing import Optional

from core.db_manager import db
from core.models import Operator, SecuritySetting
from core.security import verify_password, hash_password, validate_password_strength
from core.constants import AuditAction


# 기본값 (config_loader가 있으면 오버라이드 가능)
DEFAULT_EXPIRY_DAYS = 365
DEFAULT_SNOOZE_DAYS = 180


class AuthManager:
    """로그인 세션 관리 — 클래스 변수로 현재 사용자를 유지합니다."""

    __current_user: Optional[dict] = None

    @classmethod
    def login(cls) -> bool:
        """사용자로부터 전화번호/PW를 입력받아 로그인을 수행합니다."""
        print("\n" + "=" * 40)
        print("  NHIS Macro 시스템 로그인")
        print("=" * 40)

        phone = input("  전화번호(ID): ").strip()
        password = input("  비밀번호: ").strip()

        session = db.get_onboarding_session()
        try:
            op = session.query(Operator).filter_by(phone_num=phone, is_active=1).first()
            if not op:
                print("  등록되지 않았거나 비활성화된 계정입니다.")
                return False

            sec = session.query(SecuritySetting).filter_by(op_id=op.op_id).first()
            if not sec or not verify_password(password, sec.password_hash):
                print("  비밀번호가 일치하지 않습니다.")
                db.log_event(op_id=op.op_id, action=AuditAction.LOGIN_FAIL, reason="Wrong Password")
                return False

            # 로그인 성공
            cls.__current_user = {
                "op_id": op.op_id,
                "name": op.name,
                "role": op.role,
            }
            db.log_event(op_id=op.op_id, action=AuditAction.LOGIN_SUCCESS, reason="System Access")
            print(f"  인증 성공: {op.name}님 환영합니다.")

            # 비밀번호 만료 체크
            cls._check_password_expiry(sec, session)

            return True
        finally:
            session.close()

    @classmethod
    def _check_password_expiry(cls, sec: SecuritySetting, session) -> None:
        """비밀번호 만료 여부를 확인하고 변경을 안내합니다."""
        if not sec.password_set_at:
            return

        now = datetime.now()

        # 스누즈 기간 중이면 스킵
        if sec.password_snooze_until and now < sec.password_snooze_until:
            return

        days_since = (now - sec.password_set_at).days
        if days_since < DEFAULT_EXPIRY_DAYS:
            return

        # 만료됨 — 변경 안내
        print(f"\n  비밀번호를 설정한 지 {days_since}일이 지났습니다.")
        print("  보안을 위해 비밀번호 변경을 권장합니다.")
        print("  [1] 지금 변경  [2] 나중에")

        choice = input("  선택: ").strip()
        if choice == "1":
            cls._change_password(sec, session)
        else:
            # 스누즈: 180일 후 재안내
            sec.password_snooze_until = now + timedelta(days=DEFAULT_SNOOZE_DAYS)
            session.commit()
            print(f"  {DEFAULT_SNOOZE_DAYS}일 후에 다시 안내해 드리겠습니다.")

    @classmethod
    def _change_password(cls, sec: SecuritySetting, session) -> None:
        """비밀번호 변경 프로세스"""
        for _ in range(3):  # 최대 3회 시도
            new_pw = input("  새 비밀번호: ").strip()
            ok, reason = validate_password_strength(new_pw)
            if not ok:
                print(f"  {reason}")
                continue

            confirm = input("  새 비밀번호 확인: ").strip()
            if new_pw != confirm:
                print("  비밀번호가 일치하지 않습니다.")
                continue

            sec.password_hash = hash_password(new_pw)
            sec.password_set_at = datetime.now()
            sec.password_snooze_until = None
            session.commit()
            print("  비밀번호가 변경되었습니다.")
            return

        print("  비밀번호 변경을 건너뜁니다.")

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
