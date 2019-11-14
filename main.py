import requests
import time
import os
import json
import logging
from logging.handlers import RotatingFileHandler

import telegram

DVMN_TOKEN = os.getenv('DVMN_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')
LOG_TOKEN = os.getenv('LOG_TOKEN')

url = 'https://dvmn.org/api/long_polling/'


def send_message(tg_token, update_text):
    bot = telegram.Bot(tg_token)
    chat_id = bot.get_updates()[-1].message.chat_id
    bot.send_message(chat_id=chat_id, text=update_text)


def main(dvmn_token, url):
    last_time = None
    while True:
        try:
            response = requests.get(url,
                       headers={'Authorization': f'Token {dvmn_token}'},
                       timeout=120,
                       params={'timestamp': last_time})
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError):
            logger.exception(msg='connectionerror')
            time.sleep(30)
            continue
        if response.ok:
            response_data = response.json()
            if response_data['status'] == "found":
                last_time = response_data['last_attempt_timestamp']
                new_attempts = response_data['new_attempts'][0]
                lesson_title = new_attempts['lesson_title']
                check_result = new_attempts['is_negative']
                lesson_url = new_attempts['lesson_url']
                if check_result:
                    approve_phrase = 'В ней есть ошибки.'
                else:
                    approve_phrase = 'Ошибок нет! Ура!'
                print('found')
                send_message(TG_TOKEN,
                     f'''Задача «{lesson_title}» проверена.
                     {approve_phrase} https://dvmn.org{lesson_url}''')
            elif response_data['status'] == "timeout":
                last_time = response_data['timestamp_to_request']
                logger.info('request timeout')
            else:
                print('json decode error')
                logger.exception(msg='json decode error')
                time.sleep(5)
                continue
        else:
            print('request error')
            logger.exception(msg='request error')
            time.sleep(5)
            continue


if __name__ == '__main__':
    class MyLogsHandler(logging.Handler):
        def emit(self, record):
            log_entry = self.format(record)
            send_message(LOG_TOKEN, log_entry)

    logger = logging.getLogger("bot logger")
    handler = RotatingFileHandler("app.log", maxBytes=200, backupCount=3)
    logger.addHandler(MyLogsHandler())


    main(DVMN_TOKEN, url)
