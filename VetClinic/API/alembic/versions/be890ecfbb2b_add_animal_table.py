"""Add animal table

Revision ID: be890ecfbb2b
Revises: 2217e9041918
Create Date: 2025-04-11 17:50:35.398538

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'be890ecfbb2b'
down_revision: Union[str, None] = '2217e9041918'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create animals table if it does not already exist."""

    bind = op.get_bind()
    inspector = inspect(bind)

    if "animals" in inspector.get_table_names():
        return

    op.create_table(
        "animals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("species", sa.String(), nullable=False),
        sa.Column("breed", sa.String(), nullable=True),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("microchip_number", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["clients.id"]),
        sa.UniqueConstraint("microchip_number"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("animals")
