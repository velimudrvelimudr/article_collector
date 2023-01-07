""" Демонстрация работы сборщика статей. """

from artcollector.art_collector import ExtArt

with open('demo_urls.txt', 'r', encoding='utf-8') as file_urls:
    URLS = [u.strip() for u in file_urls.readlines()]

def article_export_to_text(urls: list) -> str:
    """ Получает список ссылок, извлекает по ним данные статей и
    возвращает их в виде единого текстового массива.

    """

    art_factor = ExtArt()

    new_line = '\n'
    toc = 'Содержание\n'
    body = 'Полные тексты\n'

    for url in urls:

        art = art_factor(url)

        header = (f"{art['source']}, {art['date']}, "
            f"{f'{art.author}, ' if art.info.get('author', False) else ''}{art.headline}{new_line}")

        toc += header

        body += (f"{new_line}###{new_line*2}{header}"
            f"{'Теги: ' + ', '.join(art['tags']) + new_line if art.info.get('tags', False) else ''}"
            f"{'Аннотация: ' + art['annotation'] + new_line if art.info.get('annotation', False) else ''}"
            f"{art.link}{new_line}{art.full_text}{new_line}"
            f"{f'Ссылки:{new_line}{new_line.join(art.links)}' if art.info.get('links', False) else ''}{new_line}")

    return f"{toc}{new_line}{body}"


if __name__ == '__main__':

    with open('example.txt', 'w', encoding='utf-8', newline='') as result:
        result.write(article_export_to_text(URLS))
