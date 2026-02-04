"""create goods table

Revision ID: 8bb2ff4e20d4
Revises: 6cae83af7a86
Create Date: 2026-02-02 21:36:12.421016

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from geoalchemy2 import Geography

from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '8bb2ff4e20d4'
down_revision: Union[str, Sequence[str], None] = '6cae83af7a86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    op.create_table(
        'goods',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('name', sa.String(150), unique=True, nullable=False),
        sa.Column('description', sa.String(1000)),
        sa.Column('price', sa.Float()),
        sa.Column('images', sa.ARRAY(sa.String(500))),
        sa.Column('location', Geography(geometry_type='POINT', srid=4326)),
        sa.Column('owner_id', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_onupdate=sa.func.now())
    )

    op.create_foreign_key(
        'fk_goods_owner_id_users',
        'goods',
        'users',
        ['owner_id'],
        ['id'],
        ondelete='CASCADE',
        onupdate='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_goods_owner_id_users', 'goods', type_='foreignkey')
    op.drop_table('goods')
    op.execute(text("DROP EXTENSION IF EXISTS postgis CASCADE;"))
