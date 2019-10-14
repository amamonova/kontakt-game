from telegram.ext import Updater
import logging
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from config import TOKEN_ID

token = TOKEN_ID
request_kwargs = {'proxy_url': 'https://192.53.40.221:8080'}

updater = Updater(token, request_kwargs=request_kwargs, use_context=True)

dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, \
                             text='Hi! I\'m bot from CSC. '\
                             'Let\'s play Kontakt game!')

def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, \
                                text=update.message.text[::-1])

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()
