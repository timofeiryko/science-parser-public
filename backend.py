"""Functions, which help to work with DB, live here.
These functions are separated from the other layers and can be used with different frontends or parsers."""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

import logging
from flag import flag

from configs import DB_FILENAME, SUPPORTED_LANGS
from db_map import ClinicalTrial, User, Paper, Topic, Base, Location
from parsers.clinical_trials_parser import ReadyClinicalTrial

# TODO: convert funcs into async funcs

DB_SETTING = f'sqlite:///{DB_FILENAME}'
backend_logger = logging.getLogger('backend')


def init():
    engine = create_engine(DB_SETTING, echo = True)
    Base.metadata.create_all(engine)

def connect():
    engine = create_engine(DB_SETTING, echo = False)
    Session = sessionmaker()
    Session.configure(bind=engine)
    return Session()

def select_user(tg_id, session = connect()):

    user = session.query(User).filter(User.tg_id == tg_id).first()

    if not user:
        # get name from aiogram using tg_id
        user = User(tg_id=tg_id)
        session.add(user)
        session.commit()

    return user

def check_paper(link, session = connect()):
    return bool(session.query(Paper).filter(Paper.link == link).first())

def add_paper(link, title, content_md, source, session = connect()):

    backend_logger.info('NEW PAPER!')
    backend_logger.info(f'ADDING NEW PAPER: {link}')

    paper = Paper(link=link, title=title, content_md=content_md, source=source)
    session.add(paper)
    session.commit()
    
    backend_logger.info(f'PAPER SAVED: {paper.link}')

    return paper

def select_location(name: str, city: str, country: str, session = connect()):

    # search location with given name, city and country
    location = session.query(Location).filter(Location.name == name, Location.city == city, Location.country == country).first()

    # if location doesn't exist, create it
    if not location:
        location = Location(name=name, city=city, country=country)
        session.add(location)
        session.commit()

    return location

def check_trial(link, session = connect()):
    return bool(session.query(ClinicalTrial).filter(ClinicalTrial.link == link).first())

def add_trial(ready_trial: ReadyClinicalTrial, session = connect()):

    trial = ClinicalTrial(
        nctt_id = ready_trial.nctt_id,
        link = ready_trial.link,
        title = ready_trial.title,
        description = ready_trial.description,
        recruitment_status = ready_trial.recruitment_status,
        completion_date = ready_trial.completion_date,
        criteria = ready_trial.criteria
    )

    for location in ready_trial.locations:
        location = select_location(location.name, location.city, location.country, session)
        trial.locations.append(location)
        session.add(trial, location)
        session.commit()

    return trial


def select_topic(user, topic_text, session = connect()):

    topic = session.query(Topic).filter(Topic.text == topic_text).first()

    if not topic:
        topic = Topic(text=topic_text)

    user.topics.append(topic)
    session.add(user, topic)
    session.commit()

    return topic

def check_save_lang(user, message, session = connect()):
    """Returns True if language was saved, False if it's not supported"""

    supported_options = {}
    for unicode, lang in SUPPORTED_LANGS.items():

        lang_code = 'gb' if unicode == 'en' else unicode
        supported_options[f'{flag(lang_code)} {lang}'] = unicode

    if message.text in supported_options.keys():
        user.lang = supported_options[message.text]
        session.add(user)
        session.commit()
        return True
    else:
        return False

def drop_topic(user, topic_text, session = connect()):
    topic = session.query(Topic).filter(Topic.text == topic_text).first()
    user.topics.remove(topic)
    session.add(user)
    session.commit()