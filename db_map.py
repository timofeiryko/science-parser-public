from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from dataclasses import dataclass, field
from typing import List

Base = declarative_base()

class Paper(Base):

    __tablename__ = 'paper'

    id = Column(Integer, primary_key=True)
    link = Column(String)
    title = Column(String)
    content_md = Column(String)
    source = Column(String)

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return f'PAPER {self.title}, {self.link}'

class Topic(Base):

    __tablename__ = 'topic'

    id = Column(Integer, primary_key=True)
    text = Column(String)

    def __repr__(self):
        return str(self.__dict__)

paper_user_table = Table(
    'paper_user_association', Base.metadata,
    Column('paper_id', ForeignKey('paper.id')),
    Column('user_id', ForeignKey('user.id'))
)

topic_user_table = Table(
    'topic_user_association', Base.metadata,
    Column('topic_id', ForeignKey('topic.id')),
    Column('user_id', ForeignKey('user.id'))
)

class Location(Base):

    __tablename__ = 'location'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String)
    country = Column(String)

location_clinical_trial_table = Table(
    'location_clinical_trial_association', Base.metadata,
    Column('location_id', ForeignKey('location.id')),
    Column('clinical_trial_id', ForeignKey('clinical_trial.id'))
)

class ClinicalTrial(Base):

    __tablename__ = 'clinical_trial'

    id = Column(Integer, primary_key=True)
    nctt_id = Column(String)
    link = Column(String)
    title = Column(String)
    description = Column(String)
    recruitment_status = Column(String)

    completion_date = Column(String)
    criteria = Column(String)

    locations = relationship('Location', secondary=location_clinical_trial_table, backref='clinical_trials')

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return f'CLINICAL TRIAL {self.link}'

trial_user_table = Table(
    'trial_user_association', Base.metadata,
    Column('trial_id', ForeignKey('clinical_trial.id')),
    Column('user_id', ForeignKey('user.id'))
)

class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    tg_id = Column(String)
    name = Column(String)
    lang = Column(String)

    topics = relationship('Topic', secondary=topic_user_table, backref='users', )
    sent_papers = relationship('Paper', secondary=paper_user_table, backref='users')
    sent_trials = relationship('ClinicalTrial', secondary=trial_user_table, backref='users')

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return f'USER {self.name}, {self.tg_id}'