"""refactor_division_to_domain_and_add_division

Revision ID: a3807c345d6c
Revises: 3e34fb4b2802
Create Date: 2026-02-13 13:36:31.461388
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3807c345d6c'
down_revision: Union[str, None] = '3e34fb4b2802'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename existing 'divisions' table to 'domains'
    op.rename_table('divisions', 'domains')
    op.execute('ALTER SEQUENCE divisions_id_seq RENAME TO domains_id_seq')
    op.execute('ALTER INDEX ix_divisions_name RENAME TO ix_domains_name')

    # 2. Update 'users' table
    # Rename division_id to domain_id
    op.alter_column('users', 'division_id', new_column_name='domain_id')
    
    # Drop old FK and create new one for domain_id -> domains.id
    # Note: Constraint name might vary, try to drop using generic name or catch error?
    # Usually standard naming: users_division_id_fkey
    op.drop_constraint('users_division_id_fkey', 'users', type_='foreignkey')
    op.create_foreign_key('fk_users_domain_id', 'users', 'domains', ['domain_id'], ['id'])

    # 3. Create new 'divisions' table
    op.create_table(
        'divisions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_divisions_name'), 'divisions', ['name'], unique=True)

    # 4. Add 'division_id' column to 'users'
    op.add_column('users', sa.Column('division_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_division_id', 'users', 'divisions', ['division_id'], ['id'])


def downgrade() -> None:
    # 1. Drop 'division_id' from 'users'
    op.drop_constraint('fk_users_division_id', 'users', type_='foreignkey')
    op.drop_column('users', 'division_id')

    # 2. Drop new 'divisions' table
    op.drop_index(op.f('ix_divisions_name'), table_name='divisions')
    op.drop_table('divisions')

    # 3. Revert 'users' table changes
    op.drop_constraint('fk_users_domain_id', 'users', type_='foreignkey')
    op.alter_column('users', 'domain_id', new_column_name='division_id')
    op.create_foreign_key('users_division_id_fkey', 'users', 'divisions', ['division_id'], ['id'])

    # 4. Rename 'domains' back to 'divisions'
    op.execute('ALTER INDEX ix_domains_name RENAME TO ix_divisions_name')
    op.execute('ALTER SEQUENCE domains_id_seq RENAME TO divisions_id_seq')
    op.rename_table('domains', 'divisions')
