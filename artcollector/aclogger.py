""" Настройка логгера для пакета artcollector """

from pathlib import Path
from logging import FileHandler, getLogger, DEBUG, Formatter, StreamHandler, ERROR
from locale import setlocale, LC_TIME

setlocale(LC_TIME, 'Russian_Russia.1251')

# Список модулей для которых требуется создание логгера.
loggers = [
    'art_collection',
    'sites',
    'to_frm'
]

formatter = Formatter(
    fmt='%(levelname)s\t%(asctime)s\t%(module)s\t%(message)s',
    datefmt='%d %B %Y, %H:%M:%S, %A'
)

ac_logger = getLogger('artcollector')
ach = StreamHandler()
ach.setFormatter(formatter)
ach.setLevel(ERROR)
ac_logger.addHandler(ach)

if not Path.joinpath(Path.cwd(), 'logs').exists():
    Path.mkdir(Path.joinpath(Path.cwd(), 'logs'))

for lgrs in loggers:
    log_file_handler = FileHandler(
        filename=Path.joinpath(Path.cwd(), 'logs', f'{lgrs}.log'),
        encoding='utf-8',
        mode='w' # Журналы перезаписываются каждый сеанс.
    )
    log_file_handler.setFormatter(formatter)
    log_file_handler.setLevel(DEBUG)
    log = getLogger(f'{ac_logger.name}.{lgrs}')
    log.addHandler(log_file_handler)
    log.setLevel(DEBUG)
