"""task.branch_id so tasks can be scoped to a business and filtered by branch

Revision ID: c4d9e1f7a2b3
Revises: b7e3c5d1f402
Create Date: 2026-10-02 15:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d9e1f7a2b3'
down_revision = 'b7e3c5d1f402'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('task', sa.Column('branch_id', sa.Integer(), nullable=True))
    op.create_foreign_key(op.f('fk_task_branch_id_business_branch'), 'task', 'business_branch', ['branch_id'], ['id'])
    op.create_index(op.f('ix_task_branch_id'), 'task', ['branch_id'], unique=False)
    # Backfill existing tasks: the assignee's branch, otherwise the creator's branch.
    op.execute(
        """
        UPDATE task SET branch_id = COALESCE(
            (SELECT staff.branch_id FROM staff WHERE staff.id = task.assigned_staff_id),
            (SELECT staff.branch_id FROM staff WHERE staff.id = task.created_by)
        )
        WHERE branch_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_task_branch_id'), table_name='task')
    op.drop_constraint(op.f('fk_task_branch_id_business_branch'), 'task', type_='foreignkey')
    op.drop_column('task', 'branch_id')
