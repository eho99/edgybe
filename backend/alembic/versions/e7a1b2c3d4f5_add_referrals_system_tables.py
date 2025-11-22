"""add_referrals_system_tables

Revision ID: e7a1b2c3d4f5
Revises: cb4c5726f2f1
Create Date: 2025-01-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7a1b2c3d4f5'
down_revision = 'cb4c5726f2f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('time_of_day', sa.String(), nullable=True),
        sa.Column('behaviors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create interventions table
    op.create_table(
        'interventions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('referral_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('referrals.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create communication_logs table
    op.create_table(
        'communication_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('referral_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('referrals.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('communication_type', sa.String(), nullable=False),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('subject_template', sa.String(), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('scope', sa.String(), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    
    # Create indexes for better query performance
    op.create_index('ix_referrals_status', 'referrals', ['status'])
    op.create_index('ix_referrals_type', 'referrals', ['type'])
    op.create_index('ix_referrals_created_at', 'referrals', ['created_at'])
    op.create_index('ix_interventions_status', 'interventions', ['status'])
    op.create_index('ix_email_templates_type', 'email_templates', ['type'])
    op.create_index('ix_email_templates_scope', 'email_templates', ['scope'])
    op.create_index('ix_email_templates_is_active', 'email_templates', ['is_active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_email_templates_is_active', table_name='email_templates')
    op.drop_index('ix_email_templates_scope', table_name='email_templates')
    op.drop_index('ix_email_templates_type', table_name='email_templates')
    op.drop_index('ix_interventions_status', table_name='interventions')
    op.drop_index('ix_referrals_created_at', table_name='referrals')
    op.drop_index('ix_referrals_type', table_name='referrals')
    op.drop_index('ix_referrals_status', table_name='referrals')
    
    # Drop tables (in reverse order due to foreign keys)
    op.drop_table('email_templates')
    op.drop_table('communication_logs')
    op.drop_table('interventions')
    op.drop_table('referrals')

