"""Useful quite universal functions, which are used in tgbot or other places."""

from spellchecker import SpellChecker
import string
import re

def suggest_spelling(s: str):
    
    spell = SpellChecker()
    corrected = False
    output_words = []

    words = s.split()
    for word in words:
        correction = spell.correction(word)
        frequency = spell.word_usage_frequency(correction)
        if (correction is not None) and (correction != word) and (frequency > 10**(-5)):
            corrected = True
            output_words.append(spell.correction(word))
        else:
            output_words.append(word)

    if corrected:
        return ' '.join(output_words)
    else:
        return ''

def remove_punctuation(s: str):
    return s.translate(str.maketrans('', '', string.punctuation))

# All whitespace symbols are replaced with single space
def clean_whitespase_symbols(text: str) -> str:
    return re.sub(r'\s+', ' ', text)

# Whitespaces are replaced with + sign
def to_link_format(query: str) -> str:
    query_lst = query.split(' ')
    return '+'.join(query_lst)

def process_query(query: str) -> str:
    query = clean_whitespase_symbols(query)
    query_words = remove_punctuation(query).split()
    query = ' '.join(query_words).capitalize()
    return query
