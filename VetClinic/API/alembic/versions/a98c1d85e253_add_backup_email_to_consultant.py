"""add_backup_email_and_must_change_password_to_consultant

Revision ID: a98c1d85e253
Revises: 96cf1625b86c
Create Date: 2025-05-17 18:02:42.593631
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'a98c1d85e253'
down_revision = '96cf1625b86c'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Dodanie backup_email i must_change_password do consultants, bez batch_alter_table."""

    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("consultants")]

    if "backup_email" not in columns:
        op.add_column(
            "consultants",
            sa.Column(
                "backup_email",
                sa.String(length=255),
                nullable=True,
            ),
        )

    if "must_change_password" not in columns:
        op.add_column(
            "consultants",
            sa.Column(
                "must_change_password",
                sa.Boolean(),
                nullable=False,
                server_default="0",
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("consultants")]

    if "must_change_password" in columns:
        op.drop_column("consultants", "must_change_password")
    if "backup_email" in columns:
        op.drop_column("consultants", "backup_email")
