from requests import RequestException

from exceptions import ParserFindTagException

from bs4 import BeautifulSoup

ERROR_PAGE_INFO = (
    'Возникла ошибка при загрузке страницы {url}'
    'Ошибка: {exception}'
)
ERROR_MESSAGE = 'Не найден тег {tag} {attrs}'


def get_response(session, url, format='utf-8'):
    try:
        response = session.get(url)
        response.encoding = format
    except RequestException as exception:
        raise ConnectionError(ERROR_PAGE_INFO.format(
            url=url,
            exception=exception
            )
        )
    return response


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(
            ERROR_MESSAGE.format(
                tag=tag, attrs=attrs
            ))
    return searched_tag


def soup_create(session, url, features='lxml'):
    return BeautifulSoup(get_response(session, url).text, features)
