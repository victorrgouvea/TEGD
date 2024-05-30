import json
from scrapy import Spider, Request


# Got from: https://store.epicgames.com/pt-BR/browse?sortBy=relevancy&sortDir=DESC&category=Game&count=40&start=40
BASE_URL = 'https://store.epicgames.com/graphql'

GENRES_URL = 'https://store.epicgames.com/graphql?operationName=getStoreTagsByGroupName&variables=%7B"storeId":"EGS","groupName":"event%7Cfeature%7Cepicfeature%7Cgenre%7Cplatform%7Csubscription","locale":"pt-BR","sortBy":"name","sortDir":"ASC"%7D&extensions=%7B"persistedQuery":%7B"version":1,"sha256Hash":"15fffcb1dddbd6ae365a603b44784853264126d9eb24098660a9e5e9eaf2ba26"%7D%7D'

PARAMS = '?operationName=searchStoreQuery&variables=%7B"allowCountries":"BR","category":"games%2Fedition%2Fbase"' \
            ',"count":1000,"country":"BR","keywords":"","locale":"pt-BR","sortBy":"relevancy,viewableDate","sortDir":"DESC,DESC","tag":"","withPrice":true%7D&extensions=%7B' \
            '"persistedQuery":%7B"version":1,"sha256Hash":"7d58e12d9dd8cb14c84a3ff18d360bf9f0caa96bf218f2c5fda68ba88d68a437"%7D%7D'

class EpicGamesSpider(Spider):
    name = "epic_games"

    custom_settings = {'RETRY_TIMES': 10}

    genres = {}

    def start_requests(self):
        yield Request(
            url=GENRES_URL,
            callback=self.parse_genres,
        )

    def parse_genres(self, response):
        data = json.loads(response.text).get("data", {}).get("Catalog", {}).get("tags", {})

        genres = data.get("elements", [])

        for genre in genres:
            id = genre.get("id")
            name = genre.get("name")

            if id and name:
                self.genres[id] = name

        # After getting genres, start the main request
        yield Request(
            url=f'{BASE_URL}?operationName=searchStoreQuery&variables=%7B"allowCountries":"BR","category":"games%2Fedition%2Fbase"' \
            ',"count":500,"country":"BR","keywords":"","locale":"pt-BR","sortBy":"relevancy,viewableDate","sortDir":"DESC,DESC","tag":"","withPrice":true%7D&extensions=%7B' \
            '"persistedQuery":%7B"version":1,"sha256Hash":"7d58e12d9dd8cb14c84a3ff18d360bf9f0caa96bf218f2c5fda68ba88d68a437"%7D%7D',
            callback=self.parse,
            meta={"count": 1000},
        )

    def parse(self, response):
        data = json.loads(response.text).get("data", {}).get("Catalog", {}).get("searchStore", {})

        products = data.get("elements", [])

        for product in products:

            price = product.get("price", {}).get("totalPrice", {}).get("fmtPrice", {}).get("originalPrice", {})

            tags = [tag.get("id") for tag in data.get("tags", [])]
            genres = [self.genres.get(tag) for tag in tags]

            # Save information about each game
            yield {
                "title": product.get("title"),
                "price": price.replace("R$", "").strip(),  # BRL
                "release_date": product.get("releaseDate").split("T")[0],  # Format: yyyy-mm-dd
                "genres": genres,  # List of genres
                "developer": product.get("developerDisplayName"),
                "publisher": product.get("publicherDisplayName"),
            }

        # Check for next pages
        count = response.meta['count']
        total_count = data.get("paging", {}).get("total", 0)

        if count < total_count:
            yield Request(
                url=f'{BASE_URL}?operationName=searchStoreQuery&variables=%7B"allowCountries":"BR","category":"games%2Fedition%2Fbase"' \
                    f',"count":1000,"country":"BR","start":{count},"keywords":"","locale":"pt-BR","sortBy":"relevancy,viewableDate","sortDir":"DESC,DESC","tag":"","withPrice":true%7D&extensions=%7B' \
                    '"persistedQuery":%7B"version":1,"sha256Hash":"7d58e12d9dd8cb14c84a3ff18d360bf9f0caa96bf218f2c5fda68ba88d68a437"%7D%7D',
                callback=self.parse,
                meta={"count": count + 1000},
            )
