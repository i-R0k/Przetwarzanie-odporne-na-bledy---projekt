# alembic/versions/e2e464860f55_docs_and_clients.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'e2e464860f55'
down_revision = 'b1cf6ca335b5'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add login safety fields to clients and doctors without batch operations."""

    bind = op.get_bind()
    inspector = inspect(bind)

    for table in ("clients", "doctors"):
        columns = [col["name"] for col in inspector.get_columns(table)]

        if "backup_email" not in columns:
            op.add_column(
                table,
                sa.Column(
                    "backup_email",
                    sa.String(length=255),
                    nullable=True,
                ),
            )

        if "must_change_password" not in columns:
            op.add_column(
                table,
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

    for table in ("doctors", "clients"):
        columns = [col["name"] for col in inspector.get_columns(table)]

        if "must_change_password" in columns:
            op.drop_column(table, "must_change_password")
        if "backup_email" in columns:
            op.drop_column(table, "backup_email")
