import telegram
import time
import requests
from dotenv import load_dotenv
from os import getenv
import logging
from settings import ENDPOINT, HOMEWORK_VERDICTS, RETRY_PERIOD

load_dotenv()

logging.basicConfig(level=logging.DEBUG,
                    filename='main.log',
                    filemode='w',
                    format='%(asctime)s [%(levelname)s] %(message)s, %(name)s')

logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)
PRACTICUM_TOKEN = getenv('HEADERS')
TELEGRAM_TOKEN = getenv('TOKEN')
TELEGRAM_CHAT_ID = getenv('TELEGRAM_CHAT_ID')

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def check_tokens():
    """Проверка токенов."""
    tokens = {'токен Яндекс.Домашка': PRACTICUM_TOKEN,
              'токен Telegram': TELEGRAM_TOKEN,
              'ID пользователя Telegram': TELEGRAM_CHAT_ID}
    for name, token in tokens.items():
        if token is None:
            logger.critical(f'Отсутствует токен {name}')
            exit()


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logger.error(error)
    except Exception as error:
        logger.error(error)
    else:
        logger.debug('Письмо успешно отправлено.')


def get_api_answer(timestamp):
    """Получение списка работ."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=payload)
        if response.status_code != requests.codes.ok:
            logger.error('Request не вернул статус 200!')
            raise KeyError
    except requests.ConnectTimeout as err:
        logger.error(err)
    except requests.Timeout as err:
        logger.error(err)
    except requests.ConnectionError as err:
        logger.error(err)
    except requests.JSONDecodeError as err:
        logger.error(err)
    return response.json()


def check_response(response):
    """Проверка статуса Домашки."""
    if not isinstance(response, dict):
        logger.critical('response[], error')
        raise TypeError
    if 'homeworks' not in response.keys():
        logger.critical("response['error'], error")
        raise KeyError
    if not isinstance(response['homeworks'], list):
        logger.critical("response['error'], error")
        raise TypeError
    return response['homeworks']


def parse_status(homework):
    """Создание ответа изменения статуса работы в Telegram."""
    try:
        homework_name = homework['homework_name']
        if homework['status'] in HOMEWORK_VERDICTS:
            verdict = HOMEWORK_VERDICTS[homework['status']]
    except KeyError as err:
        logger.error(f'Отсутсвует ключ {err}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp=timestamp)
            checked_response = check_response(response=response)
            if len(checked_response):
                message = parse_status(checked_response[0])
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
