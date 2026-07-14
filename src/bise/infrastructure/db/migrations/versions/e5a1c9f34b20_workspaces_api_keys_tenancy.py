"""workspaces, api keys, and workspace-scoped personal data

Revision ID: e5a1c9f34b20
Revises: d81bdde11610
Create Date: 2026-07-14 11:15:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'e5a1c9f34b20'
down_revision: str | None = 'd81bdde11610'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- tenant tables -----------------------------------------------------
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_workspaces_slug'),
    )
    with op.batch_alter_table('workspaces', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_workspaces_slug'), ['slug'], unique=False)

    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('prefix', sa.String(length=16), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash', name='uq_api_keys_hash'),
    )
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_api_keys_key_hash'), ['key_hash'], unique=False)
        batch_op.create_index(batch_op.f('ix_api_keys_workspace_id'), ['workspace_id'], unique=False)

    # Seed the default workspace so existing personal data can be backfilled and
    # so the opt-in-auth flow always has a workspace to fall back to.
    workspaces = sa.table(
        'workspaces', sa.column('id', sa.Integer), sa.column('name', sa.String),
        sa.column('slug', sa.String),
    )
    op.bulk_insert(workspaces, [{'id': 1, 'name': 'Default', 'slug': 'default'}])

    # --- scope personal data to a workspace --------------------------------
    for table in ('saved_searches', 'company_lists'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(
                sa.Column('workspace_id', sa.Integer(), nullable=False, server_default='1')
            )
            batch_op.create_index(
                batch_op.f(f'ix_{table}_workspace_id'), ['workspace_id'], unique=False
            )
            batch_op.create_foreign_key(
                f'fk_{table}_workspace', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE'
            )

    # company_tags also needs its uniqueness widened to include the workspace.
    with op.batch_alter_table('company_tags', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('workspace_id', sa.Integer(), nullable=False, server_default='1')
        )
        batch_op.create_index(
            batch_op.f('ix_company_tags_workspace_id'), ['workspace_id'], unique=False
        )
        batch_op.create_foreign_key(
            'fk_company_tags_workspace', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE'
        )
        batch_op.drop_constraint('uq_company_label', type_='unique')
        batch_op.create_unique_constraint(
            'uq_ws_company_label', ['workspace_id', 'company_id', 'label']
        )


def downgrade() -> None:
    with op.batch_alter_table('company_tags', schema=None) as batch_op:
        batch_op.drop_constraint('uq_ws_company_label', type_='unique')
        batch_op.create_unique_constraint('uq_company_label', ['company_id', 'label'])
        batch_op.drop_constraint('fk_company_tags_workspace', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_company_tags_workspace_id'))
        batch_op.drop_column('workspace_id')

    for table in ('company_lists', 'saved_searches'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(f'fk_{table}_workspace', type_='foreignkey')
            batch_op.drop_index(batch_op.f(f'ix_{table}_workspace_id'))
            batch_op.drop_column('workspace_id')

    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_api_keys_workspace_id'))
        batch_op.drop_index(batch_op.f('ix_api_keys_key_hash'))
    op.drop_table('api_keys')
    with op.batch_alter_table('workspaces', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_workspaces_slug'))
    op.drop_table('workspaces')
