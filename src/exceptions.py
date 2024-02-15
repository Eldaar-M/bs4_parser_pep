class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""


class ParserLoadingPageException(Exception):
    """Вызывается, при ошибке загрузки границы."""
