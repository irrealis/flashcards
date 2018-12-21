"""Add index to senses table sense column

Revision ID: 64d0fefaaec6
Revises: f51adb7c4d0d
Create Date: 2018-12-20 17:20:46.597600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64d0fefaaec6'
down_revision = 'f51adb7c4d0d'
branch_labels = None
depends_on = None


def upgrade():
  op.create_index(op.f('ix_senses_sense'), 'senses', ['sense'])


def downgrade():
  op.drop_index('ix_senses_sense', table_name = 'senses')
