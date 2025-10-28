"""Fix OrgRole enum values

Revision ID: a0f6097c8f6f
Revises: 90c0d19774ad
Create Date: 2025-10-27 21:15:16.950710

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0f6097c8f6f'
down_revision = '90c0d19774ad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, convert the role column to text temporarily
    op.execute("ALTER TABLE organization_members ALTER COLUMN role TYPE text")
    
    # Update any existing data to match new enum values
    op.execute("UPDATE organization_members SET role = 'staff' WHERE role = 'member'")
    op.execute("UPDATE organization_members SET role = 'staff' WHERE role = 'viewer'")
    
    # Drop and recreate the OrgRole enum with correct values
    op.execute("DROP TYPE IF EXISTS orgrole CASCADE")
    op.execute("CREATE TYPE orgrole AS ENUM ('admin', 'secretary', 'staff', 'guardian', 'student')")
    
    # Update the organization_members table to use the new enum
    op.execute("ALTER TABLE organization_members ALTER COLUMN role TYPE orgrole USING role::orgrole")


def downgrade() -> None:
    # Revert to text type
    op.execute("ALTER TABLE organization_members ALTER COLUMN role TYPE text")
    op.execute("DROP TYPE IF EXISTS orgrole")
