""" Демонстрация работы сборщика статей. """

from artcollector.art_collection import ArticleCollection


if __name__ == '__main__':

    ac = ArticleCollection('Тестовая коллекция')

    ac.load_from_urls('demo_urls.txt')

    toc, body = ac.to('txt')

    with open('example.txt', 'w', encoding='utf-8', newline='') as result:
        result.write(ac.collection_name + '\n' * 2 + toc + '\n' + body)
