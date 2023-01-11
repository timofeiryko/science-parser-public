"""Main module to handle all the messages with aiogram."""

import logging
import os

import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from aiogram.utils.markdown import text, bold, code, italic, pre, link
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext


import aioschedule

from emoji import emojize
from flag import flag

from configs import TG_BOT_TOKEN, DB_FILENAME, UPDATE_INTERVAL, TOPIC
from parsers.clinical_trials_parser import get_last_clinical_trials

from parsers.pubmed_parser import get_ready_papers
from parsers.scholar_parser import search_last_review
from parsers.medicalxpress_parser import get_popular_articles

from backend import init, connect, check_paper, add_paper, select_topic, select_user, check_save_lang, drop_topic, add_trial, check_trial
from frontend import get_message, get_review_message, get_settings_message, get_topic_removed_message, get_welcome_message, get_paper_message, get_topic_exists_message, get_trial_message
from frontend import get_lang_keyboard, get_settings_keyboard, get_remove_topic_keyboard
from db_map import User, Paper, ClinicalTrial
from helpers import suggest_spelling, process_query

# States for registration
class RegistrationStates(StatesGroup):
    language = State()
    check_topic = State()
    setings_choice = State()
    change_language = State()
    remove_topic = State()


# Configure logging
logging.basicConfig(level=logging.INFO)
backend_logger = logging.getLogger('backend')

# Initialize bot and dispatcher
bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Initialize database
if not os.path.isfile(DB_FILENAME):
    init()

async def send_paper(user: User, paper: Paper, topic: str, source: str, session, silent=False):

    user.sent_papers.append(paper)
    session.add(user, paper)
    session.commit()

    if not silent:
        try:
            await bot.send_message(user.tg_id, get_paper_message(paper, topic, source), parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            backend_logger.error(e)
            backend_logger.info(f'Paper was not sent:\n{paper.__repr__()}')

async def send_trial(user: User, trial: ClinicalTrial, topic: str, session, silent=False):

    user.sent_trials.append(trial)
    session.add(user, trial)
    session.commit()

    if not silent:
        try:
            await bot.send_message(user.tg_id, get_trial_message(trial, topic), parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            backend_logger.error(e)
            backend_logger.info(f'Trial was not sent:\n{trial.__repr__()}')

# To update papers database regularly
async def update_papers():

    backend_logger.info('Updating papers and clinical trials...')

    session = connect()

    for user in session.query(User).all():

        # get topics for this user
        topics = [topic.text for topic in user.topics]

        for topic in topics:
            
            try:
                ready_papers = get_ready_papers(topic)
            except RuntimeError as e:
                backend_logger.error(e)
                await RegistrationStates.check_topic.set()
                reply = get_message(user, 'wrong_topic')
                suggestion = suggest_spelling(topic)
                if suggestion:
                    reply = text(reply, get_message(user, 'suggestion'), pre(suggestion), sep='\n\n')
                await bot.send_message(user.tg_id, get_message(user, 'wrong_topic'))

            source = 'pubmed'

            for ready_paper in ready_papers:

                link = 'doi.org/' + ready_paper.doi

                if not check_paper(link):
                    paper = add_paper(link, ready_paper.title, ready_paper.abstract, source, session)
                    await send_paper(user, paper, topic, source, session)
                else:
                    backend_logger.info(f'Paper already exists: {link}')
                    paper = session.query(Paper).filter(Paper.link == link).first()
                

                sent_papers = session.query(Paper).\
                    join(User.sent_papers).filter(User.tg_id == user.tg_id).all()

                if paper not in sent_papers:
                    await send_paper(user, paper, topic, source, session)

            # TODO: DRY parsing errors handling
            try:
                popular_articles = get_popular_articles(topic)
            except Exception as e:
                backend_logger.error(e)
                await RegistrationStates.check_topic.set()
                reply = get_message(user, 'wrong_topic')
                suggestion = suggest_spelling(topic)
                if suggestion:
                    reply = text(reply, get_message(user, 'suggestion'), pre(suggestion), sep='\n\n')
                await bot.send_message(user.tg_id, get_message(user, 'wrong_topic'))

            source = 'medicalxpress'

            for pop_article in popular_articles:
                    
                    link = pop_article.link
    
                    if not check_paper(link):
                        paper = add_paper(link, pop_article.title, pop_article.abstract, source, session)
                        await send_paper(user, paper, topic, source, session)
                    else:
                        backend_logger.info(f'Paper already exists: {link}')
                        paper = session.query(Paper).filter(Paper.link == link).first()

                    sent_papers = session.query(Paper).\
                        join(User.sent_papers).filter(User.tg_id == user.tg_id).all()
    
                    if paper not in sent_papers:
                        await send_paper(user, paper, topic, source, session)

            try:
                trials = get_last_clinical_trials(topic)
            except Exception as e:
                backend_logger.error(e)
                await RegistrationStates.check_topic.set()
                reply = get_message(user, 'wrong_topic')
                suggestion = suggest_spelling(topic)
                if suggestion:
                    reply = text(reply, get_message(user, 'suggestion'), pre(suggestion), sep='\n\n')
                await bot.send_message(user.tg_id, get_message(user, 'wrong_topic'))

            for trial in trials:
                    
                    link = trial.link
    
                    if not check_trial(link):
                        trial = add_trial(trial, session)
                        await send_trial(user, trial, topic, session)
                    else:
                        backend_logger.info(f'Trial already exists: {link}')
                        trial = session.query(ClinicalTrial).filter(ClinicalTrial.link == link).first()
    
                    sent_trials = session.query(ClinicalTrial).\
                        join(User.sent_trials).filter(User.tg_id == user.tg_id).all()
    
                    if trial not in sent_trials:
                        await send_trial(user, trial, topic, session)
            
            
            
            

    
    backend_logger.info('Papers and clinical trials are up to date!')



async def scheduler():
    aioschedule.every(UPDATE_INTERVAL).seconds.do(update_papers)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())


@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message):

    await RegistrationStates.language.set()
    
    result = get_welcome_message(message.from_user.first_name)
    await message.answer(result, reply_markup = get_lang_keyboard())

@dp.message_handler(state=RegistrationStates.language, content_types=['text'])
async def set_language(message: types.Message):

    session = connect()
    tg_id = message.from_user.id
    user = select_user(tg_id, session=session)

    if check_save_lang(user, message, session):
        await RegistrationStates.check_topic.set()
        await message.answer(text(
            get_message(user, 'lang_set'),
            get_message(user, 'ask_topic'),
            sep = '\n\n'
        ), reply_markup = types.ReplyKeyboardRemove())
    else:
        await message.answer(text('Please, choose one of the supported languages from the keyboard!'), reply_markup = get_lang_keyboard())

async def correct_topic(query: str, user: User) -> str:

    reply = get_message(user, 'wrong_topic')
    suggestion = suggest_spelling(query)

    if suggestion:
        reply = text(reply, get_message(user, 'suggestion'), pre(suggestion), sep='\n\n')

    await RegistrationStates.check_topic.set()
    await bot.send_message(user.tg_id, reply, parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(state=RegistrationStates.check_topic, content_types=['text'])
async def check_topic(message: types.Message, state: FSMContext):

    session = connect()
    tg_id = message.from_user.id
    user = select_user(tg_id, session=session)

    query = process_query(message.text)

    suggestion = suggest_spelling(query)
    if suggestion:
        await correct_topic(query, user)
    else:
        await set_topic(message, state, query, user, session)

async def set_topic(message: types.Message, state: FSMContext, query: str, user: User, session):

    topics = [topic.text for topic in user.topics]
    if query in topics:
        await message.answer(get_topic_exists_message(user, query), reply_markup = types.ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN)
        await correct_topic(query, user)
    else:
        try:
            ready_papers = get_ready_papers(query)
        except Exception as e:
            backend_logger.error(e)
            await correct_topic(query, user)
        
        else:

            if not ready_papers:
                await correct_topic(query, user)
            else:
                
                try:
                    intro_review = search_last_review(query)
                except Exception as e:
                    backend_logger.error(e)
                    intro_review = None

                if intro_review:
                    await bot.send_message(user.tg_id, get_review_message(intro_review, user), parse_mode=ParseMode.MARKDOWN)
                
                await state.finish()
                await bot.send_message(user.tg_id, get_message(user, 'example_papers'), parse_mode=ParseMode.MARKDOWN)

                topic = select_topic(user, query, session=session)
                source = 'pubmed'

                not_found_count = 0
                for i, ready_paper in enumerate(ready_papers):

                    link = 'doi.org/' + ready_paper.doi
                    
                    if not check_paper(link):
                        paper = add_paper(link, ready_paper.title, ready_paper.abstract, source, session)
                    else:
                        backend_logger.info(f'Paper already exists: {link}')
                        paper = session.query(Paper).filter(Paper.link == link).first()
                    
                    if not paper:
                        backend_logger.error(f'Paper not found: {link}')
                        not_found_count += 1
                        continue
                    
                    silent = False if i - not_found_count <= 2 else True
                    try:
                        await send_paper(user, paper, topic.text, source, session, silent=silent)
                        # We send silently after first successful sending
                    except Exception as e:
                        backend_logger.error(e)
                        not_found_count += 1
                        continue


                # TODO: DRY paring errors handling
                # TODO: DRY pop articles sending
                try:
                    pop_articles = get_popular_articles(topic.text)
                except Exception as e:
                    backend_logger.error(e)
                    pop_articles = None

                if pop_articles:

                    source = 'medicalxpress'
                    await bot.send_message(user.tg_id, get_message(user, 'example_pop_article'), parse_mode=ParseMode.MARKDOWN)

                    sent = False
                    for pop_article in pop_articles:
                            
                        link = pop_article.link

                        if not check_paper(link):
                            paper = add_paper(link, pop_article.title, pop_article.abstract, source, session)
                        else:
                            backend_logger.info(f'Paper already exists: {link}')
                            paper = session.query(Paper).filter(Paper.link == link).first()

                        silent = sent
                        try:
                            await send_paper(user, paper, topic.text, source, session, silent=silent)
                            # We send silently after first successful sending
                            sent = True
                        except Exception as e:
                            backend_logger.error(e)
                            continue

                    try:
                        trials = get_last_clinical_trials(topic.text)
                    except Exception as e:
                        backend_logger.error(e)
                        trials = None
                    
                if trials:

                    await bot.send_message(user.tg_id, get_message(user, 'example_trials'), parse_mode=ParseMode.MARKDOWN)

                    sent_completed = False
                    sent_recruiting = False
                    for trial in trials:

                        link = trial.link

                        if not check_trial(link):
                            trial = add_trial(trial, session)
                        else:
                            backend_logger.info(f'Trial already exists: {link}')
                            trial = session.query(ClinicalTrial).filter(ClinicalTrial.link == link).first()

                        if trial.recruitment_status == 'Completed':
                            silent = sent_completed
                        elif trial.recruitment_status == 'Recruiting':
                            silent = sent_recruiting
                        else:
                            silent = True
                        
                        try:
                            await send_trial(user, trial, topic.text, session, silent=silent)
                            # We send silently after first successful sending
                            if trial.recruitment_status == 'Completed':
                                sent_completed = True
                            elif trial.recruitment_status == 'Recruiting':
                                sent_recruiting = True
                        except Exception as e:
                            backend_logger.error(e)
                            continue

                        

                        

                
                    

@dp.message_handler(commands=['settings'], state='*')
async def send_settings(message: types.Message):
        user = select_user(message.from_user.id)
        await RegistrationStates.setings_choice.set()
        await message.answer(get_settings_message(user ), reply_markup = get_settings_keyboard(user))

@dp.message_handler(state=RegistrationStates.setings_choice, content_types=['text'])
async def choose_setting(message: types.Message, state: FSMContext):
    
        session = connect()
        tg_id = message.from_user.id
        user = select_user(tg_id, session=session)
    
        if message.text == get_message(user, 'change_lang'):
            await RegistrationStates.change_language.set()
            await message.answer('Please, chose a language:', reply_markup = get_lang_keyboard())

        elif message.text == get_message(user, 'add_topic'):
            await RegistrationStates.check_topic.set()
            await message.answer(get_message(user, 'ask_topic'), reply_markup = types.ReplyKeyboardRemove())

        elif message.text == get_message(user, 'remove_topic'):
            await RegistrationStates.remove_topic.set()
            await message.answer(get_message(user, 'list_to_remove'), reply_markup = get_remove_topic_keyboard(user))

        else:
            await message.answer('Please, chose one of the options from the keyboard!')

@dp.message_handler(state=RegistrationStates.change_language, content_types=['text'])
async def change_language(message: types.Message, state: FSMContext):
    
        session = connect()
        tg_id = message.from_user.id
        user = select_user(tg_id, session=session)
    
        if check_save_lang(user, message, session):
            await state.finish()
            await message.answer(get_message(user, 'lang_set'), reply_markup = types.ReplyKeyboardRemove())
        else:
            await message.answer('Please, choose one of the supported languages from the keyboard!', reply_markup = get_lang_keyboard())

@dp.message_handler(state=RegistrationStates.remove_topic, content_types=['text'])
async def remove_topic(message: types.Message, state: FSMContext):

        session = connect()
        tg_id = message.from_user.id
        user = select_user(tg_id, session=session)

        topics = [topic.text for topic in user.topics]
        topic_to_remove = message.text

        if topic_to_remove in topics:
            drop_topic(user, topic_to_remove, session=session)
            await state.finish()
            await message.answer(get_topic_removed_message(user, topic_to_remove), reply_markup = types.ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN)
        else:
            await message.answer(get_message(user, 'topic_not_found'), reply_markup = get_remove_topic_keyboard(user))

@dp.message_handler(commands=['help'], state='*')
async def send_help(message: types.Message):
    await message.answer('Use /settings to change language and add or remove topics, /start to restart the bot if something is wrong')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)