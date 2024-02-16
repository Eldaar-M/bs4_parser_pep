from collections import defaultdict
import logging
import re
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    BASE_DIR,
    DOWNLOADS,
    EXPECTED_STATUS,
    MAIN_DOC_URL,
    PEP_DOCS_URL
)
from exceptions import ParserFindTagException
from outputs import control_output
from utils import find_tag, soup_create

ARCHIVE_SAVE_INFO_PHRASE = 'Архив был загружен и сохранён: {archive_path}'
ARGUMENTS_PHRASE = 'Аргументы командной строки: {args}'
ERROR_PHRASE = 'В ходе работы парсера возникла ошибка:'
FIND_TAG_PHRASE = 'Ничего не нашлось'
INCORRECT_STATUS_PHRASE = (
    'В списке есть неверно указанный статус: {preview_status}'
    'В строке: {pep}'
)
MISMATCHED_STATUS_PHRASE = (
    'Несовпадающие статусы: {pep_url}'
    'Статус в карточке: {status_card}'
    'Статус в списке: {status_list}'
)
NO_STATUS_PHRASE = 'На странице PEP {pep_url} нет статуса'
PARSER_START_PHRASE = 'Парсер запущен!'
PARSER_FINISH_PHRASE = 'Парсер завершил работу.'
URL_ERROR = 'Ссылка: {url} недоступна'


def whats_new(session):
    whats_new_url = urljoin(
        MAIN_DOC_URL,
        'whatsnew/'
    )
    sections_by_python = soup_create(
        session,
        whats_new_url
    ).select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1 > a'
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    logs = []

    for section in tqdm(sections_by_python):
        href = section['href']
        version_link = urljoin(whats_new_url, href)
        soup = soup_create(session, version_link)
        if not soup:
            logs.append(URL_ERROR.format(url=version_link))
            continue
        results.append(
            (version_link, find_tag(soup, 'h1').text,
                find_tag(soup, 'dl').text.replace('\n', ' '))
        )
    if logs:
        logging.error(logs)
    return results


def latest_versions(session):
    soup = soup_create(session, MAIN_DOC_URL)
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise ParserFindTagException(FIND_TAG_PHRASE)
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text = a_tag.text
        text_match = re.search(pattern, text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((a_tag['href'], version, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = soup_create(session, downloads_url)
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag,
        'a',
        {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / DOWNLOADS
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(ARCHIVE_SAVE_INFO_PHRASE.format(archive_path=archive_path))


def pep(session):
    soup = soup_create(session, PEP_DOCS_URL)
    numerical_index = find_tag(soup, 'section', {'id': 'numerical-index'})
    tbody = find_tag(numerical_index, 'tbody')
    tr = tbody.find_all('tr')
    status_count = defaultdict(int)
    logs = []
    for pep in tqdm(tr):
        preview_status = pep.find('td').text[1:]
        if preview_status in EXPECTED_STATUS:
            status_list = EXPECTED_STATUS[preview_status]
        else:
            status_list = []
            logs.append(INCORRECT_STATUS_PHRASE.format(
                 preview_status=preview_status,
                 pep=pep
                ))
        href = pep.find('a')['href']
        pep_url = urljoin(PEP_DOCS_URL, href)
        soup = soup_create(session, pep_url)
        if not soup:
            logs.append(URL_ERROR.format(url=pep_url))
            continue
        dl = find_tag(soup, 'dl', {'class': 'rfc2822 field-list simple'})
        status = dl.find(string='Status')
        if status:
            status_parent = status.find_parent()
            status_card = status_parent.next_sibling.next_sibling.string
            if status_card not in status_list:
                logs.append(
                    MISMATCHED_STATUS_PHRASE.format(
                     pep_url=pep_url,
                     status_card=status_card,
                     status_list=status_list
                    )
                )
            status_count[status_card] += 1
        else:
            logs.append(
                    NO_STATUS_PHRASE.format(
                     pep_url=pep_url,
                    )
                )
            continue
    if logs:
        logging.error(logs)
    return [
        ('Статус', 'Количество'),
        *status_count.items(),
        ('Всего', sum(status_count.values())),
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info(PARSER_START_PHRASE)
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(ARGUMENTS_PHRASE.format(args=args))
    try:
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception as exception:
        logging.exception(
            msg=f'{ERROR_PHRASE} {exception}',
            stack_info=True
        )
    logging.info(PARSER_FINISH_PHRASE)


if __name__ == '__main__':
    main()
