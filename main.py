# -*- coding: utf8 -*-
import telebot
from telebot import types
from SimpleQIWI import QApi

import config


bot = telebot.TeleBot(config.token, parse_mode=None)
apiqiwi = QApi(token=config.QIWI_TOKEN, phone=config.QIWI_NUMBER)

UNAVAILABLE = ('Поиск сейчас недоступен. Бот не обрабатывает запросы и не принимает '
               'оплату за подписку. Не отправляйте сюда персональные данные.')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, '👁 Глаз Бога\n\n' + UNAVAILABLE,
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(commands=['balance'])
def send_balance(message):
    if message.chat.id == config.admin_id:
        bot.send_message(message.chat.id, 'Баланс: ' + str(apiqiwi.balance[0]) + '₽')
    else:
        bot.send_message(message.chat.id, 'Команда недоступна.')


@bot.message_handler(content_types=['text'])
def message(message):
    if message.text == '📓 Руководство':
        bot.send_message(message.chat.id, 'Руководство по поиску пока недоступно. ' + UNAVAILABLE)
    elif message.text == '👤 Мой аккаунт':
        bot.send_message(message.chat.id, 'Ваш ID: ' + str(message.chat.id) + '\n'
                         'Подписки и статистика поисков в этом боте недоступны.')
    else:
        bot.send_message(message.chat.id, UNAVAILABLE)


@bot.message_handler(content_types=['document', 'photo', 'location', 'voice'])
def unsupported_media(message):
    bot.send_message(message.chat.id, UNAVAILABLE)


@bot.callback_query_handler(func=lambda call: True)
def step_buy(call):
    # Old purchase buttons may remain in existing Telegram chats.
    bot.answer_callback_query(call.id, UNAVAILABLE, show_alert=True)


if __name__ == '__main__':
    bot.polling(none_stop=True)
