from funcoes_planilha_credito import mensagem_bot_telegram
from credenciais import token_telegram, chat_id_telegram
from telegram.ext import Updater
import telegram
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

token = token_telegram
chatid = chat_id_telegram

updater = Updater(token=token, use_context=True)
lista = [['16/04', 'DROGARIA SAUDE E', 18.4],
         ['16/04', 'JOSE MARIA DA SIL', 9.19],
         ['16/04', 'CASA DE COSMETICO',17.99],
         ['16/04', 'BIO VITAMINAS', 29.9],
         ['16/04', 'EBANX*XSOLLA', 29.55],
         ['17/04', 'CASCOL COMBUSTIVEIS', 30.0]]



if len(lista) > 0:
    mensagem = '*Valores adicionados a planilha\!*\n\n'
    updater.bot.send_message(chat_id=chatid, text=mensagem, parse_mode=telegram.ParseMode.MARKDOWN_V2)
    
    mensagem = ''
    for valor in lista:
        novo_valor = f'{valor[2]:.2f}'
        mensagem += valor[1] + ' - ' + 'R$ ' + str(novo_valor).replace('.', ',') + '\n'
    updater.bot.send_message(chat_id=chatid, text=mensagem)
else:
    mensagem = '*Nenhum valor a ser adicionado a planilha*'
    updater.bot.send_message(chat_id=chatid, text=mensagem, parse_mode=telegram.ParseMode.MARKDOWN_V2)

print('Mensagem Enviada!')
