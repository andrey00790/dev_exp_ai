"""Add VK OAuth fields to users table

Revision ID: 006
Revises: 005
Create Date: 2025-01-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Add VK OAuth fields to users table"""
    # Add new columns for VK OAuth support
    op.add_column('users', sa.Column('first_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('oauth_provider', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('vk_user_id', sa.String(50), nullable=True))
    
    # Make email nullable for OAuth users
    op.alter_column('users', 'email', nullable=True)
    
    # Make hashed_password nullable for OAuth users
    op.alter_column('users', 'hashed_password', nullable=True)
    
    # Add index for vk_user_id
    op.create_index('idx_users_vk_user_id', 'users', ['vk_user_id'])
    
    # Add unique constraint for vk_user_id
    op.create_unique_constraint('uq_users_vk_user_id', 'users', ['vk_user_id'])


def downgrade():
    """Remove VK OAuth fields from users table"""
    # Remove constraints and indexes
    op.drop_constraint('uq_users_vk_user_id', 'users', type_='unique')
    op.drop_index('idx_users_vk_user_id', 'users')
    
    # Make email and hashed_password non-nullable again
    op.alter_column('users', 'email', nullable=False)
    op.alter_column('users', 'hashed_password', nullable=False)
    
    # Remove VK OAuth columns
    op.drop_column('users', 'vk_user_id')
    op.drop_column('users', 'oauth_provider')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name') 