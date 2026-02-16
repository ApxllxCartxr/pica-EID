"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-02-16 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Admin Accounts
    op.create_table(
        'admin_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('access_level', sa.Enum('VIEWER', 'ADMIN', 'SUPERADMIN', name='accesslevel'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_admin_accounts_username'), 'admin_accounts', ['username'], unique=True)

    # 2. Domains
    op.create_table(
        'domains',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_domains_name'), 'domains', ['name'], unique=True)

    # 3. Divisions
    op.create_table(
        'divisions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_divisions_name'), 'divisions', ['name'], unique=True)

    # 4. Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ulid', sa.String(length=26), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('category', sa.Enum('INTERN', 'EMPLOYEE', name='usercategory'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'EXPIRED', 'CONVERTED', name='userstatus'), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=True),
        sa.Column('division_id', sa.Integer(), nullable=True),
        sa.Column('conversion_date', sa.DateTime(), nullable=True),
        sa.Column('date_of_joining', sa.Date(), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['division_id'], ['divisions.id'], ),
        sa.ForeignKeyConstraint(['domain_id'], ['domains.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('ulid')
    )
    op.create_index('ix_users_category_status', 'users', ['category', 'status'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index('ix_users_name_search', 'users', ['name'], unique=False)
    op.create_index(op.f('ix_users_ulid'), 'users', ['ulid'], unique=True)
    op.create_index('ix_users_ulid_suffix', 'users', ['ulid'], unique=False)

    # 5. Roles
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('clearance_level', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=False)
    op.create_index('ix_roles_name_active', 'roles', ['name'], unique=True, postgresql_where=sa.text('is_active IS true'))

    # 6. User Roles
    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('removed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['admin_accounts.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role_active')
    )
    op.create_index('ix_user_roles_active', 'user_roles', ['user_id', 'role_id'], unique=False)

    # 7. Internship Tracking
    op.create_table(
        'internship_tracking',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('extended_count', sa.Integer(), nullable=True),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'EXPIRED', 'EXTENDED', 'CONVERTED', name='internshipstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_internship_end_date', 'internship_tracking', ['end_date'], unique=False)
    op.create_index('ix_internship_status', 'internship_tracking', ['status'], unique=False)

    # 8. Api Keys
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=12), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('scopes', sa.Text(), server_default='*', nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['admin_accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index(op.f('ix_api_keys_key_prefix'), 'api_keys', ['key_prefix'], unique=False)

    # 9. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=50), nullable=True),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('previous_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['changed_by'], ['admin_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_action_time', 'audit_logs', ['action', 'timestamp'], unique=False)
    op.create_index('ix_audit_entity', 'audit_logs', ['entity_type', 'entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)

    # 10. Conversion History
    op.create_table(
        'conversion_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_ulid', sa.String(length=26), nullable=False),
        sa.Column('previous_category', sa.String(length=20), nullable=False),
        sa.Column('new_category', sa.String(length=20), nullable=False),
        sa.Column('converted_by', sa.Integer(), nullable=False),
        sa.Column('conversion_date', sa.DateTime(), nullable=False),
        sa.Column('roles_migrated', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['converted_by'], ['admin_accounts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. Id Migration Map
    op.create_table(
        'id_migration_map',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('old_user_id', sa.String(length=30), nullable=False),
        sa.Column('new_ulid', sa.String(length=26), nullable=False),
        sa.Column('migrated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_id_migration_map_new_ulid'), 'id_migration_map', ['new_ulid'], unique=False)
    op.create_index(op.f('ix_id_migration_map_old_user_id'), 'id_migration_map', ['old_user_id'], unique=True)


def downgrade() -> None:
    op.drop_table('id_migration_map')
    op.drop_table('conversion_history')
    op.drop_table('audit_logs')
    op.drop_table('api_keys')
    op.drop_table('internship_tracking')
    op.drop_table('user_roles')
    op.drop_table('roles')
    op.drop_table('users')
    op.drop_table('divisions')
    op.drop_table('domains')
    op.drop_table('admin_accounts')
