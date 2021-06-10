"""empty message

Revision ID: 2235243aadff
Revises: bb4564f390bf
Create Date: 2021-05-17 18:57:47.099306

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2235243aadff'
down_revision = 'bb4564f390bf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('User', sa.Column('last_rained', sa.String(32), nullable=True))
    op.add_column('User', sa.Column('last_watered', sa.String(32), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('User', 'last_watered')
    op.drop_column('User', 'last_rained')
    # ### end Alembic commands ###
