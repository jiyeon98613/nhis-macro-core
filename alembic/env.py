# alembic/env.py
"""
Alembic 마이그레이션 환경 설정
==============================
Onboarding DB와 Runtime DB 두 개의 SQLite를 관리합니다.
--db onboarding / --db runtime 으로 대상 DB를 선택합니다.

사용법:
  alembic -x db=onboarding upgrade head
  alembic -x db=runtime upgrade head
  alembic -x db=onboarding revision --autogenerate -m "add phone_num"
"""

import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# nhis-macro-core를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.db_manager import OnboardingBase, RuntimeBase

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --db 파라미터로 대상 DB 선택
db_name = context.get_x_argument(as_dictionary=True).get("db", "onboarding")

# 모델 임포트 (metadata 등록을 위해)
import core.models  # noqa: F401

if db_name == "runtime":
    target_metadata = RuntimeBase.metadata
else:
    target_metadata = OnboardingBase.metadata


def get_url() -> str:
    """대상 DB의 SQLite URL을 반환합니다."""
    # 환경 변수 또는 기본 경로
    import os
    if db_name == "runtime":
        path = os.environ.get(
            "RUNTIME_DB_PATH",
            str(Path(__file__).resolve().parents[2]
                / "nhis-macro-config" / "storage" / "program_data" / "runtime.db")
        )
    else:
        path = os.environ.get(
            "ONBOARDING_DB_PATH",
            str(Path(__file__).resolve().parents[2]
                / "nhis-macro-config" / "storage" / "program_data" / "onboarding.db")
        )
    return f"sqlite:///{path}"


def run_migrations_offline() -> None:
    """offline 모드 마이그레이션 (SQL만 출력)"""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite ALTER TABLE 지원
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """online 모드 마이그레이션 (실제 DB 적용)"""
    # alembic.ini의 sqlalchemy.url을 동적으로 오버라이드
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite ALTER TABLE 지원
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
