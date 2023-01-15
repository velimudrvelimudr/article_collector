""" Демонстрация работы сборщика статей. """

from artcollector.art_collection import ArticleCollection


if __name__ == '__main__':

    ac = ArticleCollection('Тестовая коллекция')
    print('Коллекция: ' + ac.collection_name)
    toc, body = ac.to('txt')
    print('Добавлено ' + str(ac.load_from_urls('demo_urls.txt')) + ' статей')
    print('В коллекции ' + str(len(ac)) + ' статей')

    toc, body = ac.to('txt')
    kva = ac.to('kva')

    with open('example.txt', 'w', encoding='utf-8', newline='') as result:
        result.write(ac.collection_name + '\n' * 2 + toc + '\n' + body)
