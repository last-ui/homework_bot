class NoImportantInformation(Exception):
    """Несущественный класс"""


class JSONException(NoImportantInformation):
    """Ошибка преобразования данных JSON."""


class BadRequest(Exception):
    """Ошибка доступа к эндпоинту."""


class DictKeyErrorException(NoImportantInformation):
    """Ошибка ключа словаря в ответе API."""


class APIResponseTypeErrorException(TypeError):
    """Ошибка типа данных в ответе API."""


class UnknownAPIException(Exception):
    """Ошибка при отправке запроса к API"""
