"""Add task-complete columns

Revision ID: f51adb7c4d0d
Revises: ab13826fb264
Create Date: 2018-12-18 14:53:56.340697

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f51adb7c4d0d'
down_revision = 'ab13826fb264'
branch_labels = None
depends_on = None


def upgrade():
  op.add_column('vocabs', sa.Column('is_task_complete', sa.Text))
  op.add_column('words', sa.Column('is_task_complete', sa.Text))


def downgrade():
  op.drop_column('vocabs', 'is_task_complete')
  op.drop_column('words', 'is_task_complete')
