from bs4 import BeautifulSoup
import requests


def get_news_tass():
    url = "https://tass.ru/ekonomika"

    pages = requests.get(url)

    soup = BeautifulSoup(pages.text, "lxml")

    for news in soup.select('div[class^=tass_pkg_title_wrapper], div[class^=Message_text]'):
        item = {
            'url': news.select('href'),
            'text': news.getText
        }
        yield item


def get_news_tass_rss():
    pass


def get_news_enclosure():
    pass


