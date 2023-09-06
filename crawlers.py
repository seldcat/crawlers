from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin


def get_news_tass():
    url = "https://tass.ru/ekonomika"

    pages = requests.get(url)

    soup = BeautifulSoup(pages.text, "lxml")

    for news in soup.select('a[class^=tass_pkg_link]'):
        news_url = urljoin('https://tass.ru', news['href'])
        title = news.select('span[class^=ds_ext_title]')[0].contents[0]

        item = {
            'url': news_url,
            'title': title
        }
        yield item


def get_news_tass_rss():
    pass


def get_news_enclosure():
    pass


for elem in get_news_tass():
    print(elem)
