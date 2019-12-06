#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
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
        self.prefix_size = 0
        self.source_word = ""
        self.game_started = False
        self.win_previous = False
        self.input_expected = False
        self.answer = ""
        self.model = KontaktModel()

    def close(self):
        self.model.close()

    # TODO:
    def computer_makes_word(self):
        self.source_word = 'арбуз'
        self.prefix_size = 1

    # TODO:
    def calculate_answer(self, description):
        """
        ML calculate word from description
        """

        logger.info("Get descr from user: " , description)
        m_answer = self.model.predict_word(description, self.source_word[:self.prefix_size])
        if m_answer == []:
            return 'У меня нет ответа!'
        else:
            return m_answer[0][0]

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
           """
        update.message.reply_text(RULES)

    def error(self, update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    def init_play(self, update, context):
        query = update.callback_query
        self.computer_makes_word()
        prefix = self.source_word[:self.prefix_size]
        query.edit_message_text(text=f"Загаданной мной слово начинается на \'{prefix}\'" + '\n'
                                     + f"Загадайте свое слово на \'{prefix}\' и опишите его")
        self.input_expected = True
        return PLAY

    def play(self, update, context):
        """Send message on `/play`."""

        # Get user that sent /play and log his name
        user = update.message.from_user
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
        self.answer = self.calculate_answer(description)
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='ANSWER:Y'),
             InlineKeyboardButton("Нет", callback_data='ANSWER:N')]
        ]
        bot_reply = f"Вы загадали слово: {self.answer}?" if self.input_expected else ""
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        update.message.reply_text(
            bot_reply,
            reply_markup=reply_markup
        )
        self.input_expected = False
        return PLAY

    def wrong_answer(self, update, context):
        query = update.callback_query
        bot = context.bot
        self.prefix_size += 1
        prefix = self.source_word[:self.prefix_size]
        if prefix == self.source_word:
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text=f"Раскрываю слово полностью:{self.source_word}\n" +
                     "Вы победили!"
            )
            return ConversationHandler.END
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Эх.. Раскрываю еще одну букву\n" +
                 f"Загаданной мной слово начинается на \'{prefix}\'" + '\n'
                 + f"Загадайте свое слово на \'{prefix}\' и опишите его"
        )
        self.input_expected = True
        return PLAY

    def correct_answer(self, update, context):
        query = update.callback_query
        bot = context.bot
        if self.answer == self.source_word:
            bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                text="Вы угадали мое слово!"
            )
            return ConversationHandler.END

        prefix = self.source_word[:self.prefix_size]
        bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text="Отлично! Я угадал, играем дальше\n" +
                 f"Загаданной мной слово начинается на \'{prefix}\'" + '\n'
                 + f"Загадайте свое слово на \'{prefix}\' и опишите его"
        )
        self.input_expected = True
        return PLAY

    def cancel_command(self, update, context):
        self.input_expected = False
        update.message.reply_text("Пока!")
        return ConversationHandler.END

    def main(self):
        # YOU SHOULD HAVE TOKEN IN YOUR ENV VARIABLES
        updater = Updater(os.getenv('TOKEN'), use_context=True)

        dp = updater.dispatcher

        dp.add_handler(CommandHandler('start', self.start_command))

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('play', self.play)],
            states={
                PLAY: [
                    MessageHandler(Filters.text, self.user_word),
                    CallbackQueryHandler(self.init_play, pattern='^' + 'PLAY:Y' + '$'),
                    CallbackQueryHandler(self.play_decline, pattern='^' + 'PLAY:N' + '$'),
                    CallbackQueryHandler(self.correct_answer, pattern='^' + 'ANSWER:Y' + '$'),
                    CallbackQueryHandler(self.wrong_answer, pattern='^' + 'ANSWER:N' + '$')]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_command)]
        )

        dp.add_handler(conv_handler)
        dp.add_handler(CommandHandler('help', self.help_command))
        dp.add_handler(CommandHandler('rules', self.rules_command))

        dp.add_error_handler(self.error)

        updater.start_polling()

        updater.idle()

    def __del__(self):
        self.close()

if __name__ == '__main__':
    bot = Bot()
    bot.main()
