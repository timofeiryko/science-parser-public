"""In this module all the "frontend" things are defined: messages, keyboards, etc. There are also some helper functions to work with """

from dataclasses import dataclass
from itertools import count

from emoji import emojize
from flag import flag

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.markdown import text, bold, code, italic, pre, link

from db_map import ClinicalTrial, Paper, User
from parsers.scholar_parser import ScholarArticle
from configs import SUPPORTED_LANGS

# Remove keyboard after reply
def get_lang_keyboard() -> ReplyKeyboardMarkup:

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    
    for unicode, lang in SUPPORTED_LANGS.items():

        unicode = 'gb' if unicode == 'en' else unicode
        keyboard.add(f'{flag(unicode)} {lang}')

    return keyboard

def get_settings_keyboard(user: User) -> ReplyKeyboardMarkup:

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.row(get_message(user, 'add_topic'), get_message(user, 'remove_topic'))
    keyboard.add(get_message(user, 'change_lang'))

    return keyboard

def get_remove_topic_keyboard(user) -> ReplyKeyboardMarkup:

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    for topic in user.topics:
        keyboard.add(topic.text)

    return keyboard

def get_all_flags() -> str:

    for unicode, lang in SUPPORTED_LANGS.items():
        unicode = 'gb' if unicode == 'en' else unicode
        yield flag(unicode)

@dataclass
class MessageText:
    en: str
    ru: str

lang_set = MessageText(
    en='Language set.',
    ru='Язык установлен.'
)

ask_topic = MessageText(
    en='Welcome to the Pubmed Bot!\n\n' \
        'I will regularly send the papers with abstracts on the topic you are interested in. ' \
        'In addition, I will also send popular science articles (press releases) and information about started and completed clinical trials.\n\n' \
        'Please, send me the topic you are interested in. It will be used as a query for our databases.\n\n' \
        'Example: "Psoriatic arthritis treatment"',
    ru = 'Добро пожаловать в Pubmed Bot!\n\n' \
        'Я буду регулярно отправлять научные публикации с аннотациями на тему, которая вам интересна. ' \
        'Кроме того, я буду отправлять научно-популярные статьи (пресс-релизы) и информацию о начавшихся или завершивхся клинических испытаниях.\n\n' \
        'Пожалуйста, пришлите мне тему (на английском). Это сообщение будет использовано в качестве запроса в наших базах данных.\n\n' \
        'Пример: "Psoriatic arthritis treatment"'
)

wrong_topic = MessageText(
    en='Sorry, something is wrong with your query. Please, send me the topic again.\n\n'\
        'Probably, you should correct the misspeling or reformulate your query.',
    ru='Извините, с вашим запросом что-то не так. Пожалуйста, пришлите мне тему заново.\n\n'\
        'Вероятно, вам нужно исправить опечатку или переформулировать запрос.'
)

suggestion = MessageText(
    en='Ptobably, you meant:',
    ru='Возможно, вы имели в виду:'
)

intro_review = MessageText(
    en='All is set up! To add or remove topics and change language, send me /settings\n\n' \
        'I recomend to have a look on the  most relevant scientific review on your topic:',
    ru='Всё настроено! Чтобы добавить или удалить тему и изменить ызык, отправьте мне /settings\n\n' \
        'Я рекомендую почитать наиболее актуальный научный обзор по теме:'
)

example_papers = MessageText(
    en='When I find new publications on your tpoic, I will inform you of this. Here are 3 recent papers as an example:',
    ru='Когда я нахожу новые публикации на вашу тему, я сообщаю вам об этом. Вот 3 недавние статьи в качестве примера:'
)

settings = MessageText(
    en='What do you want to do? Here are the topics you are subscribed to:',
    ru='Что вы хотите сделать? Вот темы, на которые вы подписаны:'
)

change_lang = MessageText(
    en=f'Change language {" ".join(get_all_flags())}',
    ru=f'Изменить язык {" ".join(get_all_flags())}'
)

add_topic = MessageText(
    en=emojize(':heavy_plus_sign: Add topic', language='alias'),
    ru=emojize(':heavy_plus_sign: Добавить тему', language='alias')
)

remove_topic = MessageText(
    en=emojize(':heavy_multiplication_x: Remove topic', language='alias'),
    ru=emojize(':heavy_multiplication_x: Удалить тему', language='alias')
)

example_pop_article = MessageText(
    en='Example of medical press release:',
    ru='Пример медицинского пресс-релиза:'
)

list_to_remove = MessageText(
    en='Choose the topic you want to unsubscribe from',
    ru='Выберите тему, от которой вы хотите отписаться'
)

topic_removed = MessageText(
    en='You unsubscribed from the topic',
    ru='Вы отписались от темы'
)

topic_not_found = MessageText(
    en='Choose one of the topics you are subscribed to from the keyboard!',
    ru='Выберите одну из тем, на которые вы подписаны, с клавиатуры!'
)

topic_exists = MessageText(
    en='You are already subscribed to the topic',
    ru='Вы уже подписаны на тему'
)

example_trials = MessageText(
    en='Example clinical trials:',
    ru='Примеры клинических исследований:'
)

MESSAGES = {
    'ask_topic': ask_topic,
    'lang_set': lang_set,
    'wrong_topic': wrong_topic,
    'suggestion': suggestion,
    'intro_review': intro_review,
    'example_papers': example_papers,
    'settings': settings,
    'change_lang': change_lang,
    'add_topic': add_topic,
    'remove_topic': remove_topic,
    'example_pop_article': example_pop_article,
    'list_to_remove': list_to_remove,
    'topic_removed': topic_removed,
    'topic_not_found': topic_not_found,
    'topic_exists': topic_exists,
    'example_trials': example_trials
}

def get_message(user: User, key: str) -> str:
    lang = user.lang if user.lang else 'en'
    return getattr(MESSAGES[key], lang)

def get_review_message(review: ScholarArticle, user) -> str:
    
    review_message = '\n\n'.join([
        get_message(user, 'intro_review'),
        bold(review.title),
        italic('\n'.join(review.info.split(' - ')[:2])),
        text(review.text),
        link('READ MORE', review.link)

    ])

    return review_message


def get_paper_message(paper: Paper, topic: str, source: str) -> str:

    if source == 'pubmed':
        notification_line = emojize(f':microscope: New scientific publication about *{topic.lower()}*!')
        link_line = paper.link
    elif source == 'medicalxpress':
        notification_line = f'\N{rolled-up newspaper} New press-release about *{topic.lower()}*!'
        link_line = paper.link

    paper_message = '\n\n'.join([
        notification_line,
        f'*{paper.title}*',
        paper.content_md,
        link_line
    ]) 

    return paper_message

def get_welcome_message(username) -> str:
    return f'Hello, {username}! Please, chose a language:'

def get_settings_message(user) -> str:
    
        settings_message = '\n\n'.join([get_message(user, 'settings')] + [
            f'{i+1}) {topic.text}' for i, topic in enumerate(user.topics)
        ])
    
        return settings_message

def get_topic_removed_message(user, topic_text) -> str:
    return f'{get_message(user, "topic_removed")} *"{topic_text}"*'

def get_topic_exists_message(user, topic_text) -> str:
    return f'{get_message(user, "topic_exists")} *"{topic_text}"*'

def get_trial_message(trial: ClinicalTrial, topic_text) -> str:

    topic_text = topic_text.lower()

    if trial.recruitment_status == 'Recruiting':

        locations = emojize('\n\n:pushpin:').join([
            f'{location.name} - {location.country}, {location.city}' for location in trial.locations
        ])

        trial_message = '\n\n'.join([
            emojize(f':pill: Clinical trial regarding *{topic_text}* is recruiting!'),
            bold(trial.title.replace('\\', '')),
            trial.description,
            bold('Eligibility criterias for participants'),
            trial.criteria,
            link('See more information and participate', trial.link)
        ])

        # Check if message is too long for telegram and send shorter version
        if len(trial_message) > 4096:
            trial_message = '\n\n'.join([
                emojize(f':pill: Clinical trial regarding *{topic_text}* is recruiting!'),
                bold(trial.title),
                bold('Eligibility criterias for participants'),
                trial.criteria,
                link('See more information and participate', trial.link)
            ])

        # Check again if message is too long for telegram and send even shorter version
        if len(trial_message) > 4096:
            trial_message = '\n\n'.join([
                emojize(f':pill: Clinical trial regarding *{topic_text}* is recruiting!'),
                bold(trial.title),
                link('See more information and participate', trial.link)
            ])

    if trial.recruitment_status == 'Completed':

        trial_message = '\n\n'.join([
            emojize(f':pill: Clinical trial regarding *{topic_text}* is completed!'),
            bold(trial.title),
            trial.description,
            link('See more information results', trial.link)
        ])

        # Check if message is too long for telegram and send shorter version
        if len(trial_message) > 4096:
            trial_message = '\n\n'.join([
                emojize(f':pill: Clinical trial regarding *{topic_text}* is completed!'),
                bold(trial.title),
                link('See more information results', trial.link)
            ])

    return trial_message
