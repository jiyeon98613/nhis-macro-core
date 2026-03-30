"""schema_v2_biz_cert_claim_split_alerts

Revision ID: b7d8e9f0a1b2
Revises: 6ed17c42ba98
Create Date: 2026-03-29 10:00:00.000000

주요 변경:
  [Onboarding]
  - business_certificates 테이블 신규 생성
  - hospitals: bc_id, reg_doc_path 추가
  - doctors: license_doc_path 추가
  - vendors: bc_id 추가, rep_name/address/biz_type/biz_item/email 제거 (→ BusinessCertificate)

  [Runtime]
  - patient_biz_info 테이블 삭제 (→ BusinessCertificate로 통합)
  - patients: biz_cert_id 추가
  - prescriptions/sleep_reports/contracts/return_receipts: pat_id 추가
  - sleep_reports: report_start_date, report_end_date 추가
  - consumables: c_note 추가
  - monthly_updates: yyyymm→target_month, claim_id_1/2/3, updated_at 추가, unique 제약
  - claims: billing_month→target_month, period_start/end/days, split_reason,
            required_docs/attached_docs, sr_count 추가, mask 컬럼 제거
  - patient_alerts 테이블 신규 생성
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "6ed17c42ba98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ──────────────────────────────────────────────────────────
# UPGRADE
# ──────────────────────────────────────────────────────────
def upgrade() -> None:

    # ================================================================
    # Onboarding DB
    # ================================================================

    # 1. business_certificates (신규)
    op.create_table(
        "business_certificates",
        sa.Column("bc_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("biz_num", sa.String(), unique=True, nullable=False),
        sa.Column("company_name", sa.String(), nullable=True),
        sa.Column("rep_name", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("biz_type", sa.String(), nullable=True),
        sa.Column("biz_item", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("doc_path", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # 2. hospitals: bc_id, reg_doc_path 추가
    with op.batch_alter_table("hospitals", schema=None) as batch_op:
        batch_op.add_column(sa.Column("bc_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("reg_doc_path", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_hospitals_bc_id", "business_certificates", ["bc_id"], ["bc_id"]
        )

    # 3. doctors: license_doc_path 추가
    with op.batch_alter_table("doctors", schema=None) as batch_op:
        batch_op.add_column(sa.Column("license_doc_path", sa.String(), nullable=True))

    # 4. vendors: bc_id 추가, 상세 biz 필드 제거
    #    (기존 데이터가 있으면 먼저 BusinessCertificate로 이관 필요)
    with op.batch_alter_table("vendors", schema=None) as batch_op:
        batch_op.add_column(sa.Column("bc_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_vendors_bc_id", "business_certificates", ["bc_id"], ["bc_id"]
        )
        # 최근 마이그레이션(6ed17c42ba98)에서 추가했던 상세 필드 → BC로 이전
        batch_op.drop_column("rep_name")
        batch_op.drop_column("address")
        batch_op.drop_column("biz_type")
        batch_op.drop_column("biz_item")
        batch_op.drop_column("email")

    # ================================================================
    # Runtime DB
    # ================================================================

    # 5. patients: biz_cert_id 추가
    with op.batch_alter_table("patients", schema=None) as batch_op:
        batch_op.add_column(sa.Column("biz_cert_id", sa.Integer(), nullable=True))

    # 6. patient_biz_info 삭제
    op.drop_table("patient_biz_info")

    # 7. prescriptions: pat_id 추가
    with op.batch_alter_table("prescriptions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pat_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_prescriptions_pat_id", "patients", ["pat_id"], ["pat_id"]
        )
        batch_op.create_index("ix_prescriptions_pat_id", ["pat_id"])

    # 8. sleep_reports: pat_id, report_start_date, report_end_date 추가
    with op.batch_alter_table("sleep_reports", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pat_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_sleep_reports_pat_id", "patients", ["pat_id"], ["pat_id"]
        )
        batch_op.create_index("ix_sleep_reports_pat_id", ["pat_id"])
        batch_op.add_column(sa.Column("report_start_date", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("report_end_date", sa.DateTime(), nullable=True))

    # 9. contracts: pat_id 추가
    with op.batch_alter_table("contracts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pat_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_contracts_pat_id", "patients", ["pat_id"], ["pat_id"]
        )
        batch_op.create_index("ix_contracts_pat_id", ["pat_id"])

    # 10. return_receipts: pat_id 추가
    with op.batch_alter_table("return_receipts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pat_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_return_receipts_pat_id", "patients", ["pat_id"], ["pat_id"]
        )
        batch_op.create_index("ix_return_receipts_pat_id", ["pat_id"])

    # 11. consumables: c_note 추가, pat_id 인덱스
    with op.batch_alter_table("consumables", schema=None) as batch_op:
        batch_op.add_column(sa.Column("c_note", sa.String(), nullable=True))
        batch_op.create_index("ix_consumables_pat_id", ["pat_id"])

    # 12. travels: pat_id 인덱스
    with op.batch_alter_table("travels", schema=None) as batch_op:
        batch_op.create_index("ix_travels_pat_id", ["pat_id"])

    # 13. monthly_updates: yyyymm→target_month, claim_id_1/2/3, updated_at, unique
    #     SQLite batch mode: 테이블 재생성으로 처리
    with op.batch_alter_table("monthly_updates", schema=None) as batch_op:
        # 새 컬럼 추가
        batch_op.add_column(sa.Column("target_month", sa.String(7), nullable=True))
        batch_op.add_column(sa.Column("claim_id_1", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("claim_id_2", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("claim_id_3", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True)
        )
        batch_op.add_column(sa.Column("status", sa.String(), server_default="PENDING", nullable=True))
        batch_op.create_index("ix_mu_target_month", ["target_month"])

    # yyyymm → target_month 데이터 변환 (YYYYMM → YYYY-MM)
    op.execute(
        "UPDATE monthly_updates "
        "SET target_month = substr(yyyymm, 1, 4) || '-' || substr(yyyymm, 5, 2) "
        "WHERE yyyymm IS NOT NULL AND target_month IS NULL"
    )

    # yyyymm 컬럼 삭제 + unique 제약 추가 (batch로 재생성)
    with op.batch_alter_table("monthly_updates", schema=None) as batch_op:
        batch_op.drop_column("yyyymm")
        batch_op.create_unique_constraint("uq_mu_pat_month", ["pat_id", "target_month"])
        batch_op.alter_column("target_month", nullable=False)

    # 14. claims: billing_month→target_month, 신규컬럼, mask 컬럼 제거
    with op.batch_alter_table("claims", schema=None) as batch_op:
        # 새 컬럼 추가
        batch_op.add_column(sa.Column("target_month", sa.String(7), nullable=True))
        batch_op.add_column(sa.Column("period_start", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("period_end", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("period_days", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("split_reason", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("required_docs", sa.String(), server_default="", nullable=True))
        batch_op.add_column(sa.Column("attached_docs", sa.String(), server_default="", nullable=True))
        batch_op.add_column(sa.Column("sr_count_required", sa.Integer(), server_default="0", nullable=True))
        batch_op.add_column(sa.Column("sr_count_attached", sa.Integer(), server_default="0", nullable=True))
        batch_op.add_column(
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=True)
        )

    # billing_month → target_month 데이터 변환
    op.execute(
        "UPDATE claims "
        "SET target_month = substr(billing_month, 1, 4) || '-' || substr(billing_month, 5, 2) "
        "WHERE billing_month IS NOT NULL AND target_month IS NULL"
    )

    # 구 컬럼 삭제 + 인덱스
    with op.batch_alter_table("claims", schema=None) as batch_op:
        batch_op.drop_column("billing_month")
        batch_op.drop_column("mask_insurance")
        batch_op.drop_column("mask_self_pay")
        batch_op.create_index("ix_claims_target_month", ["target_month"])

    # 15. patient_alerts (신규)
    op.create_table(
        "patient_alerts",
        sa.Column("alert_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pat_id", sa.Integer(), sa.ForeignKey("patients.pat_id"), nullable=False),
        sa.Column("alert_type", sa.String(), nullable=True),
        sa.Column("target_month", sa.String(7), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), server_default="0"),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_alert_pat_id", "patient_alerts", ["pat_id"])
    op.create_index("ix_alert_target_month", "patient_alerts", ["target_month"])


# ──────────────────────────────────────────────────────────
# DOWNGRADE
# ──────────────────────────────────────────────────────────
def downgrade() -> None:
    # patient_alerts 삭제
    op.drop_index("ix_alert_target_month", table_name="patient_alerts")
    op.drop_index("ix_alert_pat_id", table_name="patient_alerts")
    op.drop_table("patient_alerts")

    # claims: target_month→billing_month 복원, mask 컬럼 복원
    with op.batch_alter_table("claims", schema=None) as batch_op:
        batch_op.add_column(sa.Column("billing_month", sa.String(6), nullable=True))
        batch_op.add_column(sa.Column("mask_insurance", sa.Integer(), server_default="0", nullable=True))
        batch_op.add_column(sa.Column("mask_self_pay", sa.Integer(), server_default="0", nullable=True))

    op.execute(
        "UPDATE claims "
        "SET billing_month = replace(target_month, '-', '') "
        "WHERE target_month IS NOT NULL"
    )

    with op.batch_alter_table("claims", schema=None) as batch_op:
        batch_op.drop_index("ix_claims_target_month")
        batch_op.drop_column("created_at")
        batch_op.drop_column("sr_count_attached")
        batch_op.drop_column("sr_count_required")
        batch_op.drop_column("attached_docs")
        batch_op.drop_column("required_docs")
        batch_op.drop_column("split_reason")
        batch_op.drop_column("period_days")
        batch_op.drop_column("period_end")
        batch_op.drop_column("period_start")
        batch_op.drop_column("target_month")
        batch_op.create_index("ix_claims_billing_month", ["billing_month"])

    # monthly_updates: target_month→yyyymm 복원
    with op.batch_alter_table("monthly_updates", schema=None) as batch_op:
        batch_op.add_column(sa.Column("yyyymm", sa.String(6), nullable=True))

    op.execute(
        "UPDATE monthly_updates "
        "SET yyyymm = replace(target_month, '-', '') "
        "WHERE target_month IS NOT NULL"
    )

    with op.batch_alter_table("monthly_updates", schema=None) as batch_op:
        batch_op.drop_constraint("uq_mu_pat_month", type_="unique")
        batch_op.drop_index("ix_mu_target_month")
        batch_op.drop_column("status")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("claim_id_3")
        batch_op.drop_column("claim_id_2")
        batch_op.drop_column("claim_id_1")
        batch_op.drop_column("target_month")

    # travels: 인덱스 제거
    with op.batch_alter_table("travels", schema=None) as batch_op:
        batch_op.drop_index("ix_travels_pat_id")

    # consumables: c_note 제거, 인덱스 제거
    with op.batch_alter_table("consumables", schema=None) as batch_op:
        batch_op.drop_index("ix_consumables_pat_id")
        batch_op.drop_column("c_note")

    # return_receipts: pat_id 제거
    with op.batch_alter_table("return_receipts", schema=None) as batch_op:
        batch_op.drop_index("ix_return_receipts_pat_id")
        batch_op.drop_column("pat_id")

    # contracts: pat_id 제거
    with op.batch_alter_table("contracts", schema=None) as batch_op:
        batch_op.drop_index("ix_contracts_pat_id")
        batch_op.drop_column("pat_id")

    # sleep_reports: pat_id, report dates 제거
    with op.batch_alter_table("sleep_reports", schema=None) as batch_op:
        batch_op.drop_index("ix_sleep_reports_pat_id")
        batch_op.drop_column("report_end_date")
        batch_op.drop_column("report_start_date")
        batch_op.drop_column("pat_id")

    # prescriptions: pat_id 제거
    with op.batch_alter_table("prescriptions", schema=None) as batch_op:
        batch_op.drop_index("ix_prescriptions_pat_id")
        batch_op.drop_column("pat_id")

    # patient_biz_info 복원
    op.create_table(
        "patient_biz_info",
        sa.Column("pbi_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pat_id", sa.Integer(), sa.ForeignKey("patients.pat_id"), unique=True, nullable=False),
        sa.Column("biz_name", sa.String(), nullable=True),
        sa.Column("biz_rep_name", sa.String(), nullable=True),
        sa.Column("biz_address", sa.String(), nullable=True),
        sa.Column("biz_type", sa.String(), nullable=True),
        sa.Column("biz_item", sa.String(), nullable=True),
        sa.Column("biz_email", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # patients: biz_cert_id 제거
    with op.batch_alter_table("patients", schema=None) as batch_op:
        batch_op.drop_column("biz_cert_id")

    # vendors: bc_id 제거, 상세 필드 복원
    with op.batch_alter_table("vendors", schema=None) as batch_op:
        batch_op.drop_column("bc_id")
        batch_op.add_column(sa.Column("rep_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("address", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("biz_type", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("biz_item", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("email", sa.String(), nullable=True))

    # doctors: license_doc_path 제거
    with op.batch_alter_table("doctors", schema=None) as batch_op:
        batch_op.drop_column("license_doc_path")

    # hospitals: bc_id, reg_doc_path 제거
    with op.batch_alter_table("hospitals", schema=None) as batch_op:
        batch_op.drop_column("reg_doc_path")
        batch_op.drop_column("bc_id")

    # business_certificates 삭제
    op.drop_table("business_certificates")
