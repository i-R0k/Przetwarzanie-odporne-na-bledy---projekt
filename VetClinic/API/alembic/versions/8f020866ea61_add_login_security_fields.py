"""Add login security fields

Revision ID: 8f020866ea61
Revises: 50409e86bbbb
Create Date: 2025-05-13 10:45:55.533699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '8f020866ea61'
down_revision: Union[str, None] = '50409e86bbbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Dodanie pól bezpieczeństwa logowania do tabeli clients, bez kombinowania z batch_alter_table."""

    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("clients")]

    if "failed_login_attempts" not in columns:
        op.add_column(
            "clients",
            sa.Column(
                "failed_login_attempts",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )

    if "locked_until" not in columns:
        op.add_column(
            "clients",
            sa.Column(
                "locked_until",
                sa.DateTime(),
                nullable=True,
            ),
        )


def downgrade() -> None:
    """Downgrade schema."""

    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("clients")]

    if "locked_until" in columns:
        op.drop_column("clients", "locked_until")
    if "failed_login_attempts" in columns:
        op.drop_column("clients", "failed_login_attempts")
