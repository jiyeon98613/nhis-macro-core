# nhis-macro-core/core/db_manager.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class DBManager:
    def __init__(self):
        # 엔진과 세션을 두 세트로 관리합니다.
        self.onboarding_engine = None
        self.runtime_engine = None
        self.OnboardingSession = None
        self.RuntimeSession = None

    def initialize(self, onboarding_path: str, runtime_path: str, echo: bool = False):
        """외부에서 주입받은 두 개의 경로로 각각의 DB를 초기화합니다."""
        
        # 1. Onboarding DB 초기화
        onboarding_url = f"sqlite:///{onboarding_path}"
        self.onboarding_engine = create_engine(
            onboarding_url, echo=echo, connect_args={"check_same_thread": False}
        )
        self.OnboardingSession = sessionmaker(autocommit=False, autoflush=False, bind=self.onboarding_engine)

        # 2. Runtime DB 초기화
        runtime_url = f"sqlite:///{runtime_path}"
        self.runtime_engine = create_engine(
            runtime_url, echo=echo, connect_args={"check_same_thread": False}
        )
        self.RuntimeSession = sessionmaker(autocommit=False, autoflush=False, bind=self.runtime_engine)

        # 3. 테이블 생성 (만약 파일은 있는데 테이블이 없다면 생성)
        # Base.metadata에 등록된 모든 테이블을 각 엔진에 맞게 생성합니다.
        Base.metadata.create_all(self.onboarding_engine)
        Base.metadata.create_all(self.runtime_engine)

    def get_onboarding_session(self):
        if not self.OnboardingSession:
            raise ValueError("🗄️ Onboarding DB가 초기화되지 않았습니다.")
        return self.OnboardingSession()

    def get_runtime_session(self):
        if not self.RuntimeSession:
            raise ValueError("🗄️ Runtime DB가 초기화되지 않았습니다.")
        return self.RuntimeSession()

    def log_event(self, session, operator, action, table, details=""):
        """감사 로그 생성 (AuditLog는 주로 onboarding.db에 쌓습니다)"""
        from core.models import AuditLog
        new_log = AuditLog(
            operator_name=operator,
            action=action,
            target_table=table,
            details=details
        )
        session.add(new_log)

db = DBManager()