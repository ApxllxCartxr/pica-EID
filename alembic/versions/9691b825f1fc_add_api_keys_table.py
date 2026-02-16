"""add_api_keys_table

Revision ID: 9691b825f1fc
Revises: a3807c345d6c
Create Date: 2026-02-13 14:03:25.983055

The api_keys table is created declaratively via Base.metadata.create_all().
This migration ensures Alembic is aware of it for future autogenerate runs.
If the table does not exist yet, it will be created here.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9691b825f1fc'
down_revision: Union[str, None] = 'a3807c345d6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the api_keys table if it doesn't already exist
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=12), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=False, server_default='*'),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['admin_accounts.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
        if_not_exists=True,
    )
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'], if_not_exists=True)


def downgrade() -> None:
    op.drop_index('ix_api_keys_key_prefix', table_name='api_keys')
    op.drop_table('api_keys')
