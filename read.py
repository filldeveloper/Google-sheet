from googleapiclient.discovery import build
from google.oauth2 import service_account
from funcoes_planilha_credito import extrato_bb, extrato_caixa, mensagem_bot_telegram
from datetime import datetime
import time
from pprint import pprint

# Chamando a função que pega os valores do extrato BB
lista_definitiva = extrato_bb()
historico_compras_visa = lista_definitiva[0]
historico_compras_smiles = lista_definitiva[1]
historico_compras_nanquim = lista_definitiva[2]
fechamento_visa = lista_definitiva[3]
fechamento_smiles = lista_definitiva[4]
fechamento_elo = lista_definitiva[5]

print(f'Fechamento da próxima fatura visa: {fechamento_visa}')
print(f'Histórico de compras Visa: {historico_compras_visa}')
print(f'Fechamento da próxima fatura smiles: {fechamento_smiles}')
print(f'Histórico de compras Visa: {historico_compras_smiles}')
print(f'Fechamento da próxima fatura Elo Nanquim: {fechamento_elo}')
print(f'Histórico de compras Visa: {historico_compras_nanquim}')

dicionario_meses = {5: "api", 6: "api2"}

# mensagem_visa = f'Fechamento da próxima fatura visa: {fechamento_visa}'
# mensagem_bot_telegram(mensagem_visa)
# mensagem_smiles = f'Fechamento da próxima fatura smiles: {fechamento_smiles}'
# mensagem_bot_telegram(mensagem_smiles)
# mensagem_elo = f'Fechamento da próxima fatura Elo Nanquim: {fechamento_elo}'
# mensagem_bot_telegram(mensagem_elo)

SERVICE_ACCOUNT_FILE = '/home/felipe/projetos_python/google_sheet/keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = None
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID spreadsheet.
SAMPLE_SPREADSHEET_ID = '1aYNZ1TCIvekdr1KoBmA6D9x95TyYuEM3ycYVxtiDaJQ'
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Upadte da Sheets
valor_visa = []
for gasto in historico_compras_visa:
    preço = str(f'{gasto[2]:.2f}').split('.')
    gasto[2] = "R$ " + preço[0] + "," + preço[1]
    valor_visa.append(gasto)

valor_smiles = []
for gasto in historico_compras_smiles:
    preço = str(f'{gasto[2]:.2f}').split('.')
    gasto[2] = "R$ " + preço[0] + "," + preço[1]
    valor_smiles.append(gasto)

valor_nanquim = []
for gasto in historico_compras_nanquim:
    preço = str(f'{gasto[2]:.2f}').split('.')
    gasto[2] = "R$ " + preço[0] + "," + preço[1]
    valor_nanquim.append(gasto)
# PAREI AQUI, LEVAR NOTE PARA CONTINUAR

aba = int(fechamento_visa.split('/')[1]+1)
range = f'{dicionario_meses[aba]}!A2:C17'
result = sheet.values().get(spreadshet=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])

planilha = []
for row in result:
    data = row[0].split('/')
    row[0] = data[0] + "/" + data[1]
    planilha.append(row)

resultado_visa = []
for i in valor_visa:
    if i not in planilha:
        resultado_visa.append(i)

resultado_smiles = []
for i in valor_smiles:
    if i not in planilha:
        resultado_smiles.append(i)


sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                      range=range,
                      valueInputOption="USER_ENTERED",
                      body={"values": resultado_final}).execute()
print("Cartões BB atualizados!")
mensagem_final = "Planilha de Cartões BB atualizada!"
mensagem_bot_telegram(mensagem_final)

###################################################################
time.sleep(5)
# Chamando a função que pega os valores do extrato CAIXA
cartao_caixa = extrato_caixa()
data_proxima_fatura = cartao_caixa[1]
historico_compras = cartao_caixa[0]

mensagem_caixa = f'Fechamento da próxima fatura Caixa: {data_proxima_fatura}'
mensagem_bot_telegram(mensagem_caixa)

# SERVICE_ACCOUNT_FILE = '/home/felipe/projetos_python/google_sheet/keys.json'
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# creds = None
# creds = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# # The ID spreadsheet.
# SAMPLE_SPREADSHEET_ID = '1aYNZ1TCIvekdr1KoBmA6D9x95TyYuEM3ycYVxtiDaJQ'

# service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API and get the values
range = "api!E2:G17"
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])

last_row = result[-1] if result else None
next_empty_row = len(result) + 2

# Upadte da Sheets
range = "api!E" + str(next_empty_row)

resultado_final = []
for i in historico_compras:
    if i not in result:
        resultado_final.append(i)

sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                      range=range,
                      valueInputOption="USER_ENTERED",
                      body={"values": resultado_final}).execute()
print("Valor atualizado!")
mensagem_final = 'Planilha do Cartão Caixa atualizada!'
mensagem_bot_telegram(mensagem_final)
