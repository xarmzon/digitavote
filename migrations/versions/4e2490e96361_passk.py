"""'passk'

Revision ID: 4e2490e96361
Revises: a44d92f0bffa
Create Date: 2020-05-30 11:38:43.591558

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e2490e96361'
down_revision = 'a44d92f0bffa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('gen_passwasord', schema=None) as batch_op:
        batch_op.drop_index('ix_gen_passwasord_id_number')

    op.drop_table('gen_passwasord')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gen_passwasord',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('id_number', sa.VARCHAR(length=50), nullable=True),
    sa.Column('password_hash', sa.VARCHAR(length=180), nullable=True),
    sa.ForeignKeyConstraint(['id_number'], ['voters.id_number'], name='fk_gen_passwasord_id_number_voters'),
    sa.PrimaryKeyConstraint('id', name='pk_gen_passwasord')
    )
    with op.batch_alter_table('gen_passwasord', schema=None) as batch_op:
        batch_op.create_index('ix_gen_passwasord_id_number', ['id_number'], unique=1)

    # ### end Alembic commands ###
