"""add_search_product_id

Revision ID: 93d6efe3daa8
Revises: 7e63e4387b7d
Create Date: 2026-09-27 14:59:01.667767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93d6efe3daa8'
down_revision: Union[str, None] = '7e63e4387b7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('searches') as batch_op:
        batch_op.add_column(sa.Column('product_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_search_product', 'products', ['product_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('searches') as batch_op:
        batch_op.drop_constraint('fk_search_product', type_='foreignkey')
        batch_op.drop_column('product_id')
    # ### end Alembic commands ###
