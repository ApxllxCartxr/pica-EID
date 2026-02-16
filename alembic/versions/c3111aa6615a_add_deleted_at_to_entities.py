"""add_deleted_at_to_entities

Revision ID: c3111aa6615a
Revises: 9691b825f1fc
Create Date: 2026-02-15 16:30:20.596629
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3111aa6615a'
down_revision: Union[str, None] = '9691b825f1fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deleted_at column to domains
    op.add_column('domains', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    
    # Add deleted_at column to divisions
    op.add_column('divisions', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    
    # Add deleted_at column to roles
    op.add_column('roles', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove deleted_at column from roles
    op.drop_column('roles', 'deleted_at')
    
    # Remove deleted_at column from divisions
    op.drop_column('divisions', 'deleted_at')
    
    # Remove deleted_at column from domains
    op.drop_column('domains', 'deleted_at')
