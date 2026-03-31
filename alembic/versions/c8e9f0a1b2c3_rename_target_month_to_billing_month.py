"""rename target_month to billing_month

Revision ID: c8e9f0a1b2c3
Revises: b7d8e9f0a1b2
Create Date: 2026-03-31 12:00:00.000000

target_month → billing_month 컬럼명 통일 (MonthlyUpdate, Claim, PatientAlert)
인덱스/제약조건도 함께 변경. 데이터 형식("YYYY-MM")은 그대로 유지.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "b7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── monthly_updates: target_month → billing_month ──
    with op.batch_alter_table("monthly_updates", schema=None) as batch_op:
        batch_op.alter_column("target_month", new_column_name="billing_month")
        batch_op.drop_constraint("uq_mu_pat_month", type_="unique")
        batch_op.drop_index("ix_mu_target_month")
        batch_op.create_unique_constraint("uq_mu_pat_month", ["pat_id", "billing_month"])
        batch_op.create_index("ix_mu_billing_month", ["billing_month"])

    # ── claims: target_month → billing_month ──
    with op.batch_alter_table("claims", schema=None) as batch_op:
        batch_op.alter_column("target_month", new_column_name="billing_month")
        batch_op.drop_index("ix_claims_target_month")
        batch_op.create_index("ix_claims_billing_month", ["billing_month"])

    # ── patient_alerts: target_month → billing_month ──
    with op.batch_alter_table("patient_alerts", schema=None) as batch_op:
        batch_op.alter_column("target_month", new_column_name="billing_month")
        batch_op.drop_index("ix_alert_target_month")
        batch_op.create_index("ix_alert_billing_month", ["billing_month"])


def downgrade() -> None:
    # ── patient_alerts: billing_month → target_month ──
    with op.batch_alter_table("patient_alerts", schema=None) as batch_op:
        batch_op.alter_column("billing_month", new_column_name="target_month")
        batch_op.drop_index("ix_alert_billing_month")
        batch_op.create_index("ix_alert_target_month", ["target_month"])

    # ── claims: billing_month → target_month ──
    with op.batch_alter_table("claims", schema=None) as batch_op:
        batch_op.alter_column("billing_month", new_column_name="target_month")
        batch_op.drop_index("ix_claims_billing_month")
        batch_op.create_index("ix_claims_target_month", ["target_month"])

    # ── monthly_updates: billing_month → target_month ──
    with op.batch_alter_table("monthly_updates", schema=None) as batch_op:
        batch_op.alter_column("billing_month", new_column_name="target_month")
        batch_op.drop_constraint("uq_mu_pat_month", type_="unique")
        batch_op.drop_index("ix_mu_billing_month")
        batch_op.create_unique_constraint("uq_mu_pat_month", ["pat_id", "target_month"])
        batch_op.create_index("ix_mu_target_month", ["target_month"])
