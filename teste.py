from googleapiclient.discovery import build
from google.oauth2 import service_account
from funcoes_planilha_credito import extrato_bb, extrato_caixa, mensagem_bot_telegram
from datetime import datetime
import time
from pprint import pprint

data_fechamento_visa = "24/04/2021"
data_fechamento_elo = "21/04/2021"
data_timestamp_visa = time.mktime(datetime.strptime(
    data_fechamento_visa, '%d/%m/%Y').timetuple())
data_timestamp_elo = time.mktime(datetime.strptime(
    data_fechamento_elo, '%d/%m/%Y').timetuple())

historico_compras = [["21/04/2021", "Teste1", 21.90],
                     ["23/04/2021", "Teste2", 50.90],
                     ["24/04/2021", "Teste3", 12.90],
                     ["25/04/2021", "Teste4", 19.90]]


dicionario_meses = {4: "api", 5: "api2"}


SERVICE_ACCOUNT_FILE = '/home/felipe/projetos_python/google_sheet/keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = None
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID spreadsheet.
SAMPLE_SPREADSHEET_ID = '1aYNZ1TCIvekdr1KoBmA6D9x95TyYuEM3ycYVxtiDaJQ'

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

valor = []
for gasto in historico_compras:
    preço = str(f'{gasto[2]:.2f}').split('.')
    gasto[2] = "R$ " + preço[0] + "," + preço[1]
    valor.append(gasto)
# PAREI DE COMPARAR AQUI
proxima_fatura = []
fatura_seguinte = []
for compra in valor:
    data_timestamp = time.mktime(datetime.strptime(
        compra[0], '%d/%m/%Y').timetuple())
    if int(data_timestamp) < int(data_timestamp_visa):
        proxima_fatura.append(compra)
    else:
        fatura_seguinte.append(compra)

# Coletando os dados da planilha
aba = int(data_fechamento_visa.split('/')[1])
range = f'{dicionario_meses[aba]}!A2:C17'
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])

resultado_final = []
for i in proxima_fatura:
    if i not in result:
        resultado_final.append(i)

# Atualizando a próxima fatura
next_empty_row = len(result) + 2
range = f'{dicionario_meses[aba]}!A{next_empty_row}'
sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                      range=range,
                      valueInputOption="USER_ENTERED",
                      body={"values": resultado_final}).execute()

# Coletando os dados da fatura seguinte
aba += 1
range = f'{dicionario_meses[aba]}!A2:C17'
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])

resultado_final = []
for i in fatura_seguinte:
    if i not in result:
        resultado_final.append(i)

# Atualização da fatura seguinte
next_empty_row = len(result) + 2
range = f'{dicionario_meses[aba]}!A{next_empty_row}'
sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                      range=range,
                      valueInputOption="USER_ENTERED",
                      body={"values": resultado_final}).execute()


print("Cartões BB atualizados!")
