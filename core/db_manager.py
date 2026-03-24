# nhis-macro-core/core/db_manager.py
"""
core/db_manager.py — 듀얼 DB 세션 매니저
==========================================
onboarding.db와 runtime.db 두 개의 SQLite를 관리.
모듈 하단의 `db = DBManager()` 싱글턴을 통해 접근.

사용법:
    from core.db_manager import db
    db.initialize(onboarding_path, runtime_path)
    session = db.get_onboarding_session()
"""

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime

OnboardingBase = declarative_base()  # 기준 정보용
RuntimeBase = declarative_base()     # 실행 정보용


class DBManager:
    """Onboarding / Runtime 두 개의 SQLite DB를 관리하는 싱글턴 매니저"""

    def __init__(self) -> None:
        self._onboarding_engine: Optional[Engine] = None
        self._runtime_engine: Optional[Engine] = None
        self._OnboardingSession: Optional[sessionmaker] = None
        self._RuntimeSession: Optional[sessionmaker] = None

    def initialize(self, onboarding_path: str, runtime_path: str, echo: bool = False) -> None:
        """외부에서 주입받은 두 개의 경로로 각각의 DB를 초기화합니다."""

        # 1. Onboarding DB
        self._onboarding_engine = create_engine(
            f"sqlite:///{onboarding_path}", echo=echo,
            connect_args={"check_same_thread": False}
        )
        self._OnboardingSession = sessionmaker(bind=self._onboarding_engine)

        # 2. Runtime DB
        self._runtime_engine = create_engine(
            f"sqlite:///{runtime_path}", echo=echo,
            connect_args={"check_same_thread": False}
        )
        self._RuntimeSession = sessionmaker(bind=self._runtime_engine)

        # 3. 각 Base가 자기 테이블만 생성
        OnboardingBase.metadata.create_all(self._onboarding_engine)
        RuntimeBase.metadata.create_all(self._runtime_engine)

    def get_onboarding_session(self) -> Session:
        """Onboarding DB 세션을 생성하여 반환합니다. 사용 후 반드시 close() 하세요."""

        if not self._OnboardingSession:
            raise RuntimeError("Onboarding DB가 초기화되지 않았습니다. db.initialize()를 먼저 호출하세요.")
        return self._OnboardingSession()

    def get_runtime_session(self) -> Session:
        """Runtime DB 세션을 생성하여 반환합니다. 사용 후 반드시 close() 하세요."""

        if not self._RuntimeSession:
            raise RuntimeError("Runtime DB가 초기화되지 않았습니다. db.initialize()를 먼저 호출하세요.")
        return self._RuntimeSession()

    def log_event(
        self,
        op_id: int,
        action: str,
        target_id: Optional[int] = None,
        reason: str = ""
    ) -> None:
        """감사 로그를 즉시 기록합니다 (세션 열고 → 커밋 → 닫기)."""
        from core.models import AuditLog

        session = self.get_onboarding_session()
        try:
            session.add(AuditLog(
                op_id=op_id,
                action=action,
                target_id=target_id,
                reason=reason,
            ))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"⚠️ 로그 기록 실패: {e}")
        finally:
            session.close()

    @property
    def onboarding_engine(self) -> Optional[Engine]:
        return self._onboarding_engine

    @property
    def runtime_engine(self) -> Optional[Engine]:
        return self._runtime_engine


db = DBManager()