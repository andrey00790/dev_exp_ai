"""Add SSO tables for enterprise authentication

Revision ID: 004_add_sso_tables
Revises: 003_add_users_table
Create Date: 2025-06-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_sso_tables'
down_revision = '003_add_users_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sso_providers table
    op.create_table('sso_providers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('provider_type', sa.String(length=20), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('sso_url', sa.String(length=500), nullable=True),
        sa.Column('slo_url', sa.String(length=500), nullable=True),
        sa.Column('x509_cert', sa.Text(), nullable=True),
        sa.Column('client_id', sa.String(length=255), nullable=True),
        sa.Column('client_secret', sa.String(length=255), nullable=True),
        sa.Column('authorization_url', sa.String(length=500), nullable=True),
        sa.Column('token_url', sa.String(length=500), nullable=True),
        sa.Column('userinfo_url', sa.String(length=500), nullable=True),
        sa.Column('scope', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sso_providers_id'), 'sso_providers', ['id'], unique=False)
    op.create_index(op.f('ix_sso_providers_name'), 'sso_providers', ['name'], unique=True)

    # Create sso_users table
    op.create_table('sso_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=False),
        sa.Column('external_user_id', sa.String(length=255), nullable=False),
        sa.Column('external_email', sa.String(length=255), nullable=True),
        sa.Column('external_name', sa.String(length=200), nullable=True),
        sa.Column('external_groups', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('external_attributes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_sso_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sso_session_id', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['provider_id'], ['sso_providers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sso_users_id'), 'sso_users', ['id'], unique=False)
    op.create_index(op.f('ix_sso_users_user_id'), 'sso_users', ['user_id'], unique=False)
    op.create_index(op.f('ix_sso_users_provider_id'), 'sso_users', ['provider_id'], unique=False)
    op.create_index(op.f('ix_sso_users_external_user_id'), 'sso_users', ['external_user_id'], unique=False)
    
    # Create unique constraint on provider_id + external_user_id
    op.create_unique_constraint(
        'uq_sso_users_provider_external', 
        'sso_users', 
        ['provider_id', 'external_user_id']
    )

    # Create sso_sessions table
    op.create_table('sso_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('sso_session_index', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider_id', sa.Integer(), nullable=False),
        sa.Column('login_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('session_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('logout_reason', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['provider_id'], ['sso_providers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sso_sessions_id'), 'sso_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_sso_sessions_session_id'), 'sso_sessions', ['session_id'], unique=True)
    op.create_index(op.f('ix_sso_sessions_user_id'), 'sso_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_sso_sessions_provider_id'), 'sso_sessions', ['provider_id'], unique=False)
    op.create_index(op.f('ix_sso_sessions_active'), 'sso_sessions', ['active'], unique=False)

    # Add is_sso_user column to users table if it doesn't exist
    try:
        op.add_column('users', sa.Column('is_sso_user', sa.Boolean(), nullable=False, default=False))
    except Exception:
        # Column might already exist
        pass

    # Insert default SSO providers
    op.execute("""
        INSERT INTO sso_providers (name, provider_type, enabled, config, client_id, authorization_url, token_url, userinfo_url, scope)
        VALUES 
        ('Google OAuth', 'oauth_google', true, '{}', '', 'https://accounts.google.com/o/oauth2/auth', 'https://oauth2.googleapis.com/token', 'https://www.googleapis.com/oauth2/v2/userinfo', 'openid email profile'),
        ('Microsoft OAuth', 'oauth_microsoft', true, '{}', '', 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize', 'https://login.microsoftonline.com/common/oauth2/v2.0/token', 'https://graph.microsoft.com/v1.0/me', 'openid email profile'),
        ('GitHub OAuth', 'oauth_github', true, '{}', '', 'https://github.com/login/oauth/authorize', 'https://github.com/login/oauth/access_token', 'https://api.github.com/user', 'user:email')
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('sso_sessions')
    op.drop_table('sso_users')
    op.drop_table('sso_providers')
    
    # Remove is_sso_user column from users table
    try:
        op.drop_column('users', 'is_sso_user')
    except Exception:
        # Column might not exist
        pass 