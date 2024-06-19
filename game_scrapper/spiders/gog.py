"""
Gog Spider
"""

import json
from scrapy import Spider, Request


# Got from: https://www.gog.com/en/games
BASE_URL = 'https://catalog.gog.com/v1/catalog'


class GogSpider(Spider):
    """
    Gog Spider implementation
    """

    name = 'gog'

    def start_requests(self):
        """
        Start the requests
        """

        yield Request(
            url=f'{BASE_URL}?limit=140&order=desc%3Atrending&productType=in%3Agame%2Cpack%2Cdlc%2Cextras&page=1&count'
            'ryCode=BR&locale=en-US&currencyCode=BRL',
            callback=self.parse,
            meta={'page': 1},
        )

    def parse(self, response):
        """
        Parse the response
        """

        data = json.loads(response.text)

        products = data.get('products', [])

        for product in products:

            price = product.get('price')
            release_date = product.get('releaseDate')

            # Check for unreleased games
            if product.get('productState') == 'coming-soon':
                if price is None:
                    price = 'TBA'
                if release_date is None:
                    release_date = 'TBA'
            else:
                price = product.get('price').get('finalMoney').get('amount')

            # Save information about each game
            yield {
                'title': product.get('title'),
                'price': price,  # BRL
                'release_date': release_date.replace('.', '-') if release_date else release_date,  # Format: yyyy-mm-dd
                'genres': [genre.get('name') for genre in product.get('genres', [])],  # List of genres
                'developer': product.get('developers', [])[0],
                'publisher': product.get('publishers', [])[0],
            }

        # Check for next pages
        page = response.meta['page']
        total_pages = data.get('pages')

        if page < total_pages:
            yield Request(
                url=f'{BASE_URL}?limit=140&order=desc%3Atrending&productType=in%3Agame%2Cpack%2Cdlc%2Cextras&page='
                f'{page + 1}&countryCode=BR&locale=en-US&currencyCode=BRL',
                callback=self.parse,
                meta={"page": page + 1},
            )
