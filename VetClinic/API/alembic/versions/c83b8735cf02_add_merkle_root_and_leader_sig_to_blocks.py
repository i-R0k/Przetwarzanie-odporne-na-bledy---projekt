"""add merkle_root and leader_sig to blocks

Revision ID: c83b8735cf02
Revises: a69c226e2577
Create Date: 2025-12-11 20:57:48.438624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c83b8735cf02'
down_revision: Union[str, None] = 'a69c226e2577'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema in a sposób, który nie zabija SQLite i nie kasuje danych."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_table(name: str) -> bool:
        return name in inspector.get_table_names()

    def has_column(table: str, col: str) -> bool:
        cols = [c["name"] for c in inspector.get_columns(table)]
        return col in cols

    # 1. invoices – jeśli istnieje, wywalamy (tak jak chciała migracja)
    if has_table("invoices"):
        try:
            op.drop_index("ix_invoices_client_id", table_name="invoices")
        except Exception:
            pass
        try:
            op.drop_index("ix_invoices_id", table_name="invoices")
        except Exception:
            pass
        op.drop_table("invoices")

    # 2. blocks: merkle_root i leader_sig – dodaj TYLKO jeśli brak
    if has_table("blocks"):
        if not has_column("blocks", "merkle_root"):
            op.add_column(
                "blocks",
                sa.Column("merkle_root", sa.String(length=128), nullable=True)
            )
        if not has_column("blocks", "leader_sig"):
            op.add_column(
                "blocks",
                sa.Column("leader_sig", sa.Text(), nullable=True)
            )

    # 3. clients.wallet_address – tylko UNIQUE, BEZ ALTER COLUMN
    if has_table("clients") and has_column("clients", "wallet_address"):
        try:
            existing_ucs = [
                c["name"] for c in inspector.get_unique_constraints("clients")
                if c.get("name")
            ]
        except Exception:
            existing_ucs = []

        if "uq_clients_wallet_address" not in existing_ucs:
            try:
                op.create_unique_constraint(
                    "uq_clients_wallet_address",
                    "clients",
                    ["wallet_address"],
                )
            except Exception:
                pass

    # 4. transactions – nowe pola blockchainowe
    if has_table("transactions"):

        if not has_column("transactions", "tx_id"):
            op.add_column(
                "transactions",
                sa.Column("tx_id", sa.String(length=128), nullable=True)
            )
            try:
                op.create_unique_constraint(
                    "uq_transactions_tx_id",
                    "transactions",
                    ["tx_id"],
                )
            except Exception:
                pass

        if not has_column("transactions", "payload"):
            op.add_column(
                "transactions",
                sa.Column("payload", sa.Text(), nullable=True)
            )

        if not has_column("transactions", "sender_pub"):
            op.add_column(
                "transactions",
                sa.Column("sender_pub", sa.String(length=256), nullable=True)
            )

        if not has_column("transactions", "signature"):
            op.add_column(
                "transactions",
                sa.Column("signature", sa.Text(), nullable=True)
            )

        # stare kolumny – usuwamy tylko jeśli jeszcze są
        for col in ("amount", "recipient", "sender"):
            if has_column("transactions", col):
                op.drop_column("transactions", col)


def downgrade() -> None:
    """Downgrade schema – cofnięcie zmian blockchainowych."""

    op.add_column(
        "transactions",
        sa.Column("sender", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("recipient", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("amount", sa.Float(), nullable=True),
    )

    op.drop_column("transactions", "signature")
    op.drop_column("transactions", "sender_pub")
    op.drop_column("transactions", "payload")
    op.drop_column("transactions", "tx_id")

    op.drop_column("blocks", "leader_sig")
    op.drop_column("blocks", "merkle_root")
