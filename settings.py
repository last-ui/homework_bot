import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: int = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD: int = 60 * 10

ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

LOG_FORMAT_STRING = '%(asctime)s:%(levelname)s:%(name)s:%(lineno)d:%(message)s'
LOG_LEVEL = logging.INFO
LOG_OUTPUT = sys.stdout
