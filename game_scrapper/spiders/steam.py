"""
Steam spider.
"""

import json
from datetime import datetime
from scrapy import Spider, Request, Selector


# Got from: https://store.steampowered.com/search/?sort_by=_ASC&filter=topsellers
BASE_URL = 'https://store.steampowered.com/search/results/?query&dynamic_data=&sort_by=_ASC&filter=topsellers&infinit' \
           'e=1&count=100'

TARGET_INSTANCES = 3000


class SteamSpider(Spider):
    """
    Steam Spider implementation
    """

    name = 'steam'

    def start_requests(self):
        """
        Start the requests
        """

        for start in range(0, TARGET_INSTANCES + 1, 100):
            yield Request(
                url=f'{BASE_URL}&start={start}',
                callback=self.parse
            )

    def parse(self, response):
        """
        Parse the response
        """

        data = json.loads(response.text)
        html = data['results_html']
        selector = Selector(text=html)

        for link in selector.css('a::attr(href)').getall():
            yield Request(
                url=link,
                callback=self.parse_game
            )

    def parse_game(self, response):
        """
        Parse the game page
        """

        title = response.css('div#appHubAppName_responsive::text').get()
        price = response.css('div.game_purchase_price::text').get()
        date = response.css('div.date::text').get()
        genres = response.css('a.app_tag::text').getall()
        developer = response.css('div#developers_list a::text').get()
        publisher = response.css('a[href*="publisher"]::text').get()

        if title is None:
            return

        title = title.strip()

        if price is not None:
            price = price.strip()

            if price.startswith('R$ '):
                price = price[3:].replace(',', '.')

        if date is not None:
            date = date.strip()
            day, month, year = date.split()
            month = datetime.strptime(month[:-1], '%b').strftime('%m')
            iso_date = f'{year}-{month}-{day}'

        genres = list(map(str.strip, genres))

        if developer is not None:
            developer = developer.strip()

        if publisher is not None:
            publisher = publisher.strip()

        yield {
            'title': title,
            'price': price,  # BRL
            'release_date': iso_date,
            'genres': genres,
            'developer': developer,
            'publisher': publisher,
        }
