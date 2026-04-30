"""remove_cross_db_fk_device_assignments

Revision ID: 7352aa9d03e4
Revises: a2b3c4d5e6f7
Create Date: 2026-04-23 23:00:53.370887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7352aa9d03e4'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Runtime DB의 device_assignments.dev_id는 onboarding DB의 devices를 참조하므로
    물리 FK를 유지할 수 없습니다. SQLite cross-DB FK 불가 이슈를 피하기 위해
    테이블을 재생성하여 dev_id FK를 제거합니다.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "device_assignments" not in inspector.get_table_names():
        return

    fk_list = inspector.get_foreign_keys("device_assignments")
    has_cross_db_fk = any(
        (fk.get("referred_table") == "devices") for fk in fk_list
    )
    if not has_cross_db_fk:
        return

    op.execute("PRAGMA foreign_keys=OFF")
    op.execute(
        """
        CREATE TABLE device_assignments_new (
            da_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            dev_id INTEGER NOT NULL,
            pat_id INTEGER NOT NULL,
            ct_id INTEGER NULL,
            assigned_at DATE NOT NULL,
            returned_at DATE NULL,
            created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY(pat_id) REFERENCES patients (pat_id),
            FOREIGN KEY(ct_id) REFERENCES contracts (ct_id)
        )
        """
    )
    op.execute(
        """
        INSERT INTO device_assignments_new
            (da_id, dev_id, pat_id, ct_id, assigned_at, returned_at, created_at)
        SELECT
            da_id, dev_id, pat_id, ct_id, assigned_at, returned_at, created_at
        FROM device_assignments
        """
    )
    op.execute("DROP TABLE device_assignments")
    op.execute("ALTER TABLE device_assignments_new RENAME TO device_assignments")
    op.execute("CREATE INDEX IF NOT EXISTS ix_da_dev_id ON device_assignments (dev_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_da_pat_id ON device_assignments (pat_id)")
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    """Downgrade schema.

    이전 스키마로 되돌리기 위해 dev_id -> devices.dev_id FK를 복구합니다.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "device_assignments" not in inspector.get_table_names():
        return

    fk_list = inspector.get_foreign_keys("device_assignments")
    has_cross_db_fk = any(
        (fk.get("referred_table") == "devices") for fk in fk_list
    )
    if has_cross_db_fk:
        return

    op.execute("PRAGMA foreign_keys=OFF")
    op.execute(
        """
        CREATE TABLE device_assignments_old (
            da_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            dev_id INTEGER NOT NULL,
            pat_id INTEGER NOT NULL,
            ct_id INTEGER NULL,
            assigned_at DATE NOT NULL,
            returned_at DATE NULL,
            created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY(dev_id) REFERENCES devices (dev_id),
            FOREIGN KEY(pat_id) REFERENCES patients (pat_id),
            FOREIGN KEY(ct_id) REFERENCES contracts (ct_id)
        )
        """
    )
    op.execute(
        """
        INSERT INTO device_assignments_old
            (da_id, dev_id, pat_id, ct_id, assigned_at, returned_at, created_at)
        SELECT
            da_id, dev_id, pat_id, ct_id, assigned_at, returned_at, created_at
        FROM device_assignments
        """
    )
    op.execute("DROP TABLE device_assignments")
    op.execute("ALTER TABLE device_assignments_old RENAME TO device_assignments")
    op.execute("CREATE INDEX IF NOT EXISTS ix_da_dev_id ON device_assignments (dev_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_da_pat_id ON device_assignments (pat_id)")
    op.execute("PRAGMA foreign_keys=ON")
