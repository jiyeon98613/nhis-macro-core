# nhis-macro-core/core/db_manager.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

OnboardingBase = declarative_base()  # 기준 정보용
RuntimeBase = declarative_base()     # 실행 정보용

class DBManager:
    def __init__(self):
        # 엔진과 세션을 두 세트로 관리합니다.
        self.onboarding_engine = None
        self.runtime_engine = None
        self.OnboardingSession = None
        self.RuntimeSession = None

    def initialize(self, onboarding_path: str, runtime_path: str, echo: bool = False):
        """외부에서 주입받은 두 개의 경로로 각각의 DB를 초기화합니다."""
        
        # 1. Onboarding DB
        self.onboarding_engine = create_engine(
            f"sqlite:///{onboarding_path}", echo=echo,
            connect_args={"check_same_thread": False}
        )
        self.OnboardingSession = sessionmaker(bind=self.onboarding_engine)

        # 2. Runtime DB
        self.runtime_engine = create_engine(
            f"sqlite:///{runtime_path}", echo=echo,
            connect_args={"check_same_thread": False}
        )
        self.RuntimeSession = sessionmaker(bind=self.runtime_engine)

        # 3. 각 Base가 자기 테이블만 생성
        OnboardingBase.metadata.create_all(self.onboarding_engine)  # hospitals, doctors, operators만
        RuntimeBase.metadata.create_all(self.runtime_engine)        # patients, prescriptions만

    def get_onboarding_session(self):
        if not self.OnboardingSession:
            raise ValueError("🗄️ Onboarding DB가 초기화되지 않았습니다.")
        return self.OnboardingSession()

    def get_runtime_session(self):
        if not self.RuntimeSession:
            raise ValueError("🗄️ Runtime DB가 초기화되지 않았습니다.")
        return self.RuntimeSession()

    def log_event(self, op_id: int, action: str, target_id: int = None, reason: str = ""):
        """별도의 세션을 열어 즉시 로그를 남기고 닫습니다."""
        from core.models import AuditLog
        from datetime import datetime

        session = self.get_onboarding_session()
        try:
            new_log = AuditLog(
                op_id=op_id, 
                action=action,
                target_id=target_id,
                reason=reason,
                access_time=datetime.now()
            )
            session.add(new_log)
            session.commit()  # 반드시 커밋해야 DB에 반영됨.
        except Exception as e:
            session.rollback()
            print(f"⚠️ 로그 기록 실패: {e}")
        finally:
            session.close()

db = DBManager()