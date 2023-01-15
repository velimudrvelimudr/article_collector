""" Коллекция статей.
    Описание:
        Класс ArtCollection, Представляющий коллекцию статей.
    © Михаил Духонин
    13.01.2023 - 15.01.2023

"""

from logging import getLogger

import artcollector.aclogger
from artcollector.sites import ExtArt
from artcollector.to_frm import to_txt

log = getLogger(__name__)

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

        try:
            with open(path_to_urls, 'r', encoding='utf-8') as file_urls:
                urls = map(str.strip, file_urls.readlines())
        except (FileNotFoundError, FileExistsError):
            log.fatal('Файл %s не существует или не найден', path_to_urls, exc_info=True)
            return len(self._collection_data) - size

        for url in urls:
            art = art_factor(url)
            if art:
                self._collection_data.append(art)
            else:
                log.warning('Статья по ссылке %s не выгрузилась', url)

        return len(self._collection_data) - size

    def to(self, frm: str='txt'):
        """ Конвертирует коллекцию в указанный формат. """

        formats = {
            'txt': to_txt
        }

        if frm in formats:
            return formats[frm](self)
        else:
            log.error('Неизвестный формат %s', frm)
            return
