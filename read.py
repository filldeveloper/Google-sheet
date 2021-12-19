from googleapiclient.discovery import build
from google.oauth2 import service_account
from funcoes_planilha_credito import extrato_bb, extrato_caixa, telegram_bot
from datetime import datetime, date
import time
from pprint import pprint

mensagem_inicial = "Bot de controle de gastos iniciado\!"
telegram_bot(mensagem_inicial)
# Chamando a função que pega os valores do extrato BB
lista_definitiva = extrato_bb()
historico_compras_visa = lista_definitiva[0]
historico_compras_nanquim = lista_definitiva[1]
fechamento_visa = lista_definitiva[2]
fechamento_nanquim = lista_definitiva[3]

dicionario_meses = {1: "janeiro", 2: "fevereiro", 3: "março",
                    4: "abril", 5: "maio", 6: "junho",
                    7: "julho", 8: "agosto", 9: "setembro",
                    10: "outubro", 11: "novembro", 12: "dezembro"}

aba_mes = int(fechamento_visa.split('/')[1]) + 1
if aba_mes == 13:
    aba_mes = 1

# Setar o range da aba mês api!C2
range_aba = f'{dicionario_meses[aba_mes]}!F11'

# Pegar data atual para decidir qual mês irei adicionar os dados
data_atual = date.today()
data_atual = f'{data_atual.day}/{data_atual.month}/{data_atual.year}'

# historico_compras_visa = [['10/12', 'LOUNGE KEY INC', 5.78],
#                         ['10/12', 'GOL TRANSP A*CDHZPR014216', 45.0],
#                         ['15/12', 'SUPERMERCADINHOS', 23.01],
#                         ['23/12', 'SUPERMERCADINHOS', 25.06]]

# historico_compras_nanquim = [['20/12', '99 TECNOLOGIA LTDA', 100.0],
#                             ['18/12', 'BE HONEST', 34.34],
#                             ['29/12', 'MARMITARIA VENTURA MAM', 16.0],
#                             ['29/12', '99 TECNOLOGIA LTDA', 100.0]]

# Juntar as duas listas de gastos
historico_compras = historico_compras_visa + historico_compras_nanquim

print(f'Fechamento da próxima fatura Visa: {fechamento_visa}')
print(f'Histórico de compras Visa: {historico_compras_visa}')
print(f'Fechamento da próxima fatura Elo Nanquim: {fechamento_nanquim}')
print(f'Histórico de compras Elo Nanquim: {historico_compras_nanquim}')


mensagem_visa = f'Fechamento da próxima fatura visa: {fechamento_visa}'
telegram_bot(mensagem_visa)
mensagem_elo = f'Fechamento da próxima fatura Elo Nanquim: {fechamento_nanquim}'
telegram_bot(mensagem_elo)

SERVICE_ACCOUNT_FILE = '/home/serpro/development/google-sheet/Google-sheet/keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = None
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID spreadsheet.
SAMPLE_SPREADSHEET_ID = '15p-0cJcNjjtDuCIsaLldab8McyTKEHrcj_tlY-sevhw'
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Inserir data de fechamento da fatura visa
sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                    range=range_aba,
                    valueInputOption="USER_ENTERED",
                    body={"values": [[fechamento_visa]]}).execute()

# Update da Sheets
descricao_compra = []
for gasto in historico_compras:
    preço = str(f'{gasto[2]:.2f}').split('.')
    gasto[2] = "R$ " + preço[0] + "," + preço[1]
    descricao_compra.append(gasto)

# O número da aba será coletado de aco4rdo com a data do gasto
ano = int(data_atual.split('/')[2])

range = f'{dicionario_meses[aba_mes]}!H2:J100'
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])

planilha = []
for row in result:
    data = row[0].split('/')
    row[0] = data[0] + "/" + data[1]
    planilha.append(row)

resultado_compra = []
for i in descricao_compra:
    if i not in planilha:
        resultado_compra.append(i)

# Pegar a data de fechamento da fatura na planilha e alimentá-la de acordo
fechamento_planilha = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range_aba).execute().get('values', [])[0][0]

# Transformar data de fechamento da planilha em timestamp
timestamp_fechamento = time.mktime(datetime.strptime(
    fechamento_planilha, '%d/%m/%Y').timetuple())

# Enviar mensagem via telegram caso exista gasto a ser adicionado
# Alimentar a planilha com os dados do cartão Visa
validador_msg = 0
for gasto in resultado_compra:
    numero_aba = int(gasto[0].split('/')[1]) + 1
    if numero_aba == 13:
            numero_aba = 1
    # if mes_gasto > numero_aba:
    #     data_gasto = f'{gasto[0]}/{ano-1}'
    
    data_gasto = f'{gasto[0]}/{ano}'

    timestamp_data_gasto = time.mktime(datetime.strptime(
                                data_gasto, '%d/%m/%Y').timetuple())

    if timestamp_data_gasto < timestamp_fechamento:
        # Mandar msg para cada gasto
        mensagem_gasto = f'{gasto[1]} \- {gasto[-1]}'
        if "=" in mensagem_gasto:
            mensagem_gasto = mensagem_gasto.replace('=', '\=')
        telegram_bot(mensagem_gasto)

        validador_msg = 1
        range = f'{dicionario_meses[numero_aba]}!H2:J100'
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])
        next_empty_row = len(result) + 2
        range = f'{dicionario_meses[numero_aba]}!H{next_empty_row}'
        sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                    range=range,
                    valueInputOption="USER_ENTERED",
                    body={"values": [gasto]}).execute()
    else:
        numero_aba = numero_aba + 1
        if numero_aba == 13:
            numero_aba = 1
        
        range = f'{dicionario_meses[numero_aba]}!H2:J100'
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])
        
        planilha = []
        for row in result:
            data = row[0].split('/')
            row[0] = data[0] + "/" + data[1]
            planilha.append(row)

        if gasto not in planilha:
            mensagem_gasto = f'{gasto[1]} \- {gasto[-1]}'
            if "=" in mensagem_gasto:
                mensagem_gasto = mensagem_gasto.replace('=', '\=')
            telegram_bot(mensagem_gasto)

            validador_msg = 1
            next_empty_row = len(result) + 2
            range = f'{dicionario_meses[numero_aba]}!H{next_empty_row}'
            sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range=range,
                        valueInputOption="USER_ENTERED",
                        body={"values": [gasto]}).execute()

if not validador_msg:
    mensagem  = "Nenhum valor a ser adicionado a planilha\!"
    telegram_bot(mensagem)

print("Cartões BB atualizados!")
mensagem_final = "Planilha de Cartões BB atualizada\!"
telegram_bot(mensagem_final)
# --------------------------------------------------------------------------------------

time.sleep(5)
# Chamando a função que pega os valores do extrato CAIXA
# cartao_caixa = extrato_caixa()
# data_proxima_fatura = cartao_caixa[1]
# historico_compras = cartao_caixa[0]

# mensagem_caixa = f'Fechamento da próxima fatura Caixa: {data_proxima_fatura}'
# mensagem_bot_telegram(mensagem_caixa)

# SERVICE_ACCOUNT_FILE = '/home/felipe/projetos_python/google_sheet/keys.json'
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# creds = None
# creds = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# # The ID spreadsheet.
# SAMPLE_SPREADSHEET_ID = '1aYNZ1TCIvekdr1KoBmA6D9x95TyYuEM3ycYVxtiDaJQ'

# service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API and get the values
# range = "api!E2:G17"
# sheet = service.spreadsheets()
# result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
#                             range=range).execute().get('values', [])

# last_row = result[-1] if result else None
# next_empty_row = len(result) + 2

# Upadte da Sheets
# range = "api!E" + str(next_empty_row)

# resultado_final = []
# for i in historico_compras:
#     if i not in result:
#         resultado_final.append(i)

# sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
#                       range=range,
#                       valueInputOption="USER_ENTERED",
#                       body={"values": resultado_final}).execute()
# print("Valor atualizado!")
# mensagem_final = 'Planilha do Cartão Caixa atualizada!'
# mensagem_bot_telegram(mensagem_final)
