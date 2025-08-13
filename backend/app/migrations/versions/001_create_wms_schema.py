"""Create WMS schema and tables

Revision ID: 001
Revises: 
Create Date: 2025-08-13 17:59:40.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'wms') EXEC('CREATE SCHEMA wms')")
    
    op.create_table('warehouse',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('whs_code', sa.String(length=8), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('whs_code'),
        schema='wms'
    )
    
    op.create_table('location',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('whs_code', sa.String(length=8), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('section', sa.String(length=32), nullable=True),
        sa.Column('aisle', sa.String(length=32), nullable=True),
        sa.Column('rack', sa.String(length=32), nullable=True),
        sa.Column('level', sa.String(length=32), nullable=True),
        sa.Column('bin', sa.String(length=32), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=16), nullable=True),
        sa.Column('capacity_qty', sa.Numeric(precision=18, scale=3), nullable=True),
        sa.Column('capacity_uom', sa.String(length=16), nullable=True),
        sa.Column('attributes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['parent_id'], ['wms.location.id'], ),
        sa.ForeignKeyConstraint(['whs_code'], ['wms.warehouse.whs_code'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('whs_code', 'code', name='uq_location'),
        schema='wms'
    )
    
    op.create_table('stock_location',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('whs_code', sa.String(length=8), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=False),
        sa.Column('item_name', sa.String(length=200), nullable=True),
        sa.Column('lot_no', sa.String(length=100), nullable=True),
        sa.Column('qty', sa.Numeric(precision=18, scale=3), nullable=False, default=0),
        sa.Column('uom', sa.String(length=16), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('SYSUTCDATETIME()')),
        sa.ForeignKeyConstraint(['location_id'], ['wms.location.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='wms'
    )
    
    op.create_table('movement',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('type', sa.String(length=24), nullable=False),
        sa.Column('whs_code_from', sa.String(length=8), nullable=True),
        sa.Column('location_id_from', sa.Integer(), nullable=True),
        sa.Column('whs_code_to', sa.String(length=8), nullable=True),
        sa.Column('location_id_to', sa.Integer(), nullable=True),
        sa.Column('item_code', sa.String(length=50), nullable=False),
        sa.Column('lot_no', sa.String(length=100), nullable=True),
        sa.Column('qty', sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column('uom', sa.String(length=16), nullable=True),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('sap_doc_type', sa.String(length=24), nullable=True),
        sa.Column('sap_doc_entry', sa.Integer(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=64), nullable=True),
        sa.Column('created_by', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('SYSUTCDATETIME()')),
        sa.ForeignKeyConstraint(['location_id_from'], ['wms.location.id'], ),
        sa.ForeignKeyConstraint(['location_id_to'], ['wms.location.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='wms'
    )
    
    op.create_table('count_session',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('whs_code', sa.String(length=8), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, default='OPEN'),
        sa.Column('created_by', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('SYSUTCDATETIME()')),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='wms'
    )
    
    op.create_table('count_detail',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.BigInteger(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=False),
        sa.Column('lot_no', sa.String(length=100), nullable=True),
        sa.Column('expected_qty', sa.Numeric(precision=18, scale=3), nullable=False),
        sa.Column('counted_qty', sa.Numeric(precision=18, scale=3), nullable=True),
        sa.Column('adjusted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['location_id'], ['wms.location.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['wms.count_session.id'], ),
        sa.PrimaryKeyConstraint('id'),
        schema='wms'
    )
    
    op.create_table('audit_log',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('ts', sa.DateTime(), nullable=False, server_default=sa.text('SYSUTCDATETIME()')),
        sa.Column('user_name', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='wms'
    )
    
    op.create_index('ix_stock_location_item_whs', 'stock_location', ['item_code', 'whs_code'], schema='wms')
    op.create_index('ix_stock_location_location', 'stock_location', ['location_id'], schema='wms')
    op.create_index('ix_movement_created_at', 'movement', ['created_at'], schema='wms')
    op.create_index('ix_movement_idempotency_key', 'movement', ['idempotency_key'], unique=True, schema='wms')
    op.create_index('ix_location_hierarchy', 'location', ['whs_code', 'section', 'aisle', 'rack', 'level', 'bin'], schema='wms')

def downgrade() -> None:
    op.drop_index('ix_location_hierarchy', table_name='location', schema='wms')
    op.drop_index('ix_movement_idempotency_key', table_name='movement', schema='wms')
    op.drop_index('ix_movement_created_at', table_name='movement', schema='wms')
    op.drop_index('ix_stock_location_location', table_name='stock_location', schema='wms')
    op.drop_index('ix_stock_location_item_whs', table_name='stock_location', schema='wms')
    op.drop_table('audit_log', schema='wms')
    op.drop_table('count_detail', schema='wms')
    op.drop_table('count_session', schema='wms')
    op.drop_table('movement', schema='wms')
    op.drop_table('stock_location', schema='wms')
    op.drop_table('location', schema='wms')
    op.drop_table('warehouse', schema='wms')
    op.execute("DROP SCHEMA wms")
