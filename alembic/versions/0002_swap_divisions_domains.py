"""swap_divisions_domains

Revision ID: 0002_swap_divisions_domains
Revises: 0001_initial_schema
Create Date: 2026-02-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_swap_divisions_domains'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Swap Table Names
    # Rename divisions -> temp_swap
    op.rename_table('divisions', 'temp_swap')
    # Rename domains -> divisions
    op.rename_table('domains', 'divisions')
    # Rename temp_swap -> domains
    op.rename_table('temp_swap', 'domains')
    
    # 2. Add end_date to users
    op.add_column('users', sa.Column('end_date', sa.Date(), nullable=True))
    
    # 3. Swap User FK Columns
    # Rename division_id -> temp_id
    op.alter_column('users', 'division_id', new_column_name='temp_id')
    # Rename domain_id -> division_id
    op.alter_column('users', 'domain_id', new_column_name='division_id')
    # Rename temp_id -> domain_id
    op.alter_column('users', 'temp_id', new_column_name='domain_id')


def downgrade() -> None:
    # Reverse everything
    op.alter_column('users', 'domain_id', new_column_name='temp_id')
    op.alter_column('users', 'division_id', new_column_name='domain_id')
    op.alter_column('users', 'temp_id', new_column_name='division_id')
    
    op.drop_column('users', 'end_date')
    
    op.rename_table('domains', 'temp_swap')
    op.rename_table('divisions', 'domains')
    op.rename_table('temp_swap', 'divisions')
