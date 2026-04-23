"""db model v2 fixes — 2026-04-23

Revision ID: a2b3c4d5e6f7
Revises: c8e9f0a1b2c3
Create Date: 2026-04-23 00:00:00.000000

적용 방법 (두 DB에 각각 실행):
  alembic -x db=onboarding upgrade head
  alembic -x db=runtime upgrade head

변경 내용:
  [onboarding.db]
  - frequent_hospitals: bc_id, reg_doc_path 컬럼 제거
  - vendors: is_hospital_internal 컬럼 제거
  - operators: hosp_code 컬럼 제거, vendor_id (FK→vendors) 추가
  - security_settings: id → ss_id (PK 컬럼명 변경)
  - document_templates: (doc_type, identifier_keyword) UniqueConstraint 추가

  [runtime.db]
  - travels: ix_travel_pat_dates 복합 인덱스 추가, rt_id (FK→return_receipts) 추가
  - monthly_updates: travel_id 컬럼 제거
  - device_assignments: 신규 테이블 생성
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "c8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_onboarding(bind) -> bool:
    """연결된 DB가 onboarding.db인지 판별 (operators 테이블 존재 여부)"""
    inspector = sa.inspect(bind)
    return "operators" in inspector.get_table_names()


def _is_runtime(bind) -> bool:
    """연결된 DB가 runtime.db인지 판별 (patients 테이블 존재 여부)"""
    inspector = sa.inspect(bind)
    return "patients" in inspector.get_table_names()


def _get_columns(bind, table_name) -> list:
    inspector = sa.inspect(bind)
    return [col["name"] for col in inspector.get_columns(table_name)]


def _get_indexes(bind, table_name) -> list:
    inspector = sa.inspect(bind)
    return [idx["name"] for idx in inspector.get_indexes(table_name)]


def upgrade() -> None:
    bind = op.get_bind()

    # ================================================================
    # ONBOARDING DB 변경
    # ================================================================
    if _is_onboarding(bind):

        # ── frequent_hospitals: bc_id, reg_doc_path 제거 ──
        cols = _get_columns(bind, "frequent_hospitals")
        fh_drops = [c for c in ["bc_id", "reg_doc_path"] if c in cols]
        if fh_drops:
            with op.batch_alter_table("frequent_hospitals", schema=None) as batch_op:
                for col in fh_drops:
                    batch_op.drop_column(col)

        # ── vendors: is_hospital_internal 제거 ──
        cols = _get_columns(bind, "vendors")
        if "is_hospital_internal" in cols:
            with op.batch_alter_table("vendors", schema=None) as batch_op:
                batch_op.drop_column("is_hospital_internal")

        # ── operators: hosp_code 제거, vendor_id 추가 ──
        cols = _get_columns(bind, "operators")
        with op.batch_alter_table("operators", schema=None) as batch_op:
            if "hosp_code" in cols:
                batch_op.drop_column("hosp_code")
            if "vendor_id" not in cols:
                batch_op.add_column(
                    sa.Column("vendor_id", sa.Integer(),
                              sa.ForeignKey("vendors.vendor_id"), nullable=True)
                )

        # ── security_settings: id → ss_id ──
        cols = _get_columns(bind, "security_settings")
        if "id" in cols and "ss_id" not in cols:
            with op.batch_alter_table("security_settings", schema=None) as batch_op:
                batch_op.alter_column("id", new_column_name="ss_id")

        # ── document_templates: UniqueConstraint 추가 ──
        # SQLite batch mode로 테이블 재생성하며 제약 추가
        existing_indexes = _get_indexes(bind, "document_templates")
        if "uq_doctemp_type_keyword" not in existing_indexes:
            with op.batch_alter_table("document_templates", schema=None) as batch_op:
                batch_op.create_unique_constraint(
                    "uq_doctemp_type_keyword",
                    ["doc_type", "identifier_keyword"]
                )

    # ================================================================
    # RUNTIME DB 변경
    # ================================================================
    if _is_runtime(bind):

        # ── travels: 복합 인덱스 추가, rt_id 컬럼 추가 ──
        existing_indexes = _get_indexes(bind, "travels")
        cols = _get_columns(bind, "travels")
        with op.batch_alter_table("travels", schema=None) as batch_op:
            if "ix_travel_pat_dates" not in existing_indexes:
                batch_op.create_index(
                    "ix_travel_pat_dates",
                    ["pat_id", "depart_date", "entry_date"]
                )
            if "rt_id" not in cols:
                batch_op.add_column(
                    sa.Column("rt_id", sa.Integer(),
                              sa.ForeignKey("return_receipts.rt_id"), nullable=True)
                )

        # ── monthly_updates: travel_id 제거 ──
        cols = _get_columns(bind, "monthly_updates")
        if "travel_id" in cols:
            with op.batch_alter_table("monthly_updates", schema=None) as batch_op:
                batch_op.drop_column("travel_id")

        # ── device_assignments: 신규 테이블 생성 ──
        inspector = sa.inspect(bind)
        if "device_assignments" not in inspector.get_table_names():
            op.create_table(
                "device_assignments",
                sa.Column("da_id", sa.Integer(), primary_key=True, autoincrement=True),
                sa.Column("dev_id", sa.Integer(),
                          sa.ForeignKey("devices.dev_id"), nullable=False),
                sa.Column("pat_id", sa.Integer(),
                          sa.ForeignKey("patients.pat_id"), nullable=False),
                sa.Column("ct_id", sa.Integer(),
                          sa.ForeignKey("contracts.ct_id"), nullable=True),
                sa.Column("assigned_at", sa.Date(), nullable=False),
                sa.Column("returned_at", sa.Date(), nullable=True),
                sa.Column("created_at", sa.DateTime(),
                          server_default=sa.func.now()),
            )
            op.create_index("ix_da_dev_id", "device_assignments", ["dev_id"])
            op.create_index("ix_da_pat_id", "device_assignments", ["pat_id"])


def downgrade() -> None:
    bind = op.get_bind()

    # ================================================================
    # RUNTIME DB 롤백
    # ================================================================
    if _is_runtime(bind):

        # device_assignments 삭제
        inspector = sa.inspect(bind)
        if "device_assignments" in inspector.get_table_names():
            op.drop_index("ix_da_pat_id", table_name="device_assignments")
            op.drop_index("ix_da_dev_id", table_name="device_assignments")
            op.drop_table("device_assignments")

        # monthly_updates: travel_id 복원
        cols = _get_columns(bind, "monthly_updates")
        if "travel_id" not in cols:
            with op.batch_alter_table("monthly_updates", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column("travel_id", sa.Integer(),
                              sa.ForeignKey("travels.t_id"), nullable=True)
                )

        # travels: ix_travel_pat_dates 제거, rt_id 제거
        existing_indexes = _get_indexes(bind, "travels")
        cols = _get_columns(bind, "travels")
        with op.batch_alter_table("travels", schema=None) as batch_op:
            if "ix_travel_pat_dates" in existing_indexes:
                batch_op.drop_index("ix_travel_pat_dates")
            if "rt_id" in cols:
                batch_op.drop_column("rt_id")

    # ================================================================
    # ONBOARDING DB 롤백
    # ================================================================
    if _is_onboarding(bind):

        # document_templates: UniqueConstraint 제거
        existing_indexes = _get_indexes(bind, "document_templates")
        if "uq_doctemp_type_keyword" in existing_indexes:
            with op.batch_alter_table("document_templates", schema=None) as batch_op:
                batch_op.drop_constraint("uq_doctemp_type_keyword", type_="unique")

        # security_settings: ss_id → id
        cols = _get_columns(bind, "security_settings")
        if "ss_id" in cols:
            with op.batch_alter_table("security_settings", schema=None) as batch_op:
                batch_op.alter_column("ss_id", new_column_name="id")

        # operators: vendor_id 제거, hosp_code 복원
        cols = _get_columns(bind, "operators")
        with op.batch_alter_table("operators", schema=None) as batch_op:
            if "vendor_id" in cols:
                batch_op.drop_column("vendor_id")
            if "hosp_code" not in cols:
                batch_op.add_column(
                    sa.Column("hosp_code", sa.String(), nullable=True)
                )

        # vendors: is_hospital_internal 복원
        cols = _get_columns(bind, "vendors")
        if "is_hospital_internal" not in cols:
            with op.batch_alter_table("vendors", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column("is_hospital_internal", sa.Boolean(), default=False)
                )

        # frequent_hospitals: bc_id, reg_doc_path 복원
        cols = _get_columns(bind, "frequent_hospitals")
        with op.batch_alter_table("frequent_hospitals", schema=None) as batch_op:
            if "bc_id" not in cols:
                batch_op.add_column(
                    sa.Column("bc_id", sa.Integer(),
                              sa.ForeignKey("business_certificates.bc_id"), nullable=True)
                )
            if "reg_doc_path" not in cols:
                batch_op.add_column(
                    sa.Column("reg_doc_path", sa.String(), nullable=True)
                )
