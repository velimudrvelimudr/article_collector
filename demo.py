""" Демонстрация работы сборщика статей. """

from artcollector.art_collection import ArticleCollection


if __name__ == '__main__':

    ac = ArticleCollection('Тестовая коллекция')
    print(
        'Коллекция: ' + ac.collection_name,
    'Добавлено ' + str(ac.load_from_urls('demo_urls.txt')) + ' статей',
        'В коллекции ' + str(len(ac)) + ' статей',
        sep='\n'
    )

    toc, body = ac.to('txt')

    with open('example.txt', 'w', encoding='utf-8', newline='') as result:
        result.write(ac.collection_name + '\n' * 2 + toc + '\n' + body)
