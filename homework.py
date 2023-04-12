import telegram
import time
import requests
from dotenv import load_dotenv
from os import getenv
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG,
                    filename='main.log',
                    filemode='w',
                    format='%(asctime)s [%(levelname)s] %(message)s, %(name)s')

PRACTICUM_TOKEN = getenv('HEADERS')
TELEGRAM_TOKEN = getenv('TOKEN')
TELEGRAM_CHAT_ID = getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка токенов."""
    error_status = True
    if PRACTICUM_TOKEN is None:
        logging.critical('Отсутствует токен Яндекс.Домашка')
        error_status = False
    if TELEGRAM_TOKEN is None:
        logging.critical('Отсутствует токен Telegram')
        error_status = False
    if TELEGRAM_CHAT_ID is None:
        logging.critical('Отсутствует ID Пользователя Telegram')
        error_status = False
    return error_status


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logging.error(error)
    except Exception as error:
        logging.ERROR(error)
    else:
        logging.debug('Письмо успешно отправлено.')


def get_api_answer(timestamp):
    """Получение списка работ."""
    payload = {'from_date': timestamp}
    answer: dict = {}
    try:

        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=payload)
        if response.status_code != requests.codes.ok:
            logging.ERROR('Request не вернул статус 200!')
        answer = response.json()
    except requests.ConnectTimeout as err:
        logging.ERROR(err)
    except requests.Timeout as err:
        logging.ERROR(err)
    except requests.ConnectionError as err:
        logging.ERROR(err)
    except requests.JSONDecodeError as err:
        logging.ERROR(err)

    return answer


def check_response(response):
    """Проверка статуса Домашки."""
    try:
        if not isinstance(response, dict):
            raise TypeError
        homeworks = response['homeworks']
        if not isinstance(homeworks, list):
            raise TypeError
    except KeyError as error:
        logging.CRITICAL(response['error'], error)
    except TypeError as error:
        logging.CRITICAL(error)
    return homeworks


def parse_status(homework):
    """Создание ответа изменения статуса работы в Telegram."""
    try:
        homework_name = homework['homework_name']
        if homework['status'] in HOMEWORK_VERDICTS:
            verdict = HOMEWORK_VERDICTS[homework['status']]
    except KeyError as err:
        logging.error(f'Отсутсвует ключ {err}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        timestamp = int(time.time())
        while True:
            try:
                response = get_api_answer(timestamp=timestamp)
                checked_response = check_response(response=response)
                message = parse_status(checked_response[0])
                send_message(bot, message)
            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
            time.sleep(600)


if __name__ == '__main__':
    main()
