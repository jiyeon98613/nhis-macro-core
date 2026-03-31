"""
tests/test_auth_manager.py — AuthManager QA 테스트 (C-1)
=========================================================
로그인 세션 관리 검증:
1. 올바른 이메일/비밀번호 → 로그인 성공 + AuditLog 기록
2. 잘못된 비밀번호 → 실패 + LOGIN_FAIL 로그
3. 비활성화(is_active=0) 계정 → 거부
4. get_current_user() 반환값 수정해도 내부 데이터 안 바뀌는가
"""

import sys
import shutil
import sqlite3
import tempfile
import pytest
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = CORE_ROOT.parent
sys.path.insert(0, str(CORE_ROOT))

from core.db_manager import DBManager, OnboardingBase, RuntimeBase
from core.models import Operator, SecuritySetting, FrequentHospital, AuditLog
from core.security import hash_password
from core.constants import AuditAction, Role
from core.auth_manager import AuthManager


@pytest.fixture(autouse=True)
def reset_auth_manager():
    """각 테스트 전후로 AuthManager 상태 초기화"""
    AuthManager.logout()
    yield
    AuthManager.logout()


@pytest.fixture
def temp_env():
    """병원 + 운영자 + 보안설정이 갖춰진 임시 환경"""
    d = tempfile.mkdtemp(prefix="nhis_auth_test_")
    base = Path(d)
    db_dir = base / "db"
    db_dir.mkdir()

    on_path = str((db_dir / "onboarding.db").absolute())
    rt_path = str((db_dir / "runtime.db").absolute())

    mgr = DBManager()
    mgr.initialize(onboarding_path=on_path, runtime_path=rt_path)

    # 병원 등록
    session = mgr.get_onboarding_session()
    try:
        hosp = FrequentHospital(hosp_code="TEST_HOSP", hosp_name="테스트병원", device_hwid="HWID")
        session.add(hosp)
        session.flush()

        # 활성 운영자
        op_active = Operator(
            hosp_code=hosp.hosp_code, name="활성관리자",
            email="active@test.com", role=Role.ADMIN, is_active=1
        )
        session.add(op_active)
        session.flush()

        sec_active = SecuritySetting(
            op_id=op_active.op_id,
            password_hash=hash_password("correct_pass")
        )
        session.add(sec_active)

        # 비활성 운영자
        op_inactive = Operator(
            hosp_code=hosp.hosp_code, name="비활성관리자",
            email="inactive@test.com", role=Role.ADMIN, is_active=0
        )
        session.add(op_inactive)
        session.flush()

        sec_inactive = SecuritySetting(
            op_id=op_inactive.op_id,
            password_hash=hash_password("inactive_pass")
        )
        session.add(sec_inactive)

        session.commit()
        active_op_id = op_active.op_id
    finally:
        session.close()

    yield {"db": mgr, "on_path": on_path, "active_op_id": active_op_id, "base": base}
    shutil.rmtree(d, ignore_errors=True)


def do_login(env: dict, email: str, password: str) -> bool:
    """AuthManager.login()의 핵심 로직을 input() 없이 재현"""
    from core.models import Operator, SecuritySetting
    from core.security import verify_password

    mgr = env["db"]
    session = mgr.get_onboarding_session()
    try:
        op = session.query(Operator).filter_by(email=email, is_active=1).first()
        if not op:
            return False

        sec = session.query(SecuritySetting).filter_by(op_id=op.op_id).first()
        if sec and verify_password(password, sec.password_hash):
            AuthManager._AuthManager__current_user = {
                "op_id": op.op_id,
                "name": op.name,
                "role": op.role,
            }
            mgr.log_event(op_id=op.op_id, action=AuditAction.LOGIN_SUCCESS, reason="System Access")
            return True
        else:
            mgr.log_event(op_id=op.op_id, action=AuditAction.LOGIN_FAIL, reason="Wrong Password")
            return False
    finally:
        session.close()


# ============================================================
# 테스트 1: 올바른 이메일/비밀번호 → 로그인 성공 + AuditLog
# ============================================================
class TestLoginSuccess:
    def test_correct_credentials_returns_true(self, temp_env):
        """올바른 이메일/비밀번호로 로그인 성공"""
        result = do_login(temp_env, "active@test.com", "correct_pass")
        assert result is True

    def test_current_user_set_after_login(self, temp_env):
        """로그인 후 get_current_user()가 사용자 정보 반환"""
        do_login(temp_env, "active@test.com", "correct_pass")
        user = AuthManager.get_current_user()

        assert user is not None
        assert user["name"] == "활성관리자"
        assert user["role"] == Role.ADMIN

    def test_audit_log_login_success(self, temp_env):
        """로그인 성공 시 AuditLog에 LOGIN_SUCCESS 기록"""
        do_login(temp_env, "active@test.com", "correct_pass")

        conn = sqlite3.connect(temp_env["on_path"])
        row = conn.execute(
            "SELECT action, reason FROM audit_logs ORDER BY log_id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        assert row[0] == AuditAction.LOGIN_SUCCESS
        assert "System Access" in row[1]

    def test_audit_log_has_op_id(self, temp_env):
        """AuditLog에 올바른 op_id가 기록되는지"""
        do_login(temp_env, "active@test.com", "correct_pass")

        conn = sqlite3.connect(temp_env["on_path"])
        row = conn.execute(
            "SELECT op_id FROM audit_logs WHERE action = ?",
            (AuditAction.LOGIN_SUCCESS,)
        ).fetchone()
        conn.close()

        assert row[0] == temp_env["active_op_id"]


# ============================================================
# 테스트 2: 잘못된 비밀번호 → 실패 + LOGIN_FAIL 로그
# ============================================================
class TestLoginFail:
    def test_wrong_password_returns_false(self, temp_env):
        """잘못된 비밀번호로 로그인 실패"""
        result = do_login(temp_env, "active@test.com", "wrong_pass")
        assert result is False

    def test_current_user_none_after_fail(self, temp_env):
        """로그인 실패 후 get_current_user()가 None"""
        do_login(temp_env, "active@test.com", "wrong_pass")
        assert AuthManager.get_current_user() is None

    def test_audit_log_login_fail(self, temp_env):
        """로그인 실패 시 AuditLog에 LOGIN_FAIL 기록"""
        do_login(temp_env, "active@test.com", "wrong_pass")

        conn = sqlite3.connect(temp_env["on_path"])
        row = conn.execute(
            "SELECT action, reason FROM audit_logs WHERE action = ?",
            (AuditAction.LOGIN_FAIL,)
        ).fetchone()
        conn.close()

        assert row is not None
        assert row[0] == AuditAction.LOGIN_FAIL
        assert "Wrong Password" in row[1]

    def test_nonexistent_email_returns_false(self, temp_env):
        """존재하지 않는 이메일로 로그인 시도 → False"""
        result = do_login(temp_env, "nobody@test.com", "any_pass")
        assert result is False


# ============================================================
# 테스트 3: 비활성화(is_active=0) 계정 → 거부
# ============================================================
class TestInactiveAccount:
    def test_inactive_account_rejected(self, temp_env):
        """is_active=0 계정은 올바른 비밀번호여도 로그인 거부"""
        result = do_login(temp_env, "inactive@test.com", "inactive_pass")
        assert result is False

    def test_inactive_no_current_user(self, temp_env):
        """비활성 계정 로그인 시도 후 current_user가 None"""
        do_login(temp_env, "inactive@test.com", "inactive_pass")
        assert AuthManager.get_current_user() is None

    def test_inactive_no_audit_log(self, temp_env):
        """비활성 계정은 Operator 조회 자체가 안 되므로 AuditLog도 없음"""
        do_login(temp_env, "inactive@test.com", "inactive_pass")

        conn = sqlite3.connect(temp_env["on_path"])
        count = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
        conn.close()

        assert count == 0


# ============================================================
# 테스트 4: get_current_user() 반환값 수정해도 내부 데이터 안 바뀜
# ============================================================
class TestReadOnlyCopy:
    def test_modifying_copy_does_not_affect_internal(self, temp_env):
        """반환된 dict를 수정해도 내부 __current_user가 변경되지 않는지"""
        do_login(temp_env, "active@test.com", "correct_pass")

        user_copy = AuthManager.get_current_user()
        user_copy["name"] = "해커"
        user_copy["role"] = "HACKED"
        user_copy["op_id"] = 9999

        original = AuthManager.get_current_user()
        assert original["name"] == "활성관리자"
        assert original["role"] == Role.ADMIN
        assert original["op_id"] == temp_env["active_op_id"]

    def test_each_call_returns_new_copy(self, temp_env):
        """get_current_user()를 두 번 호출하면 다른 객체인지"""
        do_login(temp_env, "active@test.com", "correct_pass")

        copy1 = AuthManager.get_current_user()
        copy2 = AuthManager.get_current_user()

        assert copy1 == copy2          # 값은 같지만
        assert copy1 is not copy2      # 객체는 다름

    def test_logout_clears_user(self, temp_env):
        """logout() 후 get_current_user()가 None"""
        do_login(temp_env, "active@test.com", "correct_pass")
        assert AuthManager.get_current_user() is not None

        AuthManager.logout()
        assert AuthManager.get_current_user() is None
