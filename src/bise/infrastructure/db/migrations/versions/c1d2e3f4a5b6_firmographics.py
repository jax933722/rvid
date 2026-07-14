"""firmographics: company location, founding, size, contact + search projection

Revision ID: c1d2e3f4a5b6
Revises: 2a68ace07acd
Create Date: 2026-07-14 09:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: str | None = '2a68ace07acd'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.add_column(sa.Column('country', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('state', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('city', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('founded_year', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('employee_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('contact_email', sa.String(length=320), nullable=True))
        batch_op.add_column(sa.Column('contact_phone', sa.String(length=64), nullable=True))
        batch_op.create_index(batch_op.f('ix_companies_country'), ['country'], unique=False)
        batch_op.create_index(batch_op.f('ix_companies_state'), ['state'], unique=False)
        batch_op.create_index(batch_op.f('ix_companies_city'), ['city'], unique=False)
        batch_op.create_index(
            batch_op.f('ix_companies_founded_year'), ['founded_year'], unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_companies_employee_count'), ['employee_count'], unique=False
        )

    with op.batch_alter_table('search_documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('founded_year', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('employee_count', sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_search_documents_founded_year'), ['founded_year'], unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_search_documents_employee_count'), ['employee_count'], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table('search_documents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_search_documents_employee_count'))
        batch_op.drop_index(batch_op.f('ix_search_documents_founded_year'))
        batch_op.drop_column('employee_count')
        batch_op.drop_column('founded_year')

    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_companies_employee_count'))
        batch_op.drop_index(batch_op.f('ix_companies_founded_year'))
        batch_op.drop_index(batch_op.f('ix_companies_city'))
        batch_op.drop_index(batch_op.f('ix_companies_state'))
        batch_op.drop_index(batch_op.f('ix_companies_country'))
        batch_op.drop_column('contact_phone')
        batch_op.drop_column('contact_email')
        batch_op.drop_column('employee_count')
        batch_op.drop_column('founded_year')
        batch_op.drop_column('city')
        batch_op.drop_column('state')
        batch_op.drop_column('country')
