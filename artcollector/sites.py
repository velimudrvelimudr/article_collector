""" Модуль sites.
    Описание: Обеспечивает поддержку сайтов пакета artcollector.
    © Михаил Духонин
    13.01.2023 - 15.01.2023

"""

import re
from datetime import datetime
from locale import LC_TIME, setlocale
from logging import getLogger
from urllib.parse import unquote

import requests
from requests.exceptions import HTTPError, ReadTimeout
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

import artcollector.aclogger

log = getLogger(__name__)

class ExtractArticleData:
    """ Базовый класс, содержащий основную логику извлечения статей по ссылкам.
        Не предназначен для создания экземпляра.
        Работа с конкретными сайтами реализуется в потомках.

    """

    SOURCE_NAME = ''
    SOURCE_SITE = ''

    MAIN_FND = ''
    MAIN_SEL = ''
    MAIN_ATTRS = {}

    FRM = "%d.%m.%Y %H:%M"

    def __init__(self, link: str) -> None:

        self._link = link

        try:
            response = requests.get(self._link, timeout=10, headers={'User-Agent':
            f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            f'Chrome/106.0.0.0 YaBrowser/22.11.5.715 Yowser/2.5 Safari/537.36'})
        except ReadTimeout:
            log.fatal('На ссылке %s сработал таймауд', self._link, exc_info=True)
            raise

        try:
            response.raise_for_status()
        except HTTPError:
            log.fatal('Ссылка %s Битая. Код ошибки %s.', self._link, response.status_code,
            exc_info=True)
            raise

        raw_data = response.text

        self._html_tree = BeautifulSoup(raw_data, 'html.parser')

        if self.MAIN_FND:
            self._main_tree = self._html_tree.find(self.MAIN_FND, attrs=self.MAIN_ATTRS)
        elif self.MAIN_SEL:
            self._main_tree = self._html_tree.select(self.MAIN_SEL)[0]

        self._source_name = f'{self.SOURCE_NAME} ({self.SOURCE_SITE})'
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

    @staticmethod
    def link_processing(tag, links_list):
        """ Получает элемент страницыи список.
        Ищет внутри переданного элемента ссылки и добавляет в конце их текста URL в скобках.
        Добавляет полученные URL'ы в список links_list.
        Возвращает None.

        """

        if not isinstance(tag, Tag):
            return

        for lnk in tag.findAll('a'):
            link = lnk.get('href', False)
            if link:
                links_list.append(unquote(link))
                if lnk.string:
                    lnk.string += ' (' + unquote(link) + ')'
                else:
                    lnk.append(' (' + unquote(link) + ')')



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

            self.link_processing(content, self._links)

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

        for content in art_content:
            if isinstance(content, (NavigableString, Comment)) or content.get('class', False) == ['ads_single']:
                content.extract()
        for content in art_content:
            if isinstance(content, (NavigableString, Comment)) or content.get('class', False) == ['ads_single']:
                content.extract()

        for content in art_content:

            self.link_processing(content, self._links)

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

            self.link_processing(content, self._links)


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

class ExtractInoSMIArticle(ExtractArticleData):
    """ Извлечение статей с inosmi.ru. """

    SOURCE_NAME = 'ИноСМИ'
    SOURCE_SITE = 'inosmi.ru'

    MAIN_SEL = '#content'

    def _ext_date(self):
        date_tag = 'div'
        date_attrs = {'itemprop': 'datePublished'}
        date_frm = "%Y-%m-%dT%H:%M"

        source_date = self._main_tree.find(date_tag, attrs=date_attrs)
        date = datetime.strptime(source_date.getText(), date_frm)

        self._date = date

    def _ext_author(self):
        author_tag = 'div'
        author_attrs = {'class': 'article__authors'}

        author = self._main_tree.find(author_tag, attrs=author_attrs)

        self._author = author.get_text().strip()

    def _ext_headline(self):

        hl_tag = 'h1'

        headline = self._main_tree.find(hl_tag)

        self._headline = headline.get_text().strip()

    def _ext_text(self):

        txt_sel = 'div.article__body'
        source_text = self._main_tree.select(txt_sel)[0]
        text = ''

        for content in source_text.contents:
            if content.strings and content.name == 'div' and content.get('data-type', '') == 'text':
                self.link_processing(content, self._links)
                text += content.getText() + '\n'
            if content.strings and content.name == 'div' and content.get('data-type', '') == 'article':
                # Вставки отсылок к предыдущим статьям по теме.
                text += '\n' + content.select('a.article__article-link')[0].getText('\n', strip=True) + '\n'
                text += content.select('div.article__article-source')[0].getText(', ', strip=True) + ', '
                text += content.select('div.article__article-info')[0].getText(strip=True) + '\n'
                text += 'https://inosmi.ru' + content.select('a.article__article-link')[0]['href'] + '\n'*2
                self._links.append(content.select('a.article__article-link')[0]['href'])

        self._text = text.strip().replace('\n'*3, '\n'*2)


    def _extra_data(self):

        tags_tag = 'div'
        tags_attrs = {'itemprop': 'articleSection'}
        ann_tag = 'div'
        ann_attrs = {'class':'article__announce-text'}

        source_tags = self._main_tree.findAll(tags_tag, attrs=tags_attrs)
        source_ann = self._main_tree.find(ann_tag, attrs=ann_attrs)

        tags = [t.string for t in source_tags]
        annotation = source_ann.getText(strip=True)

        # Добавляем в список связанных ссылок ссылку на оригинал статьи.
        self._links.append(
            self._main_tree.find('div', attrs={'class':'article__info-original'}).find('a')['href']
        )

        self._info.update({
            'tags': tags,
            'annotation': annotation
            })


class ExtArt:
    """ Запускает нужный класс для загрузки статьи """

    SITE_CLASS = {
        'habr.com': ExtractHabrArticle,
        'naked-science.ru': ExtractNakedscienceArticle,
        'tass.ru': ExtractTassArticle,
        'inosmi.ru': ExtractInoSMIArticle
    }

    def __call__(self, link, *args, **kwds):

        source = re.search(r'https?://w?w?w?\.?([\w\.-]*\.\w{2,})/', link)

        if not source:
            log.warning('Некорректная ссылка %s', link)
            return

        if source [1]in self.SITE_CLASS:
            try:
                return self.SITE_CLASS[source[1]](link)
            except (HTTPError, ReadTimeout):
                log.warning('Не удалось загрузить %s', link, exc_info=True)
                return
        else:
            log.warning('Ресурс %s не поддерживается', source[1])
            return
