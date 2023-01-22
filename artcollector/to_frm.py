""" Модуль to_frm.
    Описание: Функции сохранения ArtCollection из пакета artcollector в различные форматы.
    © Михаил Духонин
    13.01.2023 - 15.01.2023

"""

from logging import getLogger

import artcollector.aclogger

log = getLogger(__name__)


def to_txt(collection):
    """ Конвертирует коллекцию статей в текстовый формат.

    collection: Коллекция статей.

    Возвращает: кортеж из оглавления выгрузки и текстов с полными заголовками.

    """

    if len(collection) == 0 :
        log.info('Пустая коллекция %s', collection.collection_name)
        return ('', '')

    new_line = '\n'
    toc = 'Содержание\n'
    body = 'Полные тексты\n'

    for art in collection:

        header = (f"{art['source']}, {art['date']}, "
            f"{f'{art.author}, ' if art.author else ''}{art.headline}{new_line}")

        toc += header

        body += (f"{new_line}###{new_line*2}{header}"
            f"{'Теги: ' + ', '.join(art['tags']) + new_line if art.info.get('tags', False) else ''}"
            f"{'Аннотация: ' + art['annotation'] + new_line if art.info.get('annotation', False) else ''}"
            f"{art.link}{new_line}{art.full_text}{new_line}"
            f"{f'Ссылки:{new_line}{new_line.join(art.links)}' if art.info.get('links', False) else ''}{new_line}")

    return toc, body
