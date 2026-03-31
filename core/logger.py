# core/logger.py
"""
core/logger.py — 프로덕션 로깅 시스템
=======================================
Python logging 모듈 기반으로 콘솔·파일·DB에 동시 기록.

- 콘솔: INFO 이상 출력
- 파일: DEBUG 포함 전체 (nhis.log, 5MB 로테이션)
- DB: WARNING 이상만 SystemLog 테이블에 버퍼링 저장

사용법:
    # main.py에서 초기화
    from core.logger import setup_logger
    setup_logger(log_dir="path/to/logs")

    # 각 Step에서 사용
    from core.logger import get_step_logger
    logger = get_step_logger("AuthStep")
    logger.info("인증 시작")
"""
import atexit
import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler


class DBHandler(logging.Handler):
    """WARNING 이상의 로그를 runtime.db SystemLog 테이블에 버퍼링하여 일괄 저장하는 핸들러"""
    
    def __init__(self, buffer_size: int = 20):
        """버퍼 크기를 지정하여 핸들러를 초기화합니다.

        Args:
            buffer_size: 이 개수만큼 쌓이면 자동으로 DB에 flush합니다.
        """
        super().__init__()
        self._buffer: list[logging.LogRecord] = []
        self._buffer_size = buffer_size

    def emit(self, record: logging.LogRecord) -> None:
        """로그 레코드를 버퍼에 추가하고, 버퍼가 가득 차면 flush합니다."""
        self._buffer.append(record)
        if len(self._buffer) >= self._buffer_size:
            self.flush()

    def flush(self) -> None:
        """버퍼에 쌓인 로그를 한 번의 DB 세션으로 일괄 저장합니다."""
        if not self._buffer:
            return
        
        from core.db_manager import db
        from core.models import SystemLog
        
        session = db.get_runtime_session()
        try:
            for record in self._buffer:
                session.add(SystemLog(
                    level=record.levelname,
                    step_name=getattr(record, 'step_name', record.name),
                    message=self.format(record)
                ))
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
            self._buffer.clear()


def setup_logger(log_dir: str = None) -> logging.Logger:
    """프로그램 전체에서 사용할 'nhis' 로거를 초기화합니다.

    콘솔·파일·DB 세 가지 핸들러를 등록하며, 중복 호출 시 기존 로거를 반환합니다.

    Args:
        log_dir: 로그 파일 저장 경로. None이면 파일 핸들러를 등록하지 않습니다.

    Returns:
        설정 완료된 logging.Logger 인스턴스
    """
    logger = logging.getLogger("nhis")
    
    if logger.handlers:  # 이미 설정됐으면 중복 방지
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # 포맷: 시간 [레벨] 스텝이름 - 메시지
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] %(step_name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1) 콘솔 핸들러 (INFO 이상만)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # 2) 파일 핸들러 (DEBUG 포함 전부 — 5MB마다 새 파일, 최대 5개)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path / "nhis.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 3) DB 핸들러 (WARNING 이상만 DB에 — 중요한 것만)
    db_handler = DBHandler(buffer_size=10)
    db_handler.setLevel(logging.WARNING)
    db_handler.setFormatter(formatter)
    logger.addHandler(db_handler)

    # 프로그램 종료 시 버퍼에 남은 로그 flush
    atexit.register(_flush_all_handlers, logger)

    return logger


def _flush_all_handlers(logger: logging.Logger) -> None:
    """등록된 모든 핸들러를 flush합니다 (atexit용)."""
    for handler in logger.handlers:
        try:
            handler.flush()
        except Exception:
            pass


def get_step_logger(step_name: str) -> logging.LoggerAdapter:
    """각 Step에서 사용할 LoggerAdapter를 반환합니다.

    step_name이 로그 포맷의 %(step_name)s 위치에 자동 삽입됩니다.

    Args:
        step_name: 스텝 클래스명 (예: 'AuthStep', 'FileScanStep')

    Returns:
        step_name이 바인딩된 LoggerAdapter
    """
    logger = logging.getLogger("nhis")
    return logging.LoggerAdapter(logger, {"step_name": step_name})
