"""add districts table

Revision ID: a65e0c138a39
Revises: 21b428c1e57c
Create Date: 2025-11-20 01:11:04.404942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a65e0c138a39"
down_revision = "21b428c1e57c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "districts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("street_number", sa.String(), nullable=True),
        sa.Column("street_address", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("zip_code", sa.String(), nullable=True),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("slug", sa.String(), nullable=True),
        sa.Column("sis_source_id", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_districts_slug"), "districts", ["slug"], unique=True)
    op.create_index(
        op.f("ix_districts_sis_source_id"), "districts", ["sis_source_id"], unique=False
    )

    op.create_index(
        op.f("ix_organizations_district_id"), "organizations", ["district_id"], unique=False
    )
    op.create_foreign_key(
        "organizations_district_id_fkey",
        "organizations",
        "districts",
        ["district_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "organizations_district_id_fkey", "organizations", type_="foreignkey"
    )
    op.drop_index(op.f("ix_organizations_district_id"), table_name="organizations")

    op.drop_index(op.f("ix_districts_sis_source_id"), table_name="districts")
    op.drop_index(op.f("ix_districts_slug"), table_name="districts")
    op.drop_table("districts")
