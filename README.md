# Проект парсинга pep
## Технологии

- Python
- BeautifulSoup
- requests_cache
- tqdm
- prettytable

## Клонирование проекта с GitHub на сервер:
```
git clone git@github.com:Eldaar-M/bs4_parser_pep.git
```
## Cмените папку на src
```
cd src/
```
## Как использовать парсеры:
- whats-new   
Парсер выводящий список изменений в python.
```
python main.py whats-new [аргументы]
```
- latest_versions
Парсер выводящий список версий python и ссылки на их документацию.
```
python main.py latest-versions [аргументы]
```
- download   
Парсер скачивающий zip архив с документацией python в pdf формате.
```
python main.py download [аргументы]
```
- pep
Парсер выводящий список статусов документов pep
и количество документов в каждом статусе. 
```
python main.py pep [аргументы]
```
### Аргументы
Есть возможность указывать аргументы для изменения работы программы:   
- -h, --help
Общая информация о командах.
```
python main.py -h
```
- -c, --clear-cache
Очистка кеша перед выполнением парсинга.
```
python main.py [вариант парсера] -c
```
- -o {pretty,file}, --output {pretty,file}   
Дополнительные способы вывода данных   
pretty - выводит данные в командной строке в таблице   
file - сохраняет информацию в формате csv в папке ./results/
```
python main.py [вариант парсера] -o file
```
### Автор 
[Эльдар Магомедов](https://github.com/Eldaar-M)