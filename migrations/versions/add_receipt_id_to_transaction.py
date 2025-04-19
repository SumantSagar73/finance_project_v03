"""Add receipt_id to Transaction model

Revision ID: add_receipt_id_to_transaction
Revises: create_receipt_table
Create Date: 2024-04-15 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


# revision identifiers, used by Alembic.
revision = 'add_receipt_id_to_transaction'
down_revision = 'create_receipt_table'
branch_labels = None
depends_on = None


def upgrade():
    # Drop transaction_new table if it exists from a failed migration
    conn = op.get_bind()
    inspector = reflection.Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    if 'transaction_new' in tables:
        op.drop_table('transaction_new')

    # Get existing columns from transaction table
    existing_columns = [col['name'] for col in inspector.get_columns('transaction')]

    # Create new table with desired schema
    op.create_table('transaction_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('receipt_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['receipt_id'], ['receipt.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Build the INSERT statement based on existing columns
    columns_to_copy = ['id', 'amount', 'description', 'category', 'type', 'date', 'user_id']
    if 'created_at' in existing_columns:
        columns_to_copy.append('created_at')

    columns_str = ', '.join(columns_to_copy)
    select_str = ', '.join(columns_to_copy)
    
    # Copy data from old table to new table
    op.execute(f'''
        INSERT INTO transaction_new ({columns_str})
        SELECT {select_str}
        FROM "transaction"
    ''')
    
    # Drop old table
    op.drop_table('transaction')
    
    # Rename new table to original name
    op.execute('ALTER TABLE transaction_new RENAME TO "transaction"')


def downgrade():
    # Drop transaction_old table if it exists from a failed migration
    conn = op.get_bind()
    inspector = reflection.Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    if 'transaction_old' in tables:
        op.drop_table('transaction_old')

    # Create old table structure
    op.create_table('transaction_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data back to old table
    op.execute('''
        INSERT INTO transaction_old (id, amount, description, category, type, date, user_id, created_at)
        SELECT id, amount, description, category, type, date, user_id, created_at
        FROM "transaction"
    ''')
    
    # Drop new table
    op.drop_table('transaction')
    
    # Rename old table back to original name
    op.execute('ALTER TABLE transaction_old RENAME TO "transaction"') 