import os
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler


def start(update, context):
    message = 'Seja bem vindo ao Bot Telegram'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def echo(update, context):
    message = 'Escolha uma opção: \n1 - Felipe\n2 - Bruno\n3 - Vavá\n4 - Silvia'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def unknown(update, context):
    message = 'Unknown Command'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def felipe(update, context):
    message = 'Filho mais Velho'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def bruno(update, context):
    message = 'Filho mais Novo'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def vava(update, context):
    message = 'Pai de família'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def silvia(update, context):
    message = 'Mãe e dona de casa'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


token = "1784430746:AAFp0MUPY-i6nk085y16AwmowXEE4JQ16X8"
# os.getenv('TOKEN_TG')


def main():
    print('Start bot configuration')
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(
        Filters.text & (~Filters.command), echo))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    dispatcher.add_handler(MessageHandler('1', felipe))
    dispatcher.add_handler(MessageHandler('2', bruno))
    dispatcher.add_handler(MessageHandler('3', vava))
    dispatcher.add_handler(MessageHandler('4', silvia))
    # Start the bot and
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
