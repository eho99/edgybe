"""merge heads

Revision ID: 787484ac7dd3
Revises: a65e0c138a39, f8a9b0c1d2e3
Create Date: 2025-11-23 23:12:48.563361

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '787484ac7dd3'
down_revision = ('a65e0c138a39', 'f8a9b0c1d2e3')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
