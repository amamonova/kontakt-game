import csv
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from config import TOKEN_ID, DEFAULT_REQUEST_KWARGS


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Hi! I\'m bot from CSC. '
                                  'Let\'s play Kontakt game!')


def echo(update, context):
    message = update.message.text
    response = message[::-1]

    with open('database.csv', 'a') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [update.effective_chat.id, message, response])

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=response)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

if __name__ == '__main__':

    get_request = requests.get('http://pubproxy.com/api/proxy?limit=1&'
                               'format=txt&port=8080&level=anonymous&'
                               'type=socks5&country=FI|NO|US&https=True')
    proxy_response = get_request.text
    if proxy_response:
        REQUEST_KWARGS = {'proxy_url': f'https://{proxy_response}'}
    else:
        REQUEST_KWARGS = DEFAULT_REQUEST_KWARGS

    updater = Updater(TOKEN_ID, request_kwargs=REQUEST_KWARGS,
                      use_context=True)

    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    echo_handler = MessageHandler(Filters.text, echo)
    dispatcher.add_handler(echo_handler)

    updater.start_polling()
