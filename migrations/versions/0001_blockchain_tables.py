"""blockchain tables

Revision ID: 0001_blockchain
Revises:
Create Date: 2025-11-20 18:30:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_blockchain"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "blocks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("index", sa.Integer(), unique=True, nullable=False),
        sa.Column("previous_hash", sa.String(length=128), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("nonce", sa.Integer(), nullable=False),
        sa.Column("hash", sa.String(length=128), nullable=False),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("block_id", sa.Integer(), sa.ForeignKey("blocks.id"), nullable=True),
        sa.Column("sender", sa.String(length=128), nullable=False),
        sa.Column("recipient", sa.String(length=128), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("committed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_transactions_block_id", "transactions", ["block_id"])


def downgrade():
    op.drop_index("ix_transactions_block_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("blocks")
