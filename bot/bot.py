from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import logging
from config import TOKEN_ID, REQUEST_KWARGS

TOKEN = TOKEN_ID
REQUEST_KWARGS = REQUEST_KWARGS

updater = Updater(TOKEN, request_kwargs=REQUEST_KWARGS, use_context=True)

dispatcher = updater.dispatcher

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Hi! I\'m bot from CSC. '
                                  'Let\'s play Kontakt game!')


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=update.message.text[::-1])


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()
