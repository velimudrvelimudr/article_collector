
"""
    Сборщик статей
    Описание:
        Набор инструментов для загрузки статей с поддерживаемых сайтов и манипуляции с ними.
    Версия 0.3
    © Михаил Духонин
    22.12.2022 - 12.01.2023

"""

import re
from datetime import datetime
from locale import LC_TIME, setlocale
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup, Comment, NavigableString


class ExtractArticleData:
    """ Извлекает данные статьи по ссылке.

    """

    SOURCE_NAME = ''
    SOURCE_SITE = ''
    SOURCE_FULLNAME = ''

    MAIN_FND = ''
    MAIN_SEL = ''
    MAIN_ATTRS = {}

    FRM = "%d.%m.%Y %H:%M"

    def __init__(self, link: str) -> None:

        self._link = link

        response = requests.get(self._link, timeout=10, headers={'User-Agent':
        f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        f'Chrome/106.0.0.0 YaBrowser/22.11.5.715 Yowser/2.5 Safari/537.36'})

        response.raise_for_status()
        raw_data = response.text

        self._html_tree = BeautifulSoup(raw_data, 'html.parser')

        if self.MAIN_FND:
            self._main_tree = self._html_tree.find(self.MAIN_FND, attrs=self.MAIN_ATTRS)
        elif self.MAIN_SEL:
            self._main_tree = self._html_tree.select(self.MAIN_SEL)[0]

        self._source_name = f"{self.SOURCE_NAME} ({self.SOURCE_SITE})"
        self._date = None
        self._author = None
        self._headline = None
        self._text = None
        self._info = None
        self._links = []

        self._ext_date()
        self._ext_author()
        self._ext_headline()
        self._ext_text()
        self._get_info()
        self._extra_data()

    def __getitem__(self, key: str):
        return self._info[key]

    def __str__(self) -> str:
        return (f"{self.source_name}, {self.date} "
        f"{self.headline} <Полный текст> {self.link}")

    def _ext_date(self):
        pass

    def _ext_author(self):
        pass

    def _ext_headline(self):
        pass

    def _ext_text(self):
        pass

    def _get_info(self):
        self._info = {
            'source': self.source_name,
            'date': self.date,
            'author': self.author,
            'headline': self.headline,
            'link': self.link,
            'text': self.full_text,
            'links': self._links
        }

    def _extra_data(self):
        pass

    @property
    def date(self):
        """ Возвращает дату """

        return self._date.strftime(self.FRM)

    @property
    def source_name(self):
        """ Возвращает полное имя источника """

        return self._source_name

    @property
    def link(self):
        """ Возвращает ссылку на статью """

        return self._link

    @property
    def author(self):
        """ Возвращает автора статьи (если имеется) """

        return self._author

    @property
    def headline(self):
        """ Возвращает заголовок статьи """

        return self._headline

    @property
    def full_text(self):
        """ Возвращает полный текст статьи """

        return self._text

    @property
    def info(self) -> dict:
        """ Возвращает полную информацию о статье в виде словаря, включая дополнительные данные. """

        return self._info

    @property
    def links(self):
        """ Возвращает список ссылок из статьи.
        Предполагается использовать при реализации скрапера. """

        return self._links


class ExtractHabrArticle(ExtractArticleData):
    """ Извлечение статей с Хабра """

    SOURCE_NAME = 'Хабр'
    SOURCE_SITE = 'habr.com'
    MAIN_FND = 'article'

    def _ext_date(self):

        date_tag = 'time'
        date_attr = 'datetime'
        date_frm = "%Y-%m-%dT%H:%M:%S.%Z"

        source_date = self._main_tree.find(date_tag)[date_attr]
        date = datetime.strptime(f"{source_date[0:-5]}.UTC", date_frm)
        self._date = date

    def _ext_author(self):

        author_tag = 'span'
        author_attrs = {"class": "tm-user-info__user"}

        author = self._main_tree.find(author_tag, attrs=author_attrs)

        self._author = author.get_text().strip()

    def _ext_headline(self):

        hl_tag = 'h1'

        headline = self._main_tree.find(hl_tag)

        self._headline = headline.get_text().strip()

    def _ext_text(self):

        txt_sel = '#post-content-body > div:nth-child(1) > div > div'
        source_text = self._main_tree.select(txt_sel)[0]
        text = ''

        for content in source_text.contents:

            for lnk in content.findAll('a'):
                link = lnk.get('href', False)
                if link:
                    self._links.append(unquote(link))
                    if lnk.string:
                        lnk.string += ' (' + unquote(link) + ')'
                    else:
                        lnk.append(' (' + unquote(link) + ')')

            if content.name == 'br':
                content.decompose()

            for br in content.findAll('br'):
                if br.name == 'br' and br.next_element.name == 'br':
                    br.decompose()
                else:
                    br.replaceWith('\n')

            match content.name:
                case 'pre' | 'code':
                    text += '\n' + content.getText() + '\n'*2
                case 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6':
                    text += '\n' + content.getText(strip=True) + '\n'*2
                case 'ol' | 'ul':
                    text += '\n* ' + content.getText('\n* ', strip=True) + '\n' * 2
                case _:
                    if content.strings:
                        text += content.getText().strip() + '\n'

        self._text = text.strip().replace('\n\r\n', '\n').replace('\n'*3, '\n'*2)

    def _extra_data(self):

        tags_attrs = {'class': "tm-separated-list__list"}

        source_tags = self._main_tree.find(attrs=tags_attrs)
        tags = source_tags.getText('\n', strip=True).split('\n')

        self._info.update({'tags': tags})


class ExtractNakedscienceArticle(ExtractArticleData):
    """ Извлечение статей с Naked Science """

    SOURCE_NAME = 'Naked Science'
    SOURCE_SITE = 'naked-science.ru'
    MAIN_SEL = '.content'

    def _ext_date(self):

        date_attrs = {"class": "echo_date"}
        date_attr = 'data-published'
        date_frm = "%Y-%m-%dT%H:%M:%S%z"

        source_date = self._main_tree.find(attrs=date_attrs)[date_attr]
        date = datetime.strptime(source_date, date_frm)

        self._date = date

    def _ext_author(self):

        author_tag = 'div'
        author_attrs = {"class": "meta-item_author"}

        author = self._main_tree.find(author_tag, attrs=author_attrs)

        self._author = author.get_text().strip()

    def _ext_headline(self):

        hl_tag = 'h1'

        headline = self._main_tree.find(hl_tag)

        self._headline = headline.get_text().strip()

    def _ext_text(self):

        txt_sel = '.body'

        source_text = self._main_tree.select(txt_sel)[0]
        text = ''

        art_content = source_text.contents

        [content.extract() for content in art_content
        if isinstance(content, (NavigableString, Comment))
        or content.get('class', False) == ['ads_single']]
        [content.extract() for content in art_content
        if isinstance(content, (NavigableString, Comment))
        or content.get('class', False) == ['ads_single']]

        for content in art_content:

            for lnk in content.findAll('a'):
                link = lnk.get('href', False)
                if link:
                    self._links.append(unquote(link))
                    if lnk.string:
                        lnk.string += ' (' + unquote(link) + ')'
                    else:
                        lnk.append(' (' + unquote(link) + ')')

            match content.name:
                case 'pre' | 'code':
                    text += '\n' + content.getText() + '\n'*2
                case 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6':
                    text += '\n' + content.getText(strip=True) + '\n'*2
                case 'ol' | 'ul':
                    text += '\n* ' + content.getText('\n* ', strip=True) + '\n' * 2
                case 'div':
                    if 'other-news-block' in content['class']:
                        text += content.getText('\n', strip=True) + '\n'
                    # else:
                        # text += content.getText() + '\n'
                case _:
                    if content.strings:
                        text += content.getText() + '\n'

        self._text = text.strip().replace('\n\r\n', '\n').replace('\n'*3, '\n'*2)

    def _extra_data(self):

        tags_attr = '.terms-items'
        ann_attr = '.post-lead'

        source_tags = self._main_tree.select(tags_attr)[0]
        source_ann = self._main_tree.select(ann_attr)[0]

        tags = source_tags.getText('\n', strip=True).replace('# ', '').split('\n')
        annotation = source_ann.getText(strip=True)

        self._info.update({
            'tags': tags,
            'annotation': annotation
            })


class ExtractTassArticle(ExtractArticleData):
    """ Извлечение статей с ТАСС """

    SOURCE_NAME = 'Тасс'
    SOURCE_SITE = 'tass.ru'
    MAIN_FND = 'main'

    def _ext_date(self):

        date_tag = 'div'
        date_attrs = {"class": [
            'ds_ext_marker-kFsBk',
            'ds_ext_marker--font_weight_medium-wX2ql',
            'ds_ext_marker--color_secondary-z2ssC'
            ]}

        date_frm = "%d %b %Y %H:%M%z"

        source_date = self._main_tree.find(date_tag, attrs=date_attrs)

        # Приводим дату в парсибельный вид.
        date_list = source_date.getText(strip=True).replace('\xa0', ' ').split(' ')
        date_list[1] = date_list[1][:3]
        if not re.fullmatch('\d{4},', date_list[2]):
            date_list.insert(2, str(datetime.now().year))
        else:
            date_list[2] = date_list[2][:-1] if date_list[2][-1] == ',' else date_list[2]
        date_list[-1] += '+03:00'

        # Поскольку дата по умолчанию в английском формате, а на сайте - по-русски,
        # приходится менять локаль, сохраняя исходную, а затем её восстанавливать.

        cur_format = setlocale(LC_TIME)
        setlocale(LC_TIME, 'Russian_Russia.1251')
        date = datetime.strptime(' '.join(date_list), date_frm)
        self._date = date
        setlocale(LC_TIME, cur_format)

    def _ext_headline(self):

        hl_tag = 'h1'

        headline = self._main_tree.find(hl_tag)

        self._headline = headline.get_text().strip()

    def _ext_text(self):

        txt_tag = 'article'
        source_text = self._main_tree.find(txt_tag)
        text = ''

        for content in source_text.contents:

            for lnk in content.findAll('a'):
                link = lnk.get('href', False)
                if link:
                    self._links.append(unquote(link))
                    if lnk.string:
                        lnk.string += ' (' + unquote(link) + ')'
                    else:
                        lnk.append(' (' + unquote(link) + ')')

            match content.name:
                case 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6':
                    text += '\n' + content.getText(strip=True) + '\n'*2
                case 'ol' | 'ul':
                    text += '\n* ' + content.getText('\n* ', strip=True) + '\n' * 2
                case _:
                    if content.strings:
                        text += content.getText() + '\n'

        self._text = text.strip().replace('\n\r\n', '\n').replace('\n'*3, '\n'*2)

    def _extra_data(self):

        tags_tag = 'a'
        tags_attrs = {"class": "Tags_tag__tRSPs"}

        source_tags = self._main_tree.findAll(tags_tag, attrs=tags_attrs)
        tags = [t.string for t in source_tags]

        self._info.update({'tags': tags})


class ExtArt:
    """ Запускает нужный класс для загрузки статьи """

    SITE_CLASS = {
        'habr.com': ExtractHabrArticle,
        'naked-science.ru': ExtractNakedscienceArticle,
        'tass.ru': ExtractTassArticle
    }

    def __call__(self, link, *args, **kwds):
        source = re.search(r'https?://w?w?w?\.?([\w\.-]*\.\w{2,})/', link)[1]
        return ExtArt.SITE_CLASS[source](link)

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

    def to(self, frm: str='txt') -> str:
        """ возвращает коллекцию в указанном формате. """

        match frm:
            case 'txt':
                return to_txt(self)
            case _:
                print('Неизвестный формат')

def to_txt(collection: ArticleCollection) -> tuple:
    """ Конвертирует коллекцию статей в текстовый формат. """

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
