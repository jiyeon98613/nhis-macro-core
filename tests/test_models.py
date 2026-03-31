"""
tests/test_models.py — models.py의 ORM 모델 정의 검증
======================================================
Step A QA: datetime 버그 수정 확인 + 테이블 생성 정상 동작 확인

실행: cd nhis-macro-core && python -m pytest tests/test_models.py -v
"""

import time
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# models를 먼저 import해야 Base.metadata에 테이블이 등록됨
import core.models  # noqa: F401 — 사이드이펙트용 import
from core.db_manager import OnboardingBase, RuntimeBase


# ============================================================
# Fixtures: 테스트용 임시 DB (메모리 DB — 파일 안 만듦)
# ============================================================

@pytest.fixture
def onboarding_session():
    """테스트용 Onboarding 인메모리 DB 세션"""
    engine = create_engine("sqlite:///:memory:")
    OnboardingBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session, engine
    session.close()


@pytest.fixture
def runtime_session():
    """테스트용 Runtime 인메모리 DB 세션"""
    engine = create_engine("sqlite:///:memory:")
    RuntimeBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session, engine
    session.close()


# ============================================================
# 1. 테이블이 올바른 DB에만 생성되는지 확인
# ============================================================

class TestTableSeparation:
    """OnboardingBase 테이블은 onboarding DB에만,
    RuntimeBase 테이블은 runtime DB에만 생성되어야 함"""

    ONBOARDING_TABLES = {
        "business_certificates",
        "frequent_hospitals", "manufacturers", "vendors",
        "devices", "operators", "audit_logs", "security_settings",
        "approvals", "document_templates", "document_fields",
    }

    RUNTIME_TABLES = {
        "system_logs", "patients", "patient_documents",
        "prescriptions", "sleep_reports", "contracts",
        "return_receipts", "tax_invoices", "receipts",
        "consumables", "travels", "monthly_updates",
        "claims", "patient_alerts", "extracted_data", "workflow_sessions",
        "patient_business_certificates",
    }

    def test_onboarding_db_has_only_onboarding_tables(self, onboarding_session):
        _, engine = onboarding_session
        tables = set(inspect(engine).get_table_names())
        assert tables == self.ONBOARDING_TABLES, (
            f"예상과 다름. 실제: {tables}"
        )

    def test_runtime_db_has_only_runtime_tables(self, runtime_session):
        _, engine = runtime_session
        tables = set(inspect(engine).get_table_names())
        assert tables == self.RUNTIME_TABLES, (
            f"예상과 다름. 실제: {tables}"
        )

    def test_no_cross_contamination(self, onboarding_session, runtime_session):
        _, ob_engine = onboarding_session
        _, rt_engine = runtime_session
        ob_tables = set(inspect(ob_engine).get_table_names())
        rt_tables = set(inspect(rt_engine).get_table_names())
        overlap = ob_tables & rt_tables
        assert not overlap, f"양쪽 DB에 중복 테이블 존재: {overlap}"


# ============================================================
# 2. datetime 버그 수정 확인 — server_default=func.now()
# ============================================================

class TestDatetimeDefaults:
    """default=datetime.now 버그가 server_default=func.now()로
    수정되었는지 검증합니다."""

    def test_audit_log_timestamp_is_auto(self, onboarding_session):
        """AuditLog INSERT 시 access_time이 자동 생성되어야 함"""
        from core.models import AuditLog
        session, _ = onboarding_session

        log1 = AuditLog(op_id=1, action="TEST_1", reason="first")
        session.add(log1)
        session.commit()

        time.sleep(1.1)

        log2 = AuditLog(op_id=1, action="TEST_2", reason="second")
        session.add(log2)
        session.commit()

        session.refresh(log1)
        session.refresh(log2)

        assert log1.access_time is not None, "access_time이 None — server_default 미적용"
        assert log2.access_time is not None, "access_time이 None — server_default 미적용"
        assert log1.access_time != log2.access_time, (
            f"두 레코드의 시간이 동일 — 고정값 버그 존재: {log1.access_time}"
        )

    def test_approval_timestamp_is_auto(self, onboarding_session):
        """Approval의 approved_at이 자동 생성되는지 확인"""
        from core.models import Approval
        session, _ = onboarding_session

        appr = Approval(scope="TEST", target_id="1", approved_by=1)
        session.add(appr)
        session.commit()
        session.refresh(appr)

        assert appr.approved_at is not None, "approved_at이 None — server_default 미적용"

    def test_security_setting_timestamp_is_auto(self, onboarding_session):
        """SecuritySetting의 password_set_at이 자동 생성되는지 확인"""
        from core.models import Operator, SecuritySetting
        session, _ = onboarding_session

        op = Operator(name="테스트", email="test@test.com", role="ADMIN")
        session.add(op)
        session.flush()

        sec = SecuritySetting(op_id=op.op_id, password_hash="fakehash")
        session.add(sec)
        session.commit()
        session.refresh(sec)

        assert sec.password_set_at is not None, "password_set_at이 None — server_default 미적용"

    def test_system_log_timestamp_is_auto(self, runtime_session):
        """SystemLog의 created_at이 자동 생성되는지 확인"""
        from core.models import SystemLog
        session, _ = runtime_session

        log = SystemLog(level="INFO", step_name="TestStep", message="test")
        session.add(log)
        session.commit()
        session.refresh(log)

        assert log.created_at is not None, "created_at이 None — server_default 미적용"


# ============================================================
# 3. 필수 컬럼 NOT NULL 제약 확인
# ============================================================

class TestRequiredColumns:
    """nullable=False 컬럼에 None을 넣으면 에러가 나야 함"""

    def test_hospital_requires_hosp_code(self, onboarding_session):
        from core.models import FrequentHospital
        session, _ = onboarding_session

        hosp = FrequentHospital(hosp_name="테스트병원")  # hosp_code 누락
        session.add(hosp)
        with pytest.raises(Exception):
            session.commit()

    def test_hospital_requires_hosp_name(self, onboarding_session):
        from core.models import FrequentHospital
        session, _ = onboarding_session

        hosp = FrequentHospital(hosp_code="TEST001")  # hosp_name 누락
        session.add(hosp)
        with pytest.raises(Exception):
            session.commit()

    def test_patient_requires_chart_num(self, runtime_session):
        from core.models import Patient
        session, _ = runtime_session

        pat = Patient(pat_name="홍길동")  # chart_num 누락
        session.add(pat)
        with pytest.raises(Exception):
            session.commit()
