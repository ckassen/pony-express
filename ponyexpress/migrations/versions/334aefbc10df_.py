"""empty message

Revision ID: 334aefbc10df
Revises: 36b5aaa11324
Create Date: 2014-04-01 16:37:00.017980

"""

# revision identifiers, used by Alembic.
revision = '334aefbc10df'
down_revision = '36b5aaa11324'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('repositories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('uri', sa.String(length=255), nullable=True),
    sa.Column('label', sa.String(length=255), nullable=True),
    sa.Column('provider', sa.String(length=12), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('repohistory',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('repo_id', sa.Integer(), nullable=True),
    sa.Column('pkgsha', sa.String(length=255), nullable=True),
    sa.Column('pkgname', sa.String(length=255), nullable=True),
    sa.Column('pkgversion', sa.String(length=64), nullable=True),
    sa.Column('pkgsource', sa.Text(), nullable=True),
    sa.Column('released', sa.DATE(), nullable=True),
    sa.ForeignKeyConstraint(['repo_id'], ['repositories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('repohistory')
    op.drop_table('repositories')
    ### end Alembic commands ###
