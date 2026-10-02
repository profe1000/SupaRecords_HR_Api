"""recruitment: job openings and applicants

Revision ID: b7e3c5d1f402
Revises: a1d4e7b2c901
Create Date: 2026-10-02 12:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e3c5d1f402'
down_revision = 'a1d4e7b2c901'
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
    op.create_table('job_opening',
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('branch_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('employment_type', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('requirements', sa.Text(), nullable=True),
    sa.Column('salary_range', sa.String(length=100), nullable=True),
    sa.Column('closing_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    *_audit_columns(),
    sa.ForeignKeyConstraint(['business_id'], ['business.id'], name=op.f('fk_job_opening_business_id_business')),
    sa.ForeignKeyConstraint(['branch_id'], ['business_branch.id'], name=op.f('fk_job_opening_branch_id_business_branch')),
    *_audit_constraints('job_opening'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_opening')),
    )
    op.create_index(op.f('ix_job_opening_business_id'), 'job_opening', ['business_id'], unique=False)

    op.create_table('job_applicant',
    sa.Column('job_opening_id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('cv_url', sa.String(length=2048), nullable=False),
    sa.Column('cover_letter', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    *_audit_columns(),
    sa.ForeignKeyConstraint(['job_opening_id'], ['job_opening.id'], name=op.f('fk_job_applicant_job_opening_id_job_opening')),
    *_audit_constraints('job_applicant'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_applicant')),
    sa.UniqueConstraint('job_opening_id', 'email', name=op.f('uq_job_applicant_job_opening_id')),
    )
    op.create_index(op.f('ix_job_applicant_job_opening_id'), 'job_applicant', ['job_opening_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_job_applicant_job_opening_id'), table_name='job_applicant')
    op.drop_table('job_applicant')
    op.drop_index(op.f('ix_job_opening_business_id'), table_name='job_opening')
    op.drop_table('job_opening')
