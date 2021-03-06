"""'ad22'

Revision ID: 406878e98cdb
Revises: 0de2273d4f2a
Create Date: 2020-06-06 14:21:31.517770

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '406878e98cdb'
down_revision = '0de2273d4f2a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admins', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=180), nullable=True))
        batch_op.drop_column('password')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admins', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password', sa.VARCHAR(length=180), nullable=False))
        batch_op.drop_column('password_hash')

    # ### end Alembic commands ###
