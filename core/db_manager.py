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

import os
import re
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session


OnboardingBase = declarative_base()  # 기준 정보용
RuntimeBase = declarative_base()     # 실행 정보용



def _check_path_compatibility(*paths: str) -> None:
    """Windows 드라이브 경로(예: H:/foo)를 비-Windows 환경에서 사용하면 에러.

    config.yaml에 H:/nhis-macro-data/... 처럼 Windows 절대 경로가 박혀있는데
    WSL/git-bash/Linux 컨테이너에서 그대로 실행하면 'H:'가 *리터럴 폴더*로
    해석되어 cwd 아래에 H:/nhis-macro-data/... 가 잘못 생성됩니다.
    개발자(또는 자동화 도구)가 같은 사고를 다시 일으키지 않도록 차단.
    """
    if os.name == "nt":
        return
    DRIVE_RE = re.compile(r"^[A-Za-z]:[/\\]")
    for path in paths:
        if path and DRIVE_RE.match(path):
            raise RuntimeError(
                f"비-Windows 환경({os.name})에서 Windows 드라이브 경로 감지: {path}\n"
                f"이대로 진행하면 cwd 아래에 '{path[:2]}' 같은 리터럴 폴더가 생성됩니다.\n"
                f"해결: (1) Windows 네이티브에서 실행하거나 "
                f"(2) config의 db.* 경로를 OS-중립(또는 환경변수 기반)으로 수정하세요."
            )


class DBManager:
    """Onboarding / Runtime 두 개의 SQLite DB를 관리하는 싱글턴 매니저"""

    def __init__(self) -> None:
        self._onboarding_engine: Optional[Engine] = None
        self._runtime_engine: Optional[Engine] = None
        self._OnboardingSession: Optional[sessionmaker] = None
        self._RuntimeSession: Optional[sessionmaker] = None

    def initialize(self, onboarding_path: str, runtime_path: str, echo: bool = False) -> None:
        """외부에서 주입받은 두 개의 경로로 각각의 DB를 초기화합니다."""
        _check_path_compatibility(onboarding_path, runtime_path)

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

        # 4. 감사 리스너 자동 등록 (민감 테이블 INSERT/UPDATE/DELETE → AuditLog)
        #    audit_listener.py 참고. op_id 주입: session._current_op_id = op_id
        from core.audit_listener import register_audit_listeners
        register_audit_listeners(self)

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
        reason: str = "",
        session: Optional[Session] = None
    ) -> None:
        """감사 로그를 기록합니다.

        Args:
            session: 기존 세션을 넘기면 그 세션에 add만 합니다 (커밋은 호출자 책임).
                     None이면 독립 세션을 열어 즉시 커밋합니다.
        """
        from core.models import AuditLog

        audit = AuditLog(
            op_id=op_id,
            action=action,
            target_id=target_id,
            reason=reason,
        )

        if session is not None:
            # 기존 세션에 얹기만 — 커밋은 호출자가 함
            session.add(audit)
            return

        # 독립 세션 — 즉시 커밋
        own_session = self.get_onboarding_session()
        try:
            own_session.add(audit)
            own_session.commit()
        except Exception as e:
            own_session.rollback()
            print(f"⚠️ 로그 기록 실패: {e}")
        finally:
            own_session.close()

    @property
    def onboarding_engine(self) -> Optional[Engine]:
        return self._onboarding_engine

    @property
    def runtime_engine(self) -> Optional[Engine]:
        return self._runtime_engine


db = DBManager()