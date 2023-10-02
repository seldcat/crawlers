from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import feedparser
import time


def get_news_tass():
    url = "https://tass.ru/ekonomika"
    user_agent = {'User-agent': 'Mozilla/5.0 (Linux; Android 13; CPH2211 Build/TP1A.220905.001) AppleWebKit/537.36 '
                                '(KHTML, like Gecko) Version/4.0 Chrome/115.0.5790.166 Mobile Safari/537.36'}
    pages = requests.get(url, headers=user_agent)

    soup = BeautifulSoup(pages.text, "lxml")

    for news in soup.select('a[class^=tass_pkg_link]'):
        news_url = urljoin('https://tass.ru', news['href'])
        title = news.select('span[class^=ds_ext_title]')[0].contents[0]

        item = {
            '_timestamp': int(time.time()),
            'url': news_url,
            'title': title
        }
        yield item


def get_news_tass_rss():
    url = 'https://tass.ru/rss/v2.xml'

    pages = requests.get(url)

    try:
        parser = feedparser.parse(pages.text)
        if feeds_list := parser.entries:
            print(f'Received feed response for {url}')
            yield from parse_feed(feeds_list)
            return
    except Exception as exep:
        print(f"Can't parse response from {url}  exception: {exep}")
        return


def parse_feed(feeds_list):
    for feed in feeds_list:

        result_item = {
            '_timestamp': int(time.time()),
            'platform': 'tass',
            'type': 'news',
        }

        if pub_date := feed.get('published'):
            result_item['publication_date'] = pub_date

        if title := feed.get('title'):
            result_item['title'] = title.strip()

        if url := feed.get('link'):
            result_item['url'] = urljoin('https://tass.ru', url.strip())

        if categories := [tag.term.strip() for tag in feed.get('tags', [])]:
            result_item['category'] = categories

        if categories and 'Экономика и бизнес' in categories:
            yield result_item


def get_news_enclosure():
    url = 'https://www.e-disclosure.ru/'
    pages = requests.get(url)
    soup = BeautifulSoup(pages.text, "lxml")

    for news in soup.select('div.table__cell div.table__row'):
        yield extract_item_from_enclosure(news)


def extract_item_from_enclosure(news):
    cells = news.select('div.table__cell')
    text_from_cells = cells[1].text.split('\n')
    urls_from_cells = list(map(lambda x: x['href'], cells[1].select('a[href]')))
    item = {
        'time': cells[0].text,
        'company': text_from_cells[1],
        'url_company': urls_from_cells[0],
        'title': text_from_cells[3],
        'url_title': urls_from_cells[1],
        'source': text_from_cells[-2]
    }
    return item


# while True:    # TODO retries
#     for elem in get_news_tass():
#         print(elem)
#
#     for elem in get_news_tass_rss():
#         print(elem)
#
#     time.sleep(5)

for elem in get_news_enclosure():
    print(elem)
