"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-11-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('avatar_url', sa.Text),
        sa.Column('auth_provider', sa.String(length=20), nullable=False),
        sa.Column('provider_subject', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('auth_provider', 'provider_subject', name='uq_user_auth')
    )
    
    # Organisations table
    op.create_table(
        'organisations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organisation_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organisation_id', 'name', name='uq_team_name')
    )
    
    # Memberships table
    op.create_table(
        'memberships',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('team_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'team_id', name='uq_membership')
    )
    
    # Organisation admins table
    op.create_table(
        'organisation_admins',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('organisation_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'organisation_id', name='uq_org_admin')
    )
    
    # Super admins table
    op.create_table(
        'super_admins',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', name='uq_super_admin')
    )
    
    # Indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_auth', 'users', ['auth_provider', 'provider_subject'])
    op.create_index('idx_memberships_user', 'memberships', ['user_id'])
    op.create_index('idx_memberships_team', 'memberships', ['team_id'])
    op.create_index('idx_teams_org', 'teams', ['organisation_id'])
    op.create_index('idx_org_admins_user', 'organisation_admins', ['user_id'])
    op.create_index('idx_org_admins_org', 'organisation_admins', ['organisation_id'])


def downgrade():
    # Drop indexes first
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_auth', table_name='users')
    op.drop_index('idx_memberships_user', table_name='memberships')
    op.drop_index('idx_memberships_team', table_name='memberships')
    op.drop_index('idx_teams_org', table_name='teams')
    op.drop_index('idx_org_admins_user', table_name='organisation_admins')
    op.drop_index('idx_org_admins_org', table_name='organisation_admins')
    
    # Drop tables
    op.drop_table('super_admins')
    op.drop_table('organisation_admins')
    op.drop_table('memberships')
    op.drop_table('teams')
    op.drop_table('organisations')
    op.drop_table('users')
