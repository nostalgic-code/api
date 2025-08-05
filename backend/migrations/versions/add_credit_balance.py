"""Add credit_limit and balance fields to customer

Revision ID: add_credit_balance
Revises: 
Create Date: 2024-01-08

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('customer', sa.Column('credit_limit', sa.Numeric(10, 2), nullable=True))
    op.add_column('customer', sa.Column('balance', sa.Numeric(10, 2), nullable=True))

def downgrade():
    op.drop_column('customer', 'balance')
    op.drop_column('customer', 'credit_limit')
