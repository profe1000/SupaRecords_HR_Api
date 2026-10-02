"""leave allowance, leave applications and staff requests

Revision ID: a1d4e7b2c901
Revises: c75f4ff57f55
Create Date: 2026-10-02 09:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1d4e7b2c901'
down_revision = 'c75f4ff57f55'
branch_labels = None
depends_on = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
    ]


def _audit_constraints(table: str) -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(['created_by'], ['staff.id'], name=op.f(f'fk_{table}_created_by_staff'), use_alter=True),
        sa.ForeignKeyConstraint(['deleted_by'], ['staff.id'], name=op.f(f'fk_{table}_deleted_by_staff'), use_alter=True),
        sa.ForeignKeyConstraint(['updated_by'], ['staff.id'], name=op.f(f'fk_{table}_updated_by_staff'), use_alter=True),
    ]


def upgrade() -> None:
    op.create_table('leave_allowance',
    sa.Column('staff_id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('total_days', sa.Integer(), nullable=False),
    *_audit_columns(),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], name=op.f('fk_leave_allowance_staff_id_staff')),
    *_audit_constraints('leave_allowance'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_leave_allowance')),
    sa.UniqueConstraint('staff_id', 'year', name=op.f('uq_leave_allowance_staff_id')),
    )
    op.create_index(op.f('ix_leave_allowance_staff_id'), 'leave_allowance', ['staff_id'], unique=False)

    op.create_table('leave_application',
    sa.Column('staff_id', sa.Integer(), nullable=False),
    sa.Column('leave_type', sa.String(length=50), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('days', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('reviewed_by', sa.Integer(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_comment', sa.Text(), nullable=True),
    *_audit_columns(),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], name=op.f('fk_leave_application_staff_id_staff')),
    sa.ForeignKeyConstraint(['reviewed_by'], ['staff.id'], name=op.f('fk_leave_application_reviewed_by_staff')),
    *_audit_constraints('leave_application'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_leave_application')),
    )
    op.create_index(op.f('ix_leave_application_staff_id'), 'leave_application', ['staff_id'], unique=False)

    op.create_table('staff_request',
    sa.Column('staff_id', sa.Integer(), nullable=False),
    sa.Column('request_type', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('reviewed_by', sa.Integer(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_comment', sa.Text(), nullable=True),
    *_audit_columns(),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], name=op.f('fk_staff_request_staff_id_staff')),
    sa.ForeignKeyConstraint(['reviewed_by'], ['staff.id'], name=op.f('fk_staff_request_reviewed_by_staff')),
    *_audit_constraints('staff_request'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_staff_request')),
    )
    op.create_index(op.f('ix_staff_request_staff_id'), 'staff_request', ['staff_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_staff_request_staff_id'), table_name='staff_request')
    op.drop_table('staff_request')
    op.drop_index(op.f('ix_leave_application_staff_id'), table_name='leave_application')
    op.drop_table('leave_application')
    op.drop_index(op.f('ix_leave_allowance_staff_id'), table_name='leave_allowance')
    op.drop_table('leave_allowance')
