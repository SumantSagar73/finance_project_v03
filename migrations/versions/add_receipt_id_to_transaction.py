"""Add receipt_id to Transaction model

Revision ID: add_receipt_id_to_transaction
Revises: 
Create Date: 2024-04-15 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_receipt_id_to_transaction'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
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
    
    # Copy data from old table to new table
    op.execute('''
        INSERT INTO transaction_new (id, amount, description, category, type, date, user_id, created_at)
        SELECT id, amount, description, category, type, date, user_id, created_at
        FROM transaction
    ''')
    
    # Drop old table
    op.drop_table('transaction')
    
    # Rename new table to original name
    op.rename_table('transaction_new', 'transaction')


def downgrade():
    # Create new table without receipt_id
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
    
    # Copy data from current table to old table
    op.execute('''
        INSERT INTO transaction_old (id, amount, description, category, type, date, user_id, created_at)
        SELECT id, amount, description, category, type, date, user_id, created_at
        FROM transaction
    ''')
    
    # Drop current table
    op.drop_table('transaction')
    
    # Rename old table to original name
    op.rename_table('transaction_old', 'transaction') 