import requests
from bs4 import BeautifulSoup

from dataclasses import dataclass

from helpers import to_link_format

@dataclass
class PopArticle:
    link: str
    title: str
    abstract: str

def get_popular_articles(query):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    query = to_link_format(query)
    url = f'https://medicalxpress.com/search/?search={query}&s=0'

    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')

    row_articles = soup.find_all('article')
    links = [article.find('a')['href'] for article in row_articles]
    titles = [article.find('a').text.strip() for article in row_articles]
    abstracts = [article.find('p').text.strip() for article in row_articles]

    articles = list(zip(links, titles, abstracts))

    pop_articles = [
        PopArticle(link=link, title=title, abstract=abstract)
        for link, title, abstract in articles
    ]

    return pop_articles