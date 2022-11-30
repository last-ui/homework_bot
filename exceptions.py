class TokensErrorException(Exception):
    """Ошибка доступности токенов."""


class BadRequest(Exception):
    """Ошибка доступа к эндпоинту."""


class DictKeyErrorException(KeyError):
    """Ошибка ключа словаря в ответе API."""


class APIResponseTypeErrorException(TypeError):
    """Ошибка типа данных в ответе API."""


class MainException(Exception):
    """Ошибка главного модуля."""


class UnknownAPIException(Exception):
    """Неопознанная ошибка при отправке запроса к API"""
