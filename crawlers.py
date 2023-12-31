import logging
import time
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

# Initialize the logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# Create a file handler and set the log level
file_handler = logging.FileHandler('my_log.log')
file_handler.setLevel(logging.DEBUG)

# Create a stream handler to print logs to the terminal
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)

# Create a formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class ExtractorNews:
    SELECTOR_NEWS_TASS = 'main > div[class ^= Search_search_page] a'
    SELECTOR_NEWS_DISCLOSURE = 'div.table__cell div.table__row'

    def __init__(self):
        self.latest_url_tass = ''
        self.latest_url_disclosure = ''
        self.latest_url_tass_rss = ''
        self.headers = {'User-agent': 'Mozilla/5.0 (Linux; Android 13; CPH2211 Build/TP1A.220905.001) '
                                      'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/115.0.5790.166'}
        self.logger = logger

    def get_news_tass(self):
        url = "https://tass.ru/ekonomika"
        response = requests.get(url, headers=self.headers, timeout=10)

        soup = BeautifulSoup(response.text, "lxml")

        all_news = soup.select(self.SELECTOR_NEWS_TASS)

        all_items = list()
        for news in all_news:
            item = self._make_news_item(
                title=news.select('span')[0].contents[0],
                url_article=urljoin('https://tass.ru', news['href']),
                platform='tass'
            )
            all_items.append(item)

        all_items.sort(key=lambda x: x['url_article'], reverse=True)

        latest_url = all_items[0]['url_article']
        if latest_url == self.latest_url_tass:
            self.logger.info(f'Already up-to-date in <https://tass.ru/rss/v2.xml>')
            return
        i = 0
        while i < len(all_items) and all_items[i]['url_article'] > self.latest_url_tass:
            yield all_items[i]
            i += 1
        self.latest_url_tass = all_items[0]['url_article']

    # ------------------------------------------------------------------

    def get_news_tass_rss(self):
        url = 'https://tass.ru/rss/v2.xml'

        pages = requests.get(url)

        try:
            parser = feedparser.parse(pages.text)
            if feeds_list := parser.entries:
                self.logger.info(f'Received feed response for <{url}>')
                yield from self.parse_feed(feeds_list)
                return
        except Exception as exep:
            self.logger.info(f"Can't parse response from <{url}> exception: {exep}")
            return

    def parse_feed(self, feeds_list):
        all_items = []
        for feed in feeds_list:

            result_item = self._make_news_item(title=feed.get('title'),
                                               platform='latest_url_tass_rss',
                                               url_article=feed.get('link'),
                                               source='https://tass.ru/rss/v2.xml')

            if pub_date := feed.get('published'):
                result_item['publication_date'] = pub_date

            if categories := [tag.term.strip() for tag in feed.get('tags', [])]:
                result_item['category'] = categories

            if categories and 'Экономика и бизнес' in categories:
                all_items.append(result_item)

        all_items.sort(key=lambda x: x['url_article'], reverse=True)

        latest_url = all_items[0]['url_article']
        if latest_url == self.latest_url_tass_rss:
            self.logger.info(f'Already up-to-date in <https://tass.ru/rss/v2.xml>')
            return
        i = 0
        while i < len(all_items) and all_items[i]['url_article'] > self.latest_url_tass_rss:
            yield all_items[i]
            i += 1
        self.latest_url_tass_rss = all_items[0]['url_article']

    # ------------------------------------------------------------------

    def get_news_disclosure(self):
        url = 'https://www.e-disclosure.ru/'
        pages = requests.get(url)
        soup = BeautifulSoup(pages.text, "lxml")

        all_news = soup.select(self.SELECTOR_NEWS_DISCLOSURE)

        all_items = list()
        for news in all_news:
            item = self.extract_item_from_disclosure(news)
            all_items.append(item)

        all_items.sort(key=lambda x: x['url_article'], reverse=True)

        latest_url = all_items[0]['url_article']
        if latest_url == self.latest_url_disclosure:
            self.logger.info(f'Already up-to-date in <https://tass.ru/rss/v2.xml>')
            return
        i = 0
        while i < len(all_items) and all_items[i]['url_article'] > self.latest_url_disclosure:
            yield all_items[i]
            i += 1

        self.latest_url_disclosure = all_items[0]['url_article']

    def extract_item_from_disclosure(self, news):
        cells = news.select('div.table__cell')
        text_from_cells = cells[1].text.split('\n')
        urls_from_cells = list(map(lambda x: x['href'], cells[1].select('a[href]')))
        item = self._make_news_item(
            title=text_from_cells[3],
            platform='e-disclosure',
            url_article=urls_from_cells[1],
            source=text_from_cells[-2]
        )
        item['company'] = text_from_cells[1]
        item['url_company'] = urls_from_cells[0]
        return item

    # ------------------------------------------------------------------

    @staticmethod
    def _make_news_item(title=None,
                        platform=None,
                        type='news',
                        url_article=None,
                        source=None):
        item = {
            '_timestamp': int(time.time()),
            'type': type
        }
        if title:
            item['title'] = title
        if platform:
            item['platform'] = platform
        if url_article:
            item['url_article'] = url_article
        if source:
            item['source'] = source
        return item


if __name__ == "__main__":
    extractor = ExtractorNews()
    while True:
        for item in extractor.get_news_tass():
            print(item)
        logger.debug(f'CRAWLED <https://tass.ru/ekonomika>')
        for item in extractor.get_news_disclosure():
            print(item)
        logger.debug(f'CRAWLED <https://www.e-disclosure.ru/>')
        for item in extractor.get_news_tass_rss():
            print(item)
        logger.debug(f'CRAWLED <https://tass.ru/rss/v2.xml>')

        # time.sleep(5)
