# core/audit_listener.py
"""
SQLAlchemy 이벤트 리스너 — 민감 테이블 자동 감사 기록
=======================================================
민감 테이블(patients, claims, prescriptions)에 INSERT/UPDATE/DELETE
발생 시 AuditLog에 자동으로 기록합니다.

사용법:
    from core.audit_listener import register_audit_listeners
    from core.db_manager import db

    db.initialize(onboarding_path, runtime_path)
    register_audit_listeners(db)   ← initialize() 직후 한 번 호출

주의:
    - AuditLog는 onboarding.db에 있고, 이벤트는 runtime.db 세션에서 발생합니다.
      cross-DB 기록이므로 audit_session은 별도 onboarding 세션을 사용합니다.
    - _current_op_id는 세션에 수동으로 주입해야 합니다.
      예) session._current_op_id = op_id  (WorkflowRunner 등에서)
"""

from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.orm import Session

# 감사 대상 모델 (런타임에 임포트하여 순환 참조 방지)
_SENSITIVE_TABLE_NAMES = {"patients", "claims", "prescriptions"}


def register_audit_listeners(db_manager) -> None:
    """db_manager의 RuntimeSession에 after_flush 리스너를 등록합니다.
    db.initialize() 직후 한 번만 호출하면 됩니다.

    Args:
        db_manager: core.db_manager.DBManager 인스턴스 (db 싱글턴)
    """
    if db_manager._RuntimeSession is None:
        raise RuntimeError("RuntimeSession이 초기화되지 않았습니다. db.initialize()를 먼저 호출하세요.")

    @event.listens_for(db_manager._RuntimeSession, "after_flush")
    def _auto_audit(session: Session, flush_context) -> None:
        """민감 테이블 변경 시 AuditLog 자동 기록"""
        from core.models import AuditLog

        op_id = getattr(session, "_current_op_id", None)
        audit_entries = []

        def _record(obj, action: str) -> None:
            try:
                table = getattr(obj.__class__, "__tablename__", "")
                if table not in _SENSITIVE_TABLE_NAMES:
                    return
                # __dict__로 PK 값 직접 추출 (SQLAlchemy 표현식 평가 완전 회피)
                try:
                    pk_name = obj.__mapper__.primary_key[0].name
                    target_id = obj.__dict__.get(pk_name)
                except Exception:
                    target_id = None
                audit_entries.append(AuditLog(
                    op_id=op_id,
                    action=f"AUTO_{action}_{table.upper()}",
                    target_id=target_id,
                    reason="auto_audit_listener",
                ))
            except Exception:
                pass  # audit 실패는 주 작업을 막지 않음

        for obj in session.new:
            _record(obj, "INSERT")
        for obj in session.dirty:
            _record(obj, "UPDATE")
        for obj in session.deleted:
            _record(obj, "DELETE")

        if not audit_entries:
            return

        # AuditLog는 onboarding.db에 저장 — 별도 세션 사용
        audit_session = db_manager.get_onboarding_session()
        try:
            for entry in audit_entries:
                audit_session.add(entry)
            audit_session.commit()
        except Exception as e:
            audit_session.rollback()
            # 감사 로그 실패는 주 작업을 막지 않음 (경고만)
            import logging
            logging.getLogger(__name__).warning(f"[audit_listener] AuditLog 기록 실패: {e}")
        finally:
            audit_session.close()
