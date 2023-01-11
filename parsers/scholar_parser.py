from bs4 import BeautifulSoup
import requests

from typing import Optional
from datetime import datetime
from dataclasses import dataclass
import logging, sys
import re
import traceback

from serpapi import GoogleSearch

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from fp.fp import FreeProxy

from configs import API_KEY, MAX_YEARS_AGO
from helpers import remove_punctuation, clean_whitespase_symbols, to_link_format

scholar_logger = logging.getLogger('scholar')
scholar_logger.addHandler(logging.StreamHandler(sys.stdout))
scholar_logger.setLevel(logging.INFO)


highest_year = datetime.now().year
lowest_year = datetime.now().year - MAX_YEARS_AGO

@dataclass
class ScholarArticle:
    link: str
    title: str
    text: str
    info: str


def extract_article(html: str) -> ScholarArticle:

    soup = BeautifulSoup(html, 'html.parser')

    # Extract first title from google scholar results
    title = soup.find('div', id='gs_res_ccl_mid').find('h3', {'class': 'gs_rt'}).find('a').text

    # Extract first link from google scholar results
    link = soup.find('div', id='gs_res_ccl_mid').find('h3', {'class': 'gs_rt'}).find('a')['href']

    # Extract first author info from google scholar results
    info = soup.find('div', id='gs_res_ccl_mid').find('div', {'class': 'gs_a'}).text

    results = [clean_whitespase_symbols(result) for result in [link, title, '', info]]

    scholar_logger.info('SUCCESSFULLY PARSED ARTICLE FROM HTML')

    return ScholarArticle(*results)

def extract_abstract(item_html: str) -> str:

    item_soup = BeautifulSoup(item_html, 'html.parser')

    item_text = item_soup.find('div', id='gs_res_ccl_mid').find('div', {'class': 'gs_rs'}).text
    item_text = item_text[:-2] + '...'

    scholar_logger.info('SUCCESSFULLY PARSED ABSTRACT FROM HTML')
    
    return item_text

def generate_scholar_link(query: str, get_abstract: Optional[bool]=False) -> str:
    scholar_query = to_link_format(query)
    if get_abstract:
        link = f'https://scholar.google.com/scholar?q={scholar_query}'
        scholar_logger.info(f'GENERATED LINK TO GET ABSTRACT: {link}')
        return link
    else:
        link = f'https://scholar.google.com/scholar?q={scholar_query}&hl=en&as_sdt=0,5&as_ylo={lowest_year}&as_yhi={highest_year}&as_rr=1'
        scholar_logger.info(f'GENERATED LINK TO GET ARTICLE: {link}')
        return link

def search_last_review_requests(query: str) -> ScholarArticle:

    scholar_logger.info('TRYING TO SEARCH WITH REQUESTS')

    headers = {
        'User-agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15'
    }

    html = requests.get(generate_scholar_link(query), headers=headers).text
    scholar_logger.info('GOT HTML WITH REQUESTS')

    article = extract_article(html)
    item_html = requests.get(generate_scholar_link(article.title + ' ' + article.info, get_abstract=True), headers=headers).text
    article.text = extract_abstract(item_html)

    return article


def search_last_review_selenium(query: str) -> ScholarArticle:

    scholar_logger.info('TRYING TO SEARCH WITH SELENIUM')

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    # add proxy to options
    PROXY = FreeProxy().get().split('//')[1]
    options.add_argument(f'--proxy-server={PROXY}')

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.get(generate_scholar_link(query))

    html = driver.page_source
    scholar_logger.info('GOT HTML WITH SELENIUM')

    article = extract_article(html)
    driver.get(generate_scholar_link(article.title + ' ' + article.info, get_abstract=True))
    item_html = driver.page_source
    article.text = extract_abstract(item_html)

    return article

def search_last_review(query: str) -> ScholarArticle:

    try:
        review = search_last_review_requests(query)
    except Exception as e:
        scholar_logger.error(f'ERROR WHILE SEARCHING LAST REVIEW: {e}')
        scholar_logger.error(traceback.format_exc())
        try:
            review = search_last_review_selenium(query)
        except Exception as e:
            scholar_logger.error(f'ERROR WHILE SEARCHING LAST REVIEW: {e}')
            scholar_logger.error(traceback.format_exc())
            review = None

    return review
    
# deprecated
def search_last_review_serpapi(query: str) -> ScholarArticle:

        scholar_logger.info('TRYING TO SEARCH WITH SERP API')

        params = {
            'q': query,
            'engine': 'google_scholar',
            'hl': 'en',
            'as_ylo': str(lowest_year),
            'as_yhi': str(highest_year),
            'api_key': API_KEY,
            'as_rr': '1'

        }

        search = GoogleSearch(params)
        results = search.get_dict()
        first = results['organic_results'][0]


        review = ScholarArticle(
            link=first['link'],
            title=first['title'],
            text=first['snippet']
        )

        return review


if __name__ == '__main__':
    print(search_last_review('cancer'))