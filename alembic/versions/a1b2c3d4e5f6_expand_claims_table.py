"""expand_claims_table

Revision ID: a1b2c3d4e5f6
Revises: f3e92092455d
Create Date: 2026-03-28 22:00:00.000000

Claim 테이블 확장: 건보/본인 분리, 마스크비, 해외공제, 반납전환 컬럼 추가
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f3e92092455d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('claims', schema=None) as batch_op:
        # pat_id + index
        batch_op.add_column(sa.Column('pat_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_claims_pat_id', 'patients', ['pat_id'], ['pat_id'])
        batch_op.create_index('ix_claims_pat_id', ['pat_id'], unique=False)

        # 기본 청구액
        batch_op.add_column(sa.Column('base_total', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('base_insurance', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('base_self_pay', sa.Integer(), nullable=True))

        # 마스크비
        batch_op.add_column(sa.Column('mask_insurance', sa.Integer(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('mask_self_pay', sa.Integer(), server_default='0', nullable=True))

        # 해외출국 공제
        batch_op.add_column(sa.Column('travel_deduct_days', sa.Integer(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('travel_deduct_amount', sa.Integer(), server_default='0', nullable=True))

        # 반납월 공제 → 본인부담금 전환
        batch_op.add_column(sa.Column('return_deduct_to_self', sa.Integer(), server_default='0', nullable=True))

        # 최종 금액
        batch_op.add_column(sa.Column('final_insurance', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('final_self_pay', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('claims', schema=None) as batch_op:
        batch_op.drop_column('final_self_pay')
        batch_op.drop_column('final_insurance')
        batch_op.drop_column('return_deduct_to_self')
        batch_op.drop_column('travel_deduct_amount')
        batch_op.drop_column('travel_deduct_days')
        batch_op.drop_column('mask_self_pay')
        batch_op.drop_column('mask_insurance')
        batch_op.drop_column('base_self_pay')
        batch_op.drop_column('base_insurance')
        batch_op.drop_column('base_total')
        batch_op.drop_index('ix_claims_pat_id')
        batch_op.drop_column('pat_id')
