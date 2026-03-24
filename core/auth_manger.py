# core/auth_manager.py
from core.db_manager import db
from core.models import Operator, SecuritySetting
from core.security import verify_password
from datetime import datetime

class AuthManager:
    __current_user = None

    @classmethod
    def login(cls):
        """사용자로부터 ID/PW를 입력받아 로그인을 수행합니다."""
        print("\n" + "="*40)
        print("🔐 NHIS Macro 시스템 로그인")
        print("="*40)
        
        email = input("👉 이메일(ID): ").strip()
        password = input("👉 비밀번호: ").strip()

        session = db.get_onboarding_session()
        try:
            # 1. 운영자 존재 확인
            op = session.query(Operator).filter_by(email=email, is_active=1).first()
            if not op:
                print("❌ 등록되지 않았거나 비활성화된 계정입니다.")
                return False

            # 2. 비밀번호 검증
            sec = session.query(SecuritySetting).filter_by(op_id=op.op_id).first()
            if sec and verify_password(password, sec.password_hash):
                cls.__current_user = {
                    "op_id": op.op_id,
                    "name": op.name,
                    "role": op.role
                }
                # 로그인 성공 로그 (db_manager의 개선된 log_event 호출)
                db.log_event(op_id=op.op_id, action="LOGIN_SUCCESS", reason="System Access")
                print(f"✅ 인증 성공: {op.name}님 환영합니다.")
                return True
            else:
                print("❌ 비밀번호가 일치하지 않습니다.")
                db.log_event(op_id=op.op_id if op else 0, action="LOGIN_FAIL", reason="Wrong Password")
                return False
        finally:
            session.close()

    @classmethod
    def get_current_user(cls):
        """읽기 전용 복사본 반환 — 원본 딕셔너리 수정 불가"""
        if cls.__current_user is None:
            return None
        return dict(cls.__current_user)  # ② 복사본 반환
    
    @classmethod
    def logout(cls):
        """로그아웃은 명시적 메서드로만 가능"""
        cls.__current_user = None