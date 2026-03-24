"""
tests/test_db_manager.py — DBManager 듀얼 DB 매니저 검증
=========================================================
Step B QA: 초기화, 세션 생성, log_event, engine property 동작 확인

실행: cd nhis-macro-core && python -m pytest tests/test_db_manager.py -v
"""

import os
import tempfile
import pytest

import core.models  # noqa: F401 — Base에 테이블 등록
from core.db_manager import DBManager, OnboardingBase, RuntimeBase


# ============================================================
# Fixture: 매 테스트마다 깨끗한 DBManager + 임시 DB 파일
# ============================================================

@pytest.fixture
def tmp_db_paths():
    """임시 DB 파일 2개 생성 → 테스트 후 삭제"""
    ob_fd, ob_path = tempfile.mkstemp(suffix="_onboarding.db")
    rt_fd, rt_path = tempfile.mkstemp(suffix="_runtime.db")
    os.close(ob_fd)
    os.close(rt_fd)
    yield ob_path, rt_path
    os.unlink(ob_path)
    os.unlink(rt_path)


@pytest.fixture
def manager(tmp_db_paths):
    """초기화된 DBManager 인스턴스 — teardown 시 엔진 정리"""
    ob_path, rt_path = tmp_db_paths
    mgr = DBManager()
    mgr.initialize(ob_path, rt_path)
    yield mgr
    # Windows에서 SQLite 파일 잠금 해제를 위해 엔진 dispose
    if mgr.onboarding_engine:
        mgr.onboarding_engine.dispose()
    if mgr.runtime_engine:
        mgr.runtime_engine.dispose()


@pytest.fixture
def uninitialized_manager():
    """초기화 안 된 DBManager 인스턴스"""
    return DBManager()


# ============================================================
# 1. 초기화 전 호출 시 에러 확인
# ============================================================

class TestBeforeInitialize:
    """initialize() 호출 전에 세션을 요청하면 RuntimeError가 나야 함"""

    def test_get_onboarding_session_raises(self, uninitialized_manager):
        with pytest.raises(RuntimeError, match="초기화되지 않았습니다"):
            uninitialized_manager.get_onboarding_session()

    def test_get_runtime_session_raises(self, uninitialized_manager):
        with pytest.raises(RuntimeError, match="초기화되지 않았습니다"):
            uninitialized_manager.get_runtime_session()

    def test_engine_is_none_before_init(self, uninitialized_manager):
        assert uninitialized_manager.onboarding_engine is None
        assert uninitialized_manager.runtime_engine is None


# ============================================================
# 2. 초기화 후 정상 동작 확인
# ============================================================

class TestAfterInitialize:
    """initialize() 후 세션, 엔진, 테이블 생성이 정상인지 확인"""

    def test_engines_are_created(self, manager):
        assert manager.onboarding_engine is not None
        assert manager.runtime_engine is not None

    def test_engines_are_different(self, manager):
        """두 엔진이 서로 다른 DB를 가리키는지"""
        assert manager.onboarding_engine != manager.runtime_engine

    def test_onboarding_session_works(self, manager):
        session = manager.get_onboarding_session()
        assert session is not None
        session.close()

    def test_runtime_session_works(self, manager):
        session = manager.get_runtime_session()
        assert session is not None
        session.close()

    def test_multiple_sessions_are_independent(self, manager):
        """세션 2개를 열어도 서로 간섭하지 않아야 함"""
        s1 = manager.get_onboarding_session()
        s2 = manager.get_onboarding_session()
        assert s1 is not s2
        s1.close()
        s2.close()


# ============================================================
# 3. engine property 접근 확인
# ============================================================

class TestEngineProperty:
    """private _engine을 property로 안전하게 노출하는지 확인"""

    def test_onboarding_engine_property(self, manager):
        engine = manager.onboarding_engine
        assert engine is not None
        assert str(engine.url).startswith("sqlite:///")

    def test_runtime_engine_property(self, manager):
        engine = manager.runtime_engine
        assert engine is not None
        assert str(engine.url).startswith("sqlite:///")

    def test_engine_is_readonly(self, manager):
        """property이므로 직접 대입하면 AttributeError"""
        with pytest.raises(AttributeError):
            manager.onboarding_engine = "something"
        with pytest.raises(AttributeError):
            manager.runtime_engine = "something"


# ============================================================
# 4. log_event 감사 로그 기록 확인
# ============================================================

class TestLogEvent:
    """log_event()가 AuditLog 테이블에 정상 기록되는지 확인"""

    def test_log_event_creates_record(self, manager):
        from core.models import AuditLog

        manager.log_event(op_id=1, action="TEST_ACTION", reason="unit test")

        session = manager.get_onboarding_session()
        try:
            logs = session.query(AuditLog).all()
            assert len(logs) == 1
            assert logs[0].action == "TEST_ACTION"
            assert logs[0].op_id == 1
            assert logs[0].reason == "unit test"
        finally:
            session.close()

    def test_log_event_with_target_id(self, manager):
        from core.models import AuditLog

        manager.log_event(op_id=2, action="PATIENT_CREATE", target_id=99, reason="Excel")

        session = manager.get_onboarding_session()
        try:
            log = session.query(AuditLog).first()
            assert log.target_id == 99
        finally:
            session.close()

    def test_log_event_multiple(self, manager):
        """여러 번 호출해도 각각 독립적으로 기록되어야 함"""
        from core.models import AuditLog

        manager.log_event(op_id=1, action="A1", reason="r1")
        manager.log_event(op_id=1, action="A2", reason="r2")
        manager.log_event(op_id=1, action="A3", reason="r3")

        session = manager.get_onboarding_session()
        try:
            count = session.query(AuditLog).count()
            assert count == 3
        finally:
            session.close()

    def test_log_event_does_not_crash_on_error(self, manager, capsys):
        """log_event 내부 에러 시 프로그램이 죽지 않고 경고만 출력"""
        # op_id에 문자열을 넣으면 FK 타입 불일치이지만,
        # SQLite는 느슨해서 안 터질 수 있음. 대신 None action 테스트
        manager.log_event(op_id=1, action=None, reason="test")
        # 죽지 않으면 성공
