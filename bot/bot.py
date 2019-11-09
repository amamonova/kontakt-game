import csv
import re
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import logging
from config import TOKEN_ID, DEFAULT_REQUEST_KWARGS

PREFIX, RIDDLE, ANSWER, RESPONSE = range(4)


class Bot:
    def __init__(self):
        self.prefix_size = 0
        self.source_word = ""
        self.game_started = False
        self.win_previous = False

    def start_bot(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)
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

        start_handler = CommandHandler('start', self.start_command)
        dispatcher.add_handler(start_handler)

        dispatcher.add_handler(CommandHandler('help', self.help_command))
        dispatcher.add_handler(CommandHandler('rules', self.rules_command))

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('play', self.play_command)],
            states={
                PREFIX: [MessageHandler(Filters.text, self.prefix_state_handler)],
                RIDDLE: [MessageHandler(Filters.text, self.riddle_state_handler)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel_command)]
        )
        dispatcher.add_handler(conv_handler)

        updater.start_polling()

    def computer_makes_word(self):
        self.source_word = 'арбуз'
        self.prefix_size = 1

    def calculate_answer(self, description):
        """
        ML calculate word from description
        """
        return 'апельсин'

    def start_command(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Hi! I\'m bot from CSC. '
                                      'Let\'s play Kontakt game!')

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

    def play_command(self, update, context):
        update.message.reply_text('Вы готовы начать игру?(y/n)')
        self.computer_makes_word()
        self.game_started = False
        return PREFIX

    def prefix_state_handler(self, update, context):
        if self.game_started:
            if re.findall('y', update.message.text):
                update.message.reply_text("Отлично, я угадал, играем дальше")
            else:
                self.prefix_size = self.prefix_size + 1
                if self.prefix_size == len(self.source_word):
                    update.message.reply_text(f"Вы победили! Я полностью раскрываю слово: {self.source_word} "
                                              f"\nИгра окончена.")
                    return ConversationHandler.END
                update.message.reply_text("Эхх, раскрываю еще одну букву..")
        else:
            if re.findall('y', update.message.text):
                update.message.reply_text("Начинаем игру.")
                self.game_started = True
            else:
                update.message.reply_text("Сыграем в другой раз.")
                self.game_started = False
                return ConversationHandler.END
        prefix = self.source_word[:self.prefix_size]
        update.message.reply_text(f"Загаданной мной слово начинается на \'{prefix}\'")
        update.message.reply_text(f"Загадайте свое слово на \'{prefix}\' и опишите его")
        return RIDDLE

    def riddle_state_handler(self, update, context):
        description = update.message.text
        answer = self.calculate_answer(description)
        update.message.reply_text(f"Вы загадали {answer}? (y/n)")
        return PREFIX

    def cancel_command(self, update, context):
        update.message.reply_text("Игра отменяется.")
        self.game_started = False
        return ConversationHandler.END


if __name__ == '__main__':
    bot = Bot()
    bot.start_bot()
