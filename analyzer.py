"""
Data analyzer
"""

from json import load
from datetime import datetime


class Distribution():

    _min_value: float | int
    _max_value: float | int
    _class_count: int
    _sorted_keys: list[float | int]
    _classes: dict[float | int, int]
    _count: int

    def __init__(self, data: list[float | int], class_count: int, int_mode: bool = False) -> None:
        self._min_value = min(data)
        self._max_value = max(data)
        self._class_count = class_count
        self._sorted_keys = []
        self._classes = {}
        self._count = 0

        for i in range(class_count):
            class_ = self._min_value + (self._max_value - self._min_value) * i / class_count

            if int_mode:
                class_ = int(class_)

            self._sorted_keys.append(class_)
            self._classes[class_] = 0

        for value in data:
            for key in self._sorted_keys[::-1]:
                if value >= key:
                    self._classes[key] += 1
                    break

            self._count += 1

    def __str__(self) -> str:
        lines = []

        lines.append('Class - Count - Percentage - Distribution')

        if isinstance(self._sorted_keys[0], int):
            max_class_length = len(str(self._sorted_keys[-1]))
        else:
            max_class_length = len(f'{self._sorted_keys[-1]:.2f}')

        max_class_value_length = len(str(max(self._classes.values())))

        for i in range(self._class_count):
            if isinstance(self._sorted_keys[i], int):
                if i < self._class_count - 1:
                    lines.append(f'{self._sorted_keys[i]:{max_class_length}} - '
                                 f'{self._sorted_keys[i + 1]:{max_class_length}} | ')
                else:
                    lines.append(f'{self._sorted_keys[i]:{max_class_length}} - {self._max_value} | ')
            else:
                if i < self._class_count - 1:
                    lines.append(f'{self._sorted_keys[i]:{max_class_length}.2f} - '
                                 f'{self._sorted_keys[i + 1]:{max_class_length}.2f} | ')
                else:
                    lines.append(f'{self._sorted_keys[i]:{max_class_length}.2f} - {self._max_value:.2f} | ')

            lines[-1] += f'{self._classes[self._sorted_keys[i]]:{max_class_value_length}} | ' + \
                f'{(self._classes[self._sorted_keys[i]] / self._count) * 100.0:5.2f}% | ' + \
                '█' * int((self._classes[self._sorted_keys[i]] / self._count) * 100.0)

        return '\n'.join(lines)


epic_games_data = None
gog_data = None
steam_data = None

with open('epic_games.json', 'r', encoding='utf-8') as file:
    epic_games_data = load(file)

with open('gog.json', 'r', encoding='utf-8') as file:
    gog_data = load(file)

with open('steam.json', 'r', encoding='utf-8') as file:
    steam_data = load(file)

prices = []

for game in epic_games_data + gog_data + steam_data:
    try:
        prices.append(float(game['price']))
    except ValueError:
        pass
    except TypeError:
        pass

print('PRICES:')
print('GAMES:', len(prices))
print(Distribution(prices, 20))

cheaper_than_100_prices = list(filter(lambda x: x < 100, prices))
print('\nCHEAPER THAN 100:', len(cheaper_than_100_prices))
print(Distribution(cheaper_than_100_prices, 20))

cheaper_than_10_prices = list(filter(lambda x: x < 10, prices))
print('\nCHEAPER THAN 10:', len(cheaper_than_10_prices))
print(Distribution(cheaper_than_10_prices, 20))

years = []

for game in epic_games_data + gog_data + steam_data:
    try:
        year = int(game['release_date'].split('-')[0])

        if year <= datetime.now().year:
            years.append(year)
    except AttributeError:
        pass
    except ValueError:
        pass

print('\nYEARS:')
print('GAMES:', len(years))
print(Distribution(years, 20, True))
