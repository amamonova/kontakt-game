#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import os
import re

from script import KontaktModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Stages
PLAY, WAIT = range(2)


class Bot:
    def __init__(self):
        self.command_tags = ['HELLO', 'RULES', 'STOP', 'PLAY', 'HELP']
        self.tag_to_func = {
            'HELLO': self.start_command,
            'RULES': self.rules_command,
            'STOP': self.cancel_command,
            'PLAY': self.play,
            'HELP': self.help_command
        }
        self.rules_words = [
            "правила"
        ]
        self.help_words = [
            "помощь"
        ]
        self.stop_words = [
            "стой",
            "стоп",
            "остановись",
            "отмена",
            "отстань",
            "надоело"
        ]
        self.play_words = [
            "играть",
            "начинай",
            "запускай",
            "пошли"
        ]
        self.hello_words = [
            "привет",
            "здравствуй"
        ]
        self.tag_to_list = {
            'HELLO': self.hello_words,
            'RULES': self.rules_words,
            'STOP': self.stop_words,
            'PLAY': self.play_words,
            'HELP': self.help_words
        }
        self.source_word = {}
        self.prefix = {}
        self.input_expected = {}
        self.answer = ""
        self.model = KontaktModel()
        self.guessing = {}

    def log_database(self, bot_word, user_name, prefix, user_desc, bot_ans):
        with open('database.csv', 'a') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [user_name, bot_word, prefix, user_desc, bot_ans])

    def close(self):
        self.model.close()

    def computer_makes_word(self, user):
        try:
            word = self.model.get_random_word()
            if word == "":
                logger.warning("RANDOM WORD IS EMPTY")
                self.source_word[user] = 'арбуз'
                self.prefix[user] = 'а'
                return
            self.source_word[user] = word
            self.prefix[user] = word[0]
            logger.info(f"Computer choose word:{self.source_word[user]} for user {user.first_name}")
        except KeyError:
            logger.warning(f"USER NOT FOUND {user.first_name}")

    def calculate_answer(self, description, user):
        """
        ML calculate word from description
        """
        logger.info(f"Get descr from user: {description}, to prefifx {self.prefix[user]}")
        answer = self.model.predict_word(description, self.prefix[user])
        self.log_database(user_name=f'{user.first_name} {user.last_name}',
                          bot_word=self.source_word[user],
                          prefix=self.prefix[user],
                          user_desc=description,
                          bot_ans=answer)
        return answer

    def start_command(self, update, context):
        GREETINGS_TEXT = """Привет! Я бот из CSC. Давай сыграем в игру контакт! (/play чтобы начать)"""
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=GREETINGS_TEXT)

    def help_command(self, update, context):
        update.message.reply_text(
            """/rules - правила игры \n/play - начать игру"""
        )

    def rules_command(self, update, context):
        RULES = """
           Правила игры Контакт:
           (1) Компьютер загадывает некоторое слово А. Глобальная цель игры угадать слово!
           (2) Компьютер раскрывает первую, ранее не раскрытую букву слова A.
           (3) Пользователь загадывает слово B, которое обязано начинатся на ранее раскрытый перфикс слова A.
           (4) Пользователь посылает компьютеру некое объяснение слова B, не использующее однокоренных c B слов.
           (5) Компьютер пытается угадать слово B по объяснению
           (6) Если компьютер справился, т.е он угадал слово B, есть 2 варианта:
               - A = B, тогда пользователь победил
               - A \\= B, тогда игра возвращается на шаг (3)
           (7) Если компьютер не справился, т.е вывел слово отличное от B, игра переходит на шаг (2)
           (8) Игра заканчивается, если слово A раскрыто или угадано

           Особенности загаданных слов:
           Компьютер загадывает исключительно русские нарицательные существительные
           Пользователь должен загадывать исключительно русские нарицательные существительные
           """
        update.message.reply_text(RULES)

    def error(self, update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    def init_play(self, update, context):
        user = update.effective_user
        self.computer_makes_word(user)
        bot_text = f"Загаданной мной слово начинается на \'{self.prefix[user]}\'" + '\n' \
                   + f"Загадайте свое слово на \'{self.prefix[user]}\' и опишите его"
        self.guess_reply(update=update, context=context, bot_text=bot_text)
        return PLAY

    def play(self, update, context):
        """Send message on `/play`."""
        # Get user that sent /play and log his name
        user = update.effective_user
        self.guessing[user] = False
        logger.info("User %s started the conversation.", user.first_name)

        # Build InlineKeyboard where each button has a displayed text
        # and a string as callback_data
        # The keyboard is a list of button rows, where each row is in turn
        # a list (hence `[[...]]`).
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='PLAY:Y'),
             InlineKeyboardButton("Нет", callback_data='PLAY:N')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send message with text and appended InlineKeyboard
        update.message.reply_text(
            "Вы готовы начать игру?",
            reply_markup=reply_markup
        )
        # Tell ConversationHandler that we're in state `PLAY` now
        return PLAY

    def play_decline(self, update, context):
        query = update.callback_query
        bot = context.bot
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Сыграем в другой раз!"
        )
        return ConversationHandler.END

    def user_word(self, update, context):
        description = update.message.text
        user = update.effective_user
        if self.guessing[user]:
            self.guessing[user] = False
            if description == self.source_word[user]:
                update.message.reply_text("Вы угадали мое слово!")
                self.input_expected[user] = False
                return ConversationHandler.END
            else:
                update.message.reply_text("Нет, это не мое слово.")
                bot_text = f"Загаданной мной слово начинается на \'{self.prefix[user]}\'" + '\n' \
                           + f"Загадайте свое слово на \'{self.prefix[user]}\' и опишите его"
                keyboard = [
                    [InlineKeyboardButton("Угадать слово", callback_data='GUESS'),
                     InlineKeyboardButton("Сдаться", callback_data='GIVE_UP')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(
                    bot_text,
                    reply_markup=reply_markup
                )
                return PLAY
        self.answer = self.calculate_answer(description, user)
        if self.answer == "":
            update.message.reply_text("У меня нет ответа(")
            self.wrong_answer(update, context)
            return PLAY
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='ANSWER:Y'),
             InlineKeyboardButton("Нет", callback_data='ANSWER:N')]
        ]
        bot_reply = f"Вы загадали слово: {self.answer}?"
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        update.message.reply_text(
            bot_reply,
            reply_markup=reply_markup
        )
        self.input_expected[user] = False
        return PLAY

    def handle_message(self, update, context):
        user = update.effective_user
        if self.input_expected[user]:
            self.user_word(update, context)
        else:
            msg = update.message.text
            msg = re.sub(r'[^\w\s]', '', msg)
            for word in msg.split(' '):
                for tag in self.command_tags:
                    if word in self.tag_to_list[tag]:
                        self.tag_to_func[tag](update, context)
                        return

    def wrong_answer(self, update, context):
        query = update.callback_query
        bot = context.bot
        user = update.effective_user
        self.prefix[user] = self.prefix[user] + self.source_word[user][len(self.prefix[user])]
        if self.prefix[user] == self.source_word[user]:
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"Раскрываю слово полностью:{self.source_word[user]}\n" +
                     "Вы победили!"
            )
            return ConversationHandler.END
        bot_text = "Эх.. Раскрываю еще одну букву\n" + \
                   f"Загаданной мной слово начинается на \'{self.prefix[user]}\'" + '\n' \
                   + f"Загадайте свое слово на \'{self.prefix[user]}\' и опишите его"
        self.guess_reply(update=update, context=context, bot_text=bot_text)
        return PLAY

    def guess_reply(self, update, context, bot_text):
        query = update.callback_query
        bot = context.bot
        user = update.effective_user
        keyboard = [
            [InlineKeyboardButton("Угадать слово", callback_data='GUESS'),
             InlineKeyboardButton("Сдаться", callback_data='GIVE_UP')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=bot_text,
            reply_markup=reply_markup
        )
        self.input_expected[user] = True

    def giveup(self, update, context):
        query = update.callback_query
        bot = context.bot
        user = update.effective_user
        self.input_expected[user] = False
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=f"Мое слово было {self.source_word[user]}. Я победил!"
        )
        return ConversationHandler.END

    def user_guess(self, update, context):
        query = update.callback_query
        bot = context.bot
        user = update.effective_user
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=f"Хотите угадать мое слово? Введите догадку."
        )
        self.guessing[user] = True

        return PLAY

    def correct_answer(self, update, context):
        query = update.callback_query
        bot = context.bot
        user = update.effective_user
        if self.answer == self.source_word[user]:
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="Вы угадали мое слово!"
            )
            self.input_expected[user] = False
            return ConversationHandler.END

        bot_text = "Отлично! Я угадал, играем дальше\n" + \
                   f"Загаданной мной слово начинается на \'{self.prefix[user]}\'" + '\n' \
                   + f"Загадайте свое слово на \'{self.prefix[user]}\' и опишите его"
        self.guess_reply(update=update, context=context, bot_text=bot_text)
        return PLAY

    def cancel_command(self, update, context):
        user = update.effective_user
        self.input_expected[user] = False
        update.message.reply_text("Пока!")
        return ConversationHandler.END

    def main(self):
        # YOU SHOULD HAVE TOKEN IN YOUR ENV VARIABLES

        updater = Updater(os.getenv('TOKEN'), use_context=True)

        dp = updater.dispatcher

        dp.add_handler(CommandHandler('start', self.start_command))

        dp.add_handler(CallbackQueryHandler(self.init_play, pattern='^' + 'PLAY:Y' + '$'))
        dp.add_handler(CallbackQueryHandler(self.play_decline, pattern='^' + 'PLAY:N' + '$'))
        dp.add_handler(CallbackQueryHandler(self.wrong_answer, pattern='^' + 'ANSWER:N' + '$'))
        dp.add_handler(CallbackQueryHandler(self.correct_answer, pattern='^' + 'ANSWER:Y' + '$'))
        dp.add_handler(CallbackQueryHandler(self.giveup, pattern='^' + 'GIVE_UP' + '$'))
        dp.add_handler(CallbackQueryHandler(self.user_guess, pattern='^' + 'GUESS' + '$'))
        dp.add_handler(MessageHandler(Filters.text, self.handle_message))
        dp.add_handler(CommandHandler('play', self.play))
        dp.add_handler(CommandHandler('cancel', self.cancel_command))

        dp.add_handler(CommandHandler('help', self.help_command))
        dp.add_handler(CommandHandler('rules', self.rules_command))

        dp.add_error_handler(self.error)

        updater.start_polling()

        updater.idle()

    def __del__(self):
        self.close()


if __name__ == '__main__':
    bot = Bot()
    #print("SUKA")
    bot.main()
