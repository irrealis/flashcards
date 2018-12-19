from sqlalchemy import Table, Column, Integer, Float, Numeric, Text, Enum, MetaData, ForeignKey, create_engine

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, relationship

import enum

metadata = MetaData()
Base = automap_base()

# I use this class mainly to simplify pretty-printing database entries.
class Mixin(object):
  def __repr__(self):
    attr_dict = self.__dict__.copy()
    attr_dict.pop("_sa_instance_state", None)
    return self.pprint(**attr_dict)

  def pprint(self, **kw):
    return "<{name}: {kw}>".format(name=self.__class__.__name__, kw=kw)

class Vocab(Mixin, Base):
  '''
  Vocabulary-list object.
  '''
  __tablename__ = 'vocabs'

  def __repr__(self):
    return self.pprint(
      id = self.id,
      description = self.description,
    )

class Word(Mixin, Base):
  '''
  Word/definition object.
  '''
  __tablename__ = 'words'

  def __repr__(self):
    return self.pprint(
      id = self.id,
      word = self.word,
    )


# Helper functions to simplify using SQLALchemy to define sense-sense
# relationship types. This gets tricky, because...
#
# I model these relationships as a graph. Some parts of the graph need to be
# treated as undirected, and others parts need to be treated as directed.
#
# Because the "synonym" relation is symmetric (if A is a synonym of B, then B is
# a synonym of A), the graph representation of the relation is undirected.
#
# Similarly for the "antonym" relation.
#
# The graph representation of the "type-of" relation must be directed, because
# the relationship is not symmetric: if A is a type of B, then words having
# sense A also have sense B, but there may be words of sense B that do not have
# sense A. As a specific example, one sense of 'abdicate' is to give up power,
# which is a type of 'quit'; but one can 'quit' a position that has no power.
#
# Directed graphs are easier to model in SQL than undirected graphs, and both
# are easier to model than a graph with both directed subgraphs and undirected
# subgraphs. So I use some helper functions and methods to simplify things.

def sense_relationship(foreign_key_col, relation_kind):
  '''
  foreign_key_col: either 'l_sense_id' or 'r_sense_id'
  relation_kind: one of 'synonym', 'antonym', or 'type_of'

  This defines a SQLAlchemy join query that finds a sense's right or left
  related senses, where the relation is of kind 'synonym', 'antonym', or
  'type_of'.
  '''
  return relationship(
    'SenseRelation',
    foreign_keys = '[SenseRelation.{foreign_key_col}]'.format(
      foreign_key_col = foreign_key_col,
    ),
    primaryjoin = 'and_(Sense.id == SenseRelation.{foreign_key_col}, SenseRelation.relation_kind == "{relation_kind}")'.format(
      foreign_key_col = foreign_key_col,
      relation_kind = relation_kind,
    )
  )

def right_sense_relationship(relation_kind):
  '''
  relation_kind: one of 'synonym', 'antonym', or 'type_of'

  This defines a SQLAlchemy join query that finds a sense's right related
  senses, where the relation is of kind 'synonym', 'antonym', or 'type_of'.

  Note that 'l_sense_id' is used to find right-related senses. I'm not sure how
  that happened, but whatever, I'll look at fixing it sometime in the future.
  '''
  return sense_relationship(
    foreign_key_col = 'l_sense_id',
    relation_kind = relation_kind,
  )

def left_sense_relationship(relation_kind):
  '''
  relation_kind: one of 'synonym', 'antonym', or 'type_of'

  This defines a SQLAlchemy join query that finds a sense's left related senses,
  where the relation is of kind 'synonym', 'antonym', or 'type_of'.

  Note that 'r_sense_id' is used to find left-related senses. I'm not sure how
  that happened, but whatever, I'll look at fixing it sometime in the future.
  '''
  return sense_relationship(
    foreign_key_col = 'r_sense_id',
    relation_kind = relation_kind,
  )

def lr(l, r):
  '''
  l: a list of left-related sense associations.
  r: a list of right-related sense associations.

  This helper function does four things:
  - It extracts the left sense from each left association.
  - It extracts the right sense from each right association.
  - It combines the resulting left and right senses into one list.
  - It returns the combined list of senses.
  '''
  return [x.left for x in l] + [x.right for x in r]


class Sense(Mixin, Base):
  '''
  Word/definition sense object.

  A word's typically has lots of different definitions, each defining a 'sense'
  of a word. Synonyms, antonyms, specializations, and generalizations are
  related via these definition senses.
  '''
  __tablename__ = 'senses'

  left_synonyms = left_sense_relationship(relation_kind = 'synonym')
  right_synonyms = right_sense_relationship(relation_kind = 'synonym')
  left_antonyms = left_sense_relationship(relation_kind = 'antonym')
  right_antonyms = right_sense_relationship(relation_kind = 'antonym')
  left_types_of = left_sense_relationship(relation_kind = 'type_of')
  right_types_of = right_sense_relationship(relation_kind = 'type_of')

  @property
  def synonyms(self):
    '''
    Returns synonyms senses.
    '''
    return lr(self.left_synonyms, self.right_synonyms)
  @property
  def antonyms(self):
    '''
    Returns antonyms senses.
    '''
    return lr(self.left_antonyms, self.right_antonyms)
  @property
  def types(self):
    '''
    Returns senses that are types of this sense.
    '''
    return [sr.left for sr in self.left_types_of]
  @property
  def type_of(self):
    '''
    Returns the sense of which this sense is a type.

    Ideally there's at most one of these, but I don't try to enforce this.
    '''
    return [sr.right for sr in self.right_types_of]

  def __repr__(self):
    return self.pprint(
      id = self.id,
      sense = self.sense,
    )


  def add_synonym(self, related_sense):
    '''
    Helper method to add related sense to the list of this sense's synonyms.
    '''
    if related_sense not in self.synonyms:
      return SenseRelation(
        left = self,
        right = related_sense,
        relation_kind = 'synonym',
      )

  def add_antonym(self, related_sense):
    '''
    Helper method to add related sense to the list of this sense's antonyms.
    '''
    if related_sense not in self.antonyms:
      return SenseRelation(
        left = self,
        right = related_sense,
        relation_kind = 'antonym',
      )

  def add_type_of(self, related_sense):
    '''
    Helper method to assert that this sense is a type of the related sense.
    '''
    if related_sense not in self.type_of:
      return SenseRelation(
        left = self,
        right = related_sense,
        relation_kind = 'type_of',
      )

  def add_type(self, related_sense):
    '''
    Helper method to add related sense as a type of this sense.
    '''
    if related_sense not in self.types:
      return SenseRelation(
        left = related_sense,
        right = self,
        relation_kind = 'type_of',
      )


class SenseRelation(Mixin, Base):
  '''
  Object encapsulating the kind of a sense-sense relationship.

  The relationship kind is one of 'synonym', 'antonym', or 'type-of'.
  '''
  __tablename__ = 'sense_relations'
  left = relationship(Sense, foreign_keys = "SenseRelation.l_sense_id", backref = 'right')
  right = relationship(Sense, foreign_keys = "SenseRelation.r_sense_id", backref = 'left')
  def __repr__(self):
    return self.pprint(
      kind = self.relation_kind,
      left = self.left,
      right = self.right,
    )


def get_or_create(session, model, **kwargs):
  '''
  Helper function to find or create instance of model, specified by keyword arguments.

  Based on Stack Overflow question "Does SQLAlchemy have an equivalent of
  Django's get_or_create?"
  - https://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create

  This version does not commit changes to the database.
  '''
  instance = session.query(model).filter_by(**kwargs).first()
  if instance:
    return instance
  else:
    instance = model(**kwargs)
    session.add(instance)
    return instance

