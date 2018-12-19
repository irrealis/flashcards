"""Create initial tables

Revision ID: ab13826fb264
Revises: 
Create Date: 2018-12-18 14:42:44.586982

"""
from alembic import op
import sqlalchemy as sa

import enum


# revision identifiers, used by Alembic.
revision = 'ab13826fb264'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
	op.create_table('vocabs',
	  sa.Column('id', sa.Integer, primary_key = True, autoincrement = False),
	  sa.Column('description', sa.Text),
	)
	
	op.create_table('words',
	  sa.Column('id', sa.Integer, primary_key = True),
	  sa.Column('word', sa.Text),
	  sa.Column('short_blurb', sa.Text),
	  sa.Column('long_blurb', sa.Text),
	  sa.Column('frequency', sa.Float)
	)
	
	op.create_table('vocab_words',
	  sa.Column('vocab_id', sa.Integer, sa.ForeignKey('vocabs.id'), primary_key = True),
	  sa.Column('word_id', sa.Integer, sa.ForeignKey('words.id'), primary_key = True),
	)
	
	op.create_table('senses',
	  sa.Column('id', sa.Integer, primary_key = True),
	  sa.Column('sense', sa.Text),
	)
	
	op.create_table('sense_words',
	  sa.Column('sense_id', sa.Integer, sa.ForeignKey('senses.id'), primary_key = True),
	  sa.Column('word_id', sa.Integer, sa.ForeignKey('words.id'), primary_key = True),
	)
	
	class SenseRelationKind(enum.Enum):
	  synonym = 1
	  antonym = 2
	  type_of = 3
	
	op.create_table('sense_relations',
	  sa.Column('l_sense_id', sa.Integer, sa.ForeignKey('senses.id'), primary_key = True),
	  sa.Column('r_sense_id', sa.Integer, sa.ForeignKey('senses.id'), primary_key = True),
	  sa.Column('relation_kind', sa.Enum(SenseRelationKind)),
	)


def downgrade():
	op.drop_table('vocabs')
	op.drop_table('words')
	op.drop_table('vocab_words')
	op.drop_table('senses')
	op.drop_table('sense_words')
	op.drop_table('sense_relations')
