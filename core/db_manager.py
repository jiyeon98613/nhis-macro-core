# nhis-macro-core/core/db_manager.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class DBManager:
    """
    DB 연결을 관리하는 클래스.
    Public 레포이므로 실제 DB 경로는 실행 시점에 주입받습니다.
    """
    def __init__(self):
        self.engine = None
        self.SessionLocal = None

    def initialize(self, db_path: str, echo: bool = False):
        """외부(Engine)에서 알려주는 실제 DB 경로로 접속합니다."""
        # SQLite 연결 (절대 경로 권장)
        db_url = f"sqlite:///{db_path}"
        self.engine = create_engine(
            db_url, 
            echo=echo, 
            connect_args={"check_same_thread": False}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self):
        if not self.SessionLocal:
            raise ValueError("🗄️ DB가 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        return self.SessionLocal()

    def log_event(self, session, operator, action, table, details=""):
        """감사 로그 생성"""
        from core.models import AuditLog  # 순환 참조 방지
        new_log = AuditLog(
            operator_name=operator,
            action=action,
            target_table=table,
            details=details
        )
        session.add(new_log)

# 엔진 등에서 공용으로 쓸 인스턴스 생성
db = DBManager()