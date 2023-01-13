""" Коллекция статей.
    Описание:
        Класс ArtCollection, Представляющий коллекцию статей.
    © Михаил Духонин
    13.01.2023

"""


from artcollector.sites import ExtArt
from artcollector.to_frm import to_txt


class ArticleCollection:
    """ Коллекция статей """

    def __init__(self, collection_name: str='Статьи') -> None:

        self.collection_name = collection_name

        self._collection_data = []

    def __iter__(self):
        return iter(self._collection_data)

    def __getitem__(self, value):
        return self._collection_data[value]

    def __len__(self):
        return len(self._collection_data)

    def load_from_urls(self, path_to_urls: str) -> int:
        """ Получает путь к файлу со ссылками,
        Извлекает данные статей по этим ссылкам,
        Добавляет их в коллекцию,
        Возвращает количество добавленных статей. """

        art_factor = ExtArt()
        size = len(self._collection_data)

        with open(path_to_urls, 'r', encoding='utf-8') as file_urls:
            urls = map(str.strip, file_urls.readlines())

        for url in urls:
            art = art_factor(url)
            self._collection_data.append(art)

        return len(self._collection_data) - size

    def to(self, frm: str='txt'):
        """ Конвертирует коллекцию в указанный формат. """

        formats = {
            'txt': to_txt
        }

        return formats[frm](self)
