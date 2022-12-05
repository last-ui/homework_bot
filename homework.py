"""
Bot-ассистент проверки домашних заданий Практикум.Домашка.
Все настройки модуля в файле settings.py.
Не меняйте код внутри данного файла.
Периодичность запросов к API задается константой RETRY_PERIOD.
"""
import http
import logging
import requests
import sys
import telegram
import time

from json.decoder import JSONDecodeError

import exceptions as ex
from settings import (ENDPOINT, HEADERS, HOMEWORK_VERDICTS,
                      LOG_FORMAT_STRING, LOG_LEVEL, LOG_OUTPUT,
                      PRACTICUM_TOKEN, RETRY_PERIOD, TELEGRAM_TOKEN,
                      TELEGRAM_CHAT_ID)


def check_tokens() -> bool:
    """Проверка наличия токенов и id телеграм чата."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в телеграм канал."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения телеграм: {error}')
        raise ex.TelegramErrorException(error)
    else:
        logging.debug(f'Сообщение: "{message}" успешно отправлено')


def get_api_answer(timestamp: int) -> dict:
    """Отправка запроса на сервер и получение ответа."""
    payload: dict = {'from_date': timestamp}
    try:
        logging.debug(f'Отправлен запрос на {ENDPOINT}')
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        homework_statuses = response.json()
    except JSONDecodeError as error:
        raise ex.JSONException(error)
    except Exception as error:
        raise ex.UnknownAPIException(ENDPOINT, error)
    else:
        logging.debug(f'Ответ с {ENDPOINT} получен')
        if response.status_code != http.HTTPStatus.OK:
            raise ex.BadRequest(response, ENDPOINT, HEADERS, payload)
        return homework_statuses


def check_response(response: dict) -> tuple:
    """Проверка API-ответа на соответствие требований документации."""
    logging.debug('Старт проверки ответа сервера')
    if not isinstance(response, dict):
        message: str = 'Ошибка: ответ сервера должен содержать тип данных dict'
        raise ex.APIResponseTypeErrorException(message)
    if 'homeworks' not in response.keys():
        message: str = ('Ошибка: в словаре ответа сервера отсутствует ключ'
                        ' "homeworks"')
        raise ex.DictKeyErrorException(message)
    if 'current_date' not in response.keys():
        message: str = ('Ошибка: в словаре ответа сервера отсутствует ключ'
                        ' "current_date"')
        raise ex.DictKeyErrorException(message)
    homeworks = response.get('homeworks')
    current_date = response.get('current_date')
    if not isinstance(homeworks, list):
        message: str = 'Ошибка: тип данных объекта "homeworks" не list'
        raise ex.APIResponseTypeErrorException(message)
    if not isinstance(current_date, int):
        message: str = 'Ошибка: тип данных объекта "current_date" не int'
        raise ex.APIResponseTypeErrorException(message)
    logging.debug('Проверка ответа успешно выполнена')
    return homeworks, current_date


def parse_status(homework: dict) -> str:
    """Парсинг статуса домашней работы."""
    if not isinstance(homework, dict):
        message: str = 'Ошибка: у объекта "homework" тип данных  не dict'
        raise ex.DictKeyErrorException(message)
    homework_name: str = homework.get('homework_name')
    status: str = homework.get('status')
    if not homework_name:
        message: str = ('Ошибка: в объекте homework отсутствует ключ'
                        ' "homework_name"')
        raise ex.DictKeyErrorException(message)
    if not status:
        message: str = ('Ошибка: в объекте homework отсутствует ключ'
                        ' "status"')
        raise ex.DictKeyErrorException(message)
    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        message: str = ('Ошибка: в словаре HOMEWORK_VERDICTS отсутствует ключ'
                        f' "{status}"')
        raise ex.DictKeyErrorException(message)
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
    if not check_tokens():
        message = ('Отсутствует обязательная переменная окружения, работа '
                   'модуля не возможна')
        logging.critical(message)
        sys.exit(message)

    bot: telegram.Bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp: int = int(time.time())
    old_message: str = ''
    while True:
        try:
            homework_statuses: dict = get_api_answer(timestamp)
            homeworks, timestamp = check_response(homework_statuses)
            if not homeworks or not timestamp:
                raise ex.NoNewInformation
            message: str = parse_status(homeworks[0])
            if message != old_message:
                send_message(bot, message)
                old_message = message
        except ex.NoNewInformation:
            logging.debug('Новая информация о статусе отсутствует')
        except Exception as error:
            message: str = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=error)
            if message != old_message:
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format=LOG_FORMAT_STRING,
        level=LOG_LEVEL,
        handlers=[logging.StreamHandler(stream=LOG_OUTPUT)]
    )
    main()
