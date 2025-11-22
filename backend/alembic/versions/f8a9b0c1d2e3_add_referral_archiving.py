"""add_referral_archiving

Revision ID: f8a9b0c1d2e3
Revises: e7a1b2c3d4f5
Create Date: 2025-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f8a9b0c1d2e3'
down_revision = 'e7a1b2c3d4f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add archived and archived_at columns to referrals table
    op.add_column('referrals', sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('referrals', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create index on archived for better query performance
    op.create_index('ix_referrals_archived', 'referrals', ['archived'])


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_referrals_archived', table_name='referrals')
    
    # Drop columns
    op.drop_column('referrals', 'archived_at')
    op.drop_column('referrals', 'archived')

