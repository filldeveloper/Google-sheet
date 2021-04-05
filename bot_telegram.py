import requests
from pprint import pprint
import urllib.parse

# Ler msgs que estão sendo mandadas para o bot
chat_id = '-1001410402288'
token = '1775549137:AAHNBuPFWmvq-K1aI2SHhojVqQC2unQBGoA'
mensagem = 'Fechamento da próxima fatura visa: 24/04/2021'
msg_url = urllib.parse.quote(mensagem)
# url_base = f'https://api.telegram.org/bot{token}/getUpdates'
url_send = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={msg_url}'
resultado = requests.post(url_send)
pprint(msg_url)
# time.sleep(50)
