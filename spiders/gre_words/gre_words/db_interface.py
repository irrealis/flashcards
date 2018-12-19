from sqlalchemy import Table, Column, Integer, Float, Numeric, Text, Enum, MetaData, ForeignKey, create_engine

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, relationship

import enum

metadata = MetaData()
Base = automap_base()

class Mixin(object):
  def __repr__(self):
    attr_dict = self.__dict__.copy()
    attr_dict.pop("_sa_instance_state", None)
    return self.pprint(**attr_dict)

  def pprint(self, **kw):
    return "<{name}: {kw}>".format(name=self.__class__.__name__, kw=kw)


class Vocab(Mixin, Base):
  __tablename__ = 'vocabs'

  def __repr__(self):
    return self.pprint(
      id = self.id,
      description = self.description,
    )

class Word(Mixin, Base):
  __tablename__ = 'words'

  def __repr__(self):
    return self.pprint(
      id = self.id,
      word = self.word,
    )


def sense_relationship(foreign_key_col, relation_kind):
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
  return sense_relationship(
    foreign_key_col = 'l_sense_id',
    relation_kind = relation_kind,
  )

def left_sense_relationship(relation_kind):
  return sense_relationship(
    foreign_key_col = 'r_sense_id',
    relation_kind = relation_kind,
  )

def lr(l, r):
  return [x.left for x in l] + [x.right for x in r]


class Sense(Mixin, Base):
  __tablename__ = 'senses'

  left_synonyms = left_sense_relationship(relation_kind = 'synonym')
  right_synonyms = right_sense_relationship(relation_kind = 'synonym')
  left_antonyms = left_sense_relationship(relation_kind = 'antonym')
  right_antonyms = right_sense_relationship(relation_kind = 'antonym')
  left_types_of = left_sense_relationship(relation_kind = 'type_of')
  right_types_of = right_sense_relationship(relation_kind = 'type_of')

  @property
  def synonyms(self):
    return lr(self.left_synonyms, self.right_synonyms)
  @property
  def antonyms(self):
    return lr(self.left_antonyms, self.right_antonyms)
  @property
  def types(self):
    return [sr.left for sr in self.left_types_of]
  @property
  def type_of(self):
    return [sr.right for sr in self.right_types_of]

  def __repr__(self):
    return self.pprint(
      id = self.id,
      sense = self.sense,
    )


  def add_synonym(self, related_sense):
    if related_sense not in self.synonyms:
      return SenseRelation(
        left = self,
        right = related_sense,
        relation_kind = 'synonym',
      )

  def add_antonym(self, related_sense):
    if related_sense not in self.antonyms:
      return SenseRelation(
        left = self,
        right = related_sense,
        relation_kind = 'antonym',
      )

  def add_type_of(self, related_sense):
    if related_sense not in self.type_of:
      return SenseRelation(
        left = self,
        right = related_sense,
        relation_kind = 'type_of',
      )

  def add_type(self, related_sense):
    if related_sense not in self.types:
      return SenseRelation(
        left = related_sense,
        right = self,
        relation_kind = 'type_of',
      )


class SenseRelation(Mixin, Base):
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
  instance = session.query(model).filter_by(**kwargs).first()
  if instance:
    return instance
  else:
    instance = model(**kwargs)
    session.add(instance)
    #session.commit()
    return instance

