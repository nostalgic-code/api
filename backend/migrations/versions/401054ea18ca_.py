"""empty message

Revision ID: 401054ea18ca
Revises: 
Create Date: 2025-06-23 10:22:38.367430

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '401054ea18ca'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('customer_user_otps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone', sa.String(length=15), nullable=False),
    sa.Column('otp_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('customer_user_otps', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_customer_user_otps_expires_at'), ['expires_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_customer_user_otps_phone'), ['phone'], unique=False)

    op.create_table('platform_users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.Column('role', sa.Enum('admin', 'support', 'developer', name='platformuserrole'), nullable=False),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('platform_users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_platform_users_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_platform_users_phone'), ['phone'], unique=True)

    op.drop_table('carts')
    op.drop_table('cart_items')
    with op.batch_alter_table('user_otps', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_otps_expires_at'))
        batch_op.drop_index(batch_op.f('ix_user_otps_phone'))

    op.drop_table('user_otps')
    with op.batch_alter_table('admin_users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('email'))

    op.drop_table('admin_users')
    with op.batch_alter_table('customer_users', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
        batch_op.alter_column('customer_id',
               existing_type=mysql.INTEGER(),
               nullable=False)
        batch_op.drop_index(batch_op.f('email'))
        batch_op.create_index(batch_op.f('ix_customer_users_customer_id'), ['customer_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_customer_users_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_customer_users_phone'), ['phone'], unique=True)
        batch_op.create_index(batch_op.f('ix_customer_users_role'), ['role'], unique=False)
        batch_op.create_index(batch_op.f('ix_customer_users_status'), ['status'], unique=False)
        batch_op.create_foreign_key(None, 'permission_codes', ['permission_code'], ['code'])

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.alter_column('type',
               existing_type=mysql.ENUM('individual', 'company'),
               nullable=False,
               existing_server_default=sa.text("'individual'"))
        batch_op.alter_column('status',
               existing_type=mysql.ENUM('pending', 'approved', 'on_hold', 'rejected'),
               nullable=False,
               existing_server_default=sa.text("'pending'"))
        batch_op.alter_column('created_at',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
        batch_op.alter_column('updated_at',
               existing_type=mysql.DATETIME(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
        batch_op.drop_index(batch_op.f('customer_code'))
        batch_op.create_index(batch_op.f('ix_customers_account_number'), ['account_number'], unique=False)
        batch_op.create_index(batch_op.f('ix_customers_customer_code'), ['customer_code'], unique=True)
        batch_op.create_index(batch_op.f('ix_customers_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_customers_status'), ['status'], unique=False)
        batch_op.drop_column('credit_limit')
        batch_op.drop_column('balance')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('idx_branch_code'))
        batch_op.drop_index(batch_op.f('idx_brand'))
        batch_op.drop_index(batch_op.f('idx_category'))
        batch_op.drop_index(batch_op.f('idx_current_price'))
        batch_op.drop_index(batch_op.f('idx_data_hash'))
        batch_op.drop_index(batch_op.f('idx_is_available'))
        batch_op.drop_index(batch_op.f('idx_product_code'))
        batch_op.drop_index(batch_op.f('product_code'))
        batch_op.create_index(batch_op.f('ix_products_branch_code'), ['branch_code'], unique=False)
        batch_op.create_index(batch_op.f('ix_products_brand'), ['brand'], unique=False)
        batch_op.create_index(batch_op.f('ix_products_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_products_current_price'), ['current_price'], unique=False)
        batch_op.create_index(batch_op.f('ix_products_data_hash'), ['data_hash'], unique=False)
        batch_op.create_index(batch_op.f('ix_products_is_available'), ['is_available'], unique=False)
        batch_op.create_index(batch_op.f('ix_products_product_code'), ['product_code'], unique=True)
        batch_op.drop_column('status')

    with op.batch_alter_table('user_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_type', sa.String(length=20), nullable=False))
        batch_op.drop_index(batch_op.f('idx_user'))
        batch_op.drop_index(batch_op.f('session_token'))
        batch_op.create_index('idx_user_session_lookup', ['user_id', 'user_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_sessions_expires_at'), ['expires_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_sessions_session_token'), ['session_token'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_sessions_user_id'), ['user_id'], unique=False)
        batch_op.drop_constraint(batch_op.f('user_sessions_ibfk_1'), type_='foreignkey')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_sessions', schema=None) as batch_op:
        batch_op.create_foreign_key(batch_op.f('user_sessions_ibfk_1'), 'admin_users', ['user_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_index(batch_op.f('ix_user_sessions_user_id'))
        batch_op.drop_index(batch_op.f('ix_user_sessions_session_token'))
        batch_op.drop_index(batch_op.f('ix_user_sessions_expires_at'))
        batch_op.drop_index('idx_user_session_lookup')
        batch_op.create_index(batch_op.f('session_token'), ['session_token'], unique=True)
        batch_op.create_index(batch_op.f('idx_user'), ['user_id'], unique=False)
        batch_op.drop_column('user_type')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', mysql.ENUM('available', 'on_hold'), server_default=sa.text("'available'"), nullable=False))
        batch_op.drop_index(batch_op.f('ix_products_product_code'))
        batch_op.drop_index(batch_op.f('ix_products_is_available'))
        batch_op.drop_index(batch_op.f('ix_products_data_hash'))
        batch_op.drop_index(batch_op.f('ix_products_current_price'))
        batch_op.drop_index(batch_op.f('ix_products_category'))
        batch_op.drop_index(batch_op.f('ix_products_brand'))
        batch_op.drop_index(batch_op.f('ix_products_branch_code'))
        batch_op.create_index(batch_op.f('product_code'), ['product_code'], unique=True)
        batch_op.create_index(batch_op.f('idx_product_code'), ['product_code'], unique=False)
        batch_op.create_index(batch_op.f('idx_is_available'), ['is_available'], unique=False)
        batch_op.create_index(batch_op.f('idx_data_hash'), ['data_hash'], unique=False)
        batch_op.create_index(batch_op.f('idx_current_price'), ['current_price'], unique=False)
        batch_op.create_index(batch_op.f('idx_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('idx_brand'), ['brand'], unique=False)
        batch_op.create_index(batch_op.f('idx_branch_code'), ['branch_code'], unique=False)

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('balance', mysql.DECIMAL(precision=15, scale=2), nullable=True))
        batch_op.add_column(sa.Column('credit_limit', mysql.DECIMAL(precision=15, scale=2), nullable=True))
        batch_op.drop_index(batch_op.f('ix_customers_status'))
        batch_op.drop_index(batch_op.f('ix_customers_name'))
        batch_op.drop_index(batch_op.f('ix_customers_customer_code'))
        batch_op.drop_index(batch_op.f('ix_customers_account_number'))
        batch_op.create_index(batch_op.f('customer_code'), ['customer_code'], unique=True)
        batch_op.alter_column('updated_at',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
        batch_op.alter_column('created_at',
               existing_type=mysql.DATETIME(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
        batch_op.alter_column('status',
               existing_type=mysql.ENUM('pending', 'approved', 'on_hold', 'rejected'),
               nullable=True,
               existing_server_default=sa.text("'pending'"))
        batch_op.alter_column('type',
               existing_type=mysql.ENUM('individual', 'company'),
               nullable=True,
               existing_server_default=sa.text("'individual'"))

    with op.batch_alter_table('customer_users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_customer_users_status'))
        batch_op.drop_index(batch_op.f('ix_customer_users_role'))
        batch_op.drop_index(batch_op.f('ix_customer_users_phone'))
        batch_op.drop_index(batch_op.f('ix_customer_users_email'))
        batch_op.drop_index(batch_op.f('ix_customer_users_customer_id'))
        batch_op.create_index(batch_op.f('email'), ['email'], unique=True)
        batch_op.alter_column('customer_id',
               existing_type=mysql.INTEGER(),
               nullable=True)
        batch_op.alter_column('name',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)

    op.create_table('admin_users',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('email', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('password', mysql.VARCHAR(length=255), nullable=False),
    sa.Column('confirm_password', mysql.VARCHAR(length=255), nullable=True),
    sa.Column('customer_code', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('phone', mysql.VARCHAR(length=20), nullable=True),
    sa.Column('role', mysql.ENUM('admin', 'customer', 'staff', 'buyer'), server_default=sa.text("'customer'"), nullable=True),
    sa.Column('created_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    sa.Column('status', mysql.ENUM('pending', 'approved', 'rejected'), server_default=sa.text("'pending'"), nullable=True),
    sa.Column('updated_at', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True),
    sa.Column('last_login', mysql.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('admin_users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('email'), ['email'], unique=True)

    op.create_table('user_otps',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('phone', mysql.VARCHAR(length=15), nullable=False),
    sa.Column('otp_hash', mysql.VARCHAR(length=64), nullable=False),
    sa.Column('expires_at', mysql.DATETIME(), nullable=False),
    sa.Column('attempts', mysql.INTEGER(), server_default=sa.text("'0'"), autoincrement=False, nullable=True),
    sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('user_otps', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_otps_phone'), ['phone'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_otps_expires_at'), ['expires_at'], unique=False)

    op.create_table('cart_items',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('cart_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('product_code', mysql.VARCHAR(length=100), nullable=False),
    sa.Column('product_name', mysql.VARCHAR(length=255), nullable=True),
    sa.Column('quantity', mysql.INTEGER(), server_default=sa.text("'1'"), autoincrement=False, nullable=True),
    sa.Column('price', mysql.DECIMAL(precision=10, scale=2), nullable=True),
    sa.Column('depot_code', mysql.VARCHAR(length=10), nullable=True),
    sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], name=op.f('cart_items_ibfk_1')),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_table('carts',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('customer_user_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('status', mysql.ENUM('active', 'submitted', 'saved'), server_default=sa.text("'active'"), nullable=True),
    sa.Column('created_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    sa.Column('updated_at', mysql.DATETIME(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True),
    sa.ForeignKeyConstraint(['customer_user_id'], ['customer_users.id'], name=op.f('carts_ibfk_1')),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('platform_users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_platform_users_phone'))
        batch_op.drop_index(batch_op.f('ix_platform_users_email'))

    op.drop_table('platform_users')
    with op.batch_alter_table('customer_user_otps', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_customer_user_otps_phone'))
        batch_op.drop_index(batch_op.f('ix_customer_user_otps_expires_at'))

    op.drop_table('customer_user_otps')
    # ### end Alembic commands ###
