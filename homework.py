"""
Bot-ассистент проверки домашних заданий Практикум.Домашка.
Все настройки модуля в файле settings.py.
Не меняйте код внутри данного файла.
Периодичность запросов к API задается константой RETRY_PERIOD.
"""

import http
import logging
import requests
import telegram
import time


from json.decoder import JSONDecodeError

from settings import (ENDPOINT, HOMEWORK_VERDICTS,
                      LOG_FORMAT_STRING, LOG_LEVEL, LOG_OUTPUT,
                      PRACTICUM_TOKEN, RETRY_PERIOD, TELEGRAM_TOKEN,
                      TELEGRAM_CHAT_ID)
import exceptions as ex


HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logger = logging.getLogger(__name__)
sh = logging.StreamHandler(stream=LOG_OUTPUT)
formatter = logging.Formatter(LOG_FORMAT_STRING)
sh.setFormatter(formatter)
sh.setLevel(LOG_LEVEL)
logger.addHandler(sh)


def check_tokens() -> bool:
    """Проверка наличия токенов и id телеграм чата."""
    env_var: tuple = (
        'PRACTICUM_TOKEN',
        'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID',
    )
    for var in env_var:
        if not globals()[var]:
            message = (f'Отсутствует переменная окружения {var}, '
                       'работа модуля не возможна')
            logger.critical(message)
            raise ex.TokensErrorException(message)
    return True


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в телеграм канал."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение: {message[:10]}... успешно отправлено')
    except telegram.TelegramError as error:
        logger.error(f'Ошибка при отправке сообщения телеграм: {error}')


def get_api_answer(timestamp: int) -> dict:
    """Отправка запроса на сервер и получение ответа."""
    payload: dict = {'from_date': timestamp}
    try:
        logger.debug(f'Отправлен запрос на {ENDPOINT}')
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.exceptions.Timeout as error:
        logger.error(f'Превышение таймаута ожидания ответа: {error}')
    except requests.exceptions.ConnectionError as error:
        logger.error(f'Ошибка подключения к удаленному серверу: {error}')
    except requests.exceptions.RequestException as error:
        logger.error(f'Ошибка при получении ответа с сервера: {error}')
    except Exception as error:
        message = (f'Неопознанная ошибка при отправке запроса на {ENDPOINT}:'
                   f' {error}')
        logger.error(message)
        raise ex.UnknownAPIException(message)
    else:
        logger.debug(f'Ответ с {ENDPOINT} получен')
        if response.status_code != http.HTTPStatus.OK:
            message = (f'Ошибка доступа к эндпоинту {ENDPOINT}, '
                       f'код ответа: {response.status_code}')
            logger.error(message)
            raise ex.BadRequest(message)
        try:
            homework_statuses = response.json()
        except JSONDecodeError as error:
            logger.error(f'Ошибка преобразования данных JSON: {error}')
        else:
            return homework_statuses


def check_response(response: dict) -> tuple:
    """Проверка API-ответа на соответствие требований документации."""
    if not isinstance(response, dict):
        message: str = 'Ошибка: ответ сервера должен содержать тип данных dict'
        logger.error(message)
        raise ex.APIResponseTypeErrorException(message)

    if 'homeworks' not in response.keys():
        message: str = ('Ошибка: в словаре ответа сервера отсутствует ключ'
                        ' "homeworks"')
        logger.error(message)
        raise ex.DictKeyErrorException(message)

    if 'current_date' not in response.keys():
        message: str = ('Ошибка: в словаре ответа сервера отсутствует ключ'
                        ' "current_date"')
        logger.error(message)
        raise ex.DictKeyErrorException(message)

    if not isinstance(response['homeworks'], list):
        message: str = 'Ошибка: тип данных объекта "homeworks" не list'
        logger.error(message)
        raise ex.APIResponseTypeErrorException(message)

    if not isinstance(response['current_date'], int):
        message: str = 'Ошибка: тип данных объекта "current_date" не int'
        logger.error(message)
        raise ex.APIResponseTypeErrorException(message)

    return response['homeworks'], response['current_date']


def parse_status(homework: dict) -> str:
    """Парсинг статуса домашней работы."""
    if not isinstance(homework, dict):
        message: str = 'Ошибка: у объекта "homework" тип данных  не dict'
        logger.error(message)
        raise ex.DictKeyErrorException(message)

    if 'homework_name' not in homework.keys():
        message: str = ('Ошибка: в объекте homework отсутствует ключ'
                        ' "homework_name"')
        logger.error(message)
        raise ex.DictKeyErrorException(message)

    if 'status' not in homework.keys():
        message: str = ('Ошибка: в объекте homework отсутствует ключ'
                        ' "status"')
        logger.error(message)
        raise ex.DictKeyErrorException(message)

    homework_name: str = homework.get('homework_name')
    status: str = homework.get('status')
    if status not in HOMEWORK_VERDICTS.keys():
        message: str = ('Ошибка: в словаре HOMEWORK_VERDICTS отсутствует ключ'
                        f' "{status}"')
        logger.error(message)
        raise ex.DictKeyErrorException(message)

    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """
    Основная логика работы бота.
    1. Проверка доступности обязательных переменных окружения check_tokens().
    2. Запрос к API get_api_answer().
    3. Проверка ответа на корректность данных check_response().
    4. При наличии корректных данных в ответе парсинг статуса parse_status().
    5. Отправка сообщений в Telegram send_message().
    6. Пауза RETRY_PERIOD и возврат к началу цикла.
    """
    if check_tokens():
        bot: telegram.Bot = telegram.Bot(token=TELEGRAM_TOKEN)
        timestamp: int = int(time.time()) - RETRY_PERIOD
        old_message: str = ''
        while True:
            try:
                homework_statuses: dict = get_api_answer(timestamp)
            except Exception as error:
                message: str = f'Сбой в работе программы: {error}'
                logger.error(message)
                send_message(bot, message)
                raise ex.MainException()
            else:
                if check_response(homework_statuses):
                    homeworks, timestamp = check_response(homework_statuses)
                    for homework in homeworks:
                        message: str = parse_status(homework)
                        if message and message != old_message:
                            send_message(bot, message)
                            old_message = message
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
