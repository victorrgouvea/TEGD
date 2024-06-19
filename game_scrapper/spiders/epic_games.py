"""
Epic Games Spider
"""

from json import loads
from scrapy import Spider, Request


# Got from: https://store.epicgames.com/pt-BR/browse?sortBy=relevancy&sortDir=DESC&category=Game&count=40&start=40
BASE_URL = 'https://store.epicgames.com/graphql'

GENRES_URL = 'https://store.epicgames.com/graphql?operationName=getStoreTagsByGroupName&variables=%7B"storeId":"EGS",' \
             '"groupName":"event%7Cfeature%7Cepicfeature%7Cgenre%7Cplatform%7Csubscription","locale":"pt-BR","sortBy"' \
             ':"name","sortDir":"ASC"%7D&extensions=%7B"persistedQuery":%7B"version":1,"sha256Hash":"15fffcb1dddbd6ae' \
             '365a603b44784853264126d9eb24098660a9e5e9eaf2ba26"%7D%7D'


class EpicGamesSpider(Spider):
    """
    Epic Games Spider implementation
    """

    name = 'epic_games'
    custom_settings = {'RETRY_TIMES': 10}
    genres = {}

    def start_requests(self):
        """
        Start the requests
        """

        # Parse genres and build a dict for them first
        yield Request(
            url=GENRES_URL,
            callback=self.parse_genres,
        )

    def get_genres(self, tags):
        """
        Get genres based on tags
        """

        genres = []

        for tag in tags:
            genre = self.genres.get(tag)
            if genre:
                genres.append(genre)

        return genres

    def parse_genres(self, response):
        """
        Parse genres
        """

        data = loads(response.text).get('data', {}).get('Catalog', {}).get('tags', {})

        genres = data.get('elements', [])

        for genre in genres:
            if genre.get('groupName') == 'genre':
                id_ = genre.get('id')
                name = genre.get('name')

                if id_ and name:
                    self.genres[id_] = name

        # After getting genres, start the main request
        yield Request(
            url=f'{BASE_URL}?operationName=searchStoreQuery&variables=%7B"allowCountries":"BR","category":"games%2Fed'
            'ition%2Fbase","count":1000,"country":"BR","keywords":"","locale":"pt-BR","sortBy":"relevancy,viewableDat'
            'e","sortDir":"DESC,DESC","tag":"","withPrice":true%7D&extensions=%7B"persistedQuery":%7B"version":1,"sha'
            '256Hash":"7d58e12d9dd8cb14c84a3ff18d360bf9f0caa96bf218f2c5fda68ba88d68a437"%7D%7D',
            callback=self.parse,
            meta={"count": 1000},
        )

    def parse(self, response):
        """
        Parse the response
        """

        data = loads(response.text).get('data', {}).get('Catalog', {}).get('searchStore', {})

        products = data.get('elements', [])

        for product in products:
            price = product.get('price', {}).get('totalPrice', {}).get('fmtPrice', {}).get('originalPrice', {})

            # Get genres already scrapped based on tags
            tags = [tag.get('id') for tag in product.get('tags', [])]
            genres = self.get_genres(tags)

            # Save information about each game
            yield {
                'title': product.get('title'),
                'price': price.replace('R$', '').strip().replace(',', '.'),  # BRL
                # Format: yyyy-mm-dd
                'release_date': product.get('releaseDate').split('T')[0] if product.get('releaseDate') else 'TBA',
                'genres': genres,  # List of genres
                'developer': product.get('developerDisplayName'),
                'publisher': product.get('publisherDisplayName'),
            }

        # Check for next pages
        count = response.meta['count']
        total_count = data.get('paging', {}).get('total', 0)

        if count < total_count:
            yield Request(
                url=f'{BASE_URL}?operationName=searchStoreQuery&variables=%7B"allowCountries":"BR","category":"games%'
                f'2Fedition%2Fbase","count":1000,"country":"BR","start":{count},"keywords":"","locale":"pt-BR","s'
                'ortBy":"relevancy,viewableDate","sortDir":"DESC,DESC","tag":"","withPrice":true%7D&extensions=%'
                '7B"persistedQuery":%7B"version":1,"sha256Hash":"7d58e12d9dd8cb14c84a3ff18d360bf9f0caa96bf218f2c'
                '5fda68ba88d68a437"%7D%7D,',
                callback=self.parse,
                meta={"count": count + 1000},  # set the start for next request
            )
