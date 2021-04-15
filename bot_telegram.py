import os
import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from credenciais import token_bot_zabbix
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import ConversationHandler

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def start(update, context):
    message = update.message.reply_text(
        'Seja bem vindo ao Bot Telegram do Felipe Barreto!\n\nEscolha uma opção: \n1 - Felipe\n2 - Bruno\n3 - Vavá\n4 - Silvia',
        reply_markup=ReplyKeyboardRemove()
    )
    echo(update, context)


def echo(update, context):
    option = update.message.text
    if option == '1':
        message = 'Felipe é o filho mais velho!'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    elif option == '2':
        message = 'Bruno é o filho mais novo!'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    elif option == '3':
        message = 'Vavá é o pai da família!'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    else:
        message = 'Silvia é a mãe da família!'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def unknown(update, context):
    message = 'Mas que bosta'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)



token = token_bot_zabbix
# os.getenv('TOKEN_TG')


def main():
    print('Start bot configuration')
    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    teste = dp.add_handler(MessageHandler(
        Filters.text & (~Filters.command), start))
    dp.add_handler(MessageHandler(Filters.text, unknown))
    
    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
