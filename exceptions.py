class NoNewInformation(Exception):
    """Новая информация о статусе отсутствует"""


class JSONException(Exception):
    """Ошибка преобразования данных JSON."""
    def __init__(self, error):
        message = f'Ошибка преобразования данных JSON: {error}'
        super().__init__(message)


class BadRequest(Exception):
    """Ошибка доступа к эндпоинту."""
    def __init__(self, response, endpoint, headers, params):
        message = (f'Ошибка при отправке запроса на {endpoint}: '
                   f'status_code - {response.status_code}, ',
                   f'reason - {response.reason}, ',
                   f'text - {response.text}, ',
                   f'headers - {headers}, ',
                   f'params - {params}, ',)
        super().__init__(message)


class DictKeyErrorException(KeyError):
    """Ошибка ключа словаря в ответе API."""
    def __init__(self, message):
        super().__init__(message)


class APIResponseTypeErrorException(TypeError):
    """Ошибка типа данных в ответе API."""
    def __init__(self, message):
        super().__init__(message)


class UnknownAPIException(Exception):
    """Ошибка при отправке запроса к API"""
    def __init__(self, endpoint, error):
        message = (f'Не опознанная ошибка при отправке запроса на {endpoint}:'
                   f' {error}')
        super().__init__(message)


class TelegramErrorException(Exception):
    """Ошибка при отправке сообщения телеграм"""
    def __init__(self, error):
        message = f'Ошибка при отправке сообщения телеграм: {error}'
        super().__init__(message)
