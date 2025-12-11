from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '475b1af14e99'
down_revision = '0d3d0cad1cb9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Upgrade schema: drop legacy invoices, ensure no orphaned temp table,
    add wallet_address to clients, add fee to appointments.
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    tables = inspector.get_table_names()
    if 'invoices' in tables:
        op.drop_table('invoices')

    # Clean up any stray batch-alter temp table from previous failures
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_clients")

    existing_cols = [col['name'] for col in inspector.get_columns('clients')]

    # Add wallet_address to clients if not already present
    if 'wallet_address' not in existing_cols:
        op.add_column(
            'clients',
            sa.Column('wallet_address', sa.String(length=42), nullable=False, server_default='')
        )
        op.create_unique_constraint('uq_clients_wallet_address', 'clients', ['wallet_address'])
        # remove server default now that constraint is in place
        op.alter_column('clients', 'wallet_address', server_default=None)

    # Inspect appointments table for fee column
    appt_cols = [col['name'] for col in inspector.get_columns('appointments')]
    if 'fee' not in appt_cols:
        # Add fee to appointments
        op.add_column(
            'appointments',
            sa.Column('fee', sa.Float(), nullable=False, server_default='0.0')
        )
        op.alter_column('appointments', 'fee', server_default=None)


def downgrade() -> None:
    """
    Downgrade schema: remove fee and wallet_address, recreate legacy invoices.
    """
    # Remove fee from appointments if exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    appt_cols = [col['name'] for col in inspector.get_columns('appointments')]
    if 'fee' in appt_cols:
        op.drop_column('appointments', 'fee')

    # Remove wallet_address from clients if exists
    client_cols = [col['name'] for col in inspector.get_columns('clients')]
    if 'wallet_address' in client_cols:
        op.drop_constraint('uq_clients_wallet_address', 'clients', type_='unique')
        op.drop_column('clients', 'wallet_address')

    # Recreate legacy invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.INTEGER(), primary_key=True, nullable=False),
        sa.Column('client_id', sa.INTEGER(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.VARCHAR(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_invoices_id', 'invoices', ['id'], unique=False)
    op.create_index('ix_invoices_client_id', 'invoices', ['client_id'], unique=False)
