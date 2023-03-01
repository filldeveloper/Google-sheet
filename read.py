from googleapiclient.discovery import build
from google.oauth2 import service_account
from funcoes_planilha_credito import extrato_bb, extrato_caixa
from datetime import datetime, date
import time
from pprint import pprint

lista_definitiva = extrato_bb()

historico_compras_visa = lista_definitiva[0]
historico_compras_nanquim = lista_definitiva[1]
fechamento_fatura = lista_definitiva[2]

dicionario_meses = {1: "janeiro", 2: "fevereiro", 3: "março",
                    4: "abril", 5: "maio", 6: "junho",
                    7: "julho", 8: "agosto", 9: "setembro",
                    10: "outubro", 11: "novembro", 12: "dezembro"}

aba_mes = int(fechamento_fatura.split('/')[1]) + 1
if aba_mes == 13:
    aba_mes = 1

# Setar o range da aba mês api!C2 - Fechamento da Fatura
range_aba = f'{dicionario_meses[aba_mes]}!F11'

# Pegar data atual para decidir qual mês irei adicionar os dados
data_atual = date.today() 
data_atual = f'{data_atual.day}/{data_atual.month}/{data_atual.year}'

# Juntar as duas listas de gastos
historico_compras = historico_compras_visa + historico_compras_nanquim

print(f'Fechamento da próxima fatura Visa: {fechamento_fatura}')
print(f'Histórico de compras Visa: {historico_compras_visa}')
print(f'Histórico de compras Elo Nanquim: {historico_compras_nanquim}')


SERVICE_ACCOUNT_FILE = "C:\\Users\\S027668971\\Developments\\Google-sheet\\keys.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = None
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID spreadsheet.
SAMPLE_SPREADSHEET_ID = '1QhNbaGgEAUzUL_FhOI5xfqTe643xI7lxmpKysub8lPI'
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Inserir data de fechamento da fatura visa
sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                    range=range_aba,
                    valueInputOption="USER_ENTERED",
                    body={"values": [[fechamento_fatura]]}).execute()

# Update da Sheets
descricao_compra = []
for gasto in historico_compras:
    preço = str(f'{gasto[2]:.2f}').split('.')
    gasto[2] = "R$ " + preço[0] + "," + preço[1]
    descricao_compra.append(gasto)

# O número da aba será coletado de acordo com a data do gasto
ano = int(data_atual.split('/')[2])

# Pegando dados da planilha de gastos. Cartão Smiles
range = f'{dicionario_meses[aba_mes]}!H2:J100'
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])

# Formatar dados coletados par uma melhor comparação
planilha = []
for row in result:
    data = row[0].split('/')
    row[0] = data[0] + "/" + data[1]
    planilha.append(row)

# Comparando os gastos com os valores já na planilha
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
    mes_gasto = int(gasto[0].split('/')[1])
    mes_fechamento_fatura = int(fechamento_planilha.split('/')[1])
    if numero_aba == 13:
            numero_aba = 1
    # if mes_gasto > numero_aba:
    #     data_gasto = f'{gasto[0]}/{ano-1}'
    
    data_gasto = f'{gasto[0]}/{ano}'

    timestamp_data_gasto = time.mktime(datetime.strptime(
                                data_gasto, '%d/%m/%Y').timetuple())

    if timestamp_data_gasto < timestamp_fechamento:

        validador_msg = 1
        if mes_gasto < mes_fechamento_fatura:
            range = f'{dicionario_meses[numero_aba+1]}!H2:J100'
            result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=range).execute().get('values', [])
            next_empty_row = len(result) + 2
            range = f'{dicionario_meses[numero_aba+1]}!H{next_empty_row}'
            sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range=range,
                        valueInputOption="USER_ENTERED",
                        body={"values": [gasto]}).execute()
        else:
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
            if "*" in mensagem_gasto:
                mensagem_gasto = mensagem_gasto.replace('*', '\*')
            # telegram_bot(mensagem_gasto)

            validador_msg = 1
            next_empty_row = len(result) + 2
            range = f'{dicionario_meses[numero_aba]}!H{next_empty_row}'
            sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range=range,
                        valueInputOption="USER_ENTERED",
                        body={"values": [gasto]}).execute()
            
# Fechar objeto de conexão com a api do googlesheet
sheet.close()

# --------------------------------------------------------------------------------------

# Chamando a função que pega os valores do extrato CAIXA
chrome = lista_definitiva[-1]
cartao_caixa = extrato_caixa(chrome)
data_proxima_fatura = cartao_caixa[1]
historico_compras = cartao_caixa[0]

# Setar o range da aba mês - Fechamento da Fatura Caixa
range_fechamento = f'{dicionario_meses[aba_mes]}!F5'

SERVICE_ACCOUNT_FILE = "C:\\Users\\S027668971\\Developments\\Google-sheet\\keys.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = None
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID spreadsheet.
SAMPLE_SPREADSHEET_ID = '1QhNbaGgEAUzUL_FhOI5xfqTe643xI7lxmpKysub8lPI'
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Inserir data de fechamento da fatura visa
sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                    range=range_fechamento,
                    valueInputOption="USER_ENTERED",
                    body={"values": [[data_proxima_fatura]]}).execute()


for gasto in historico_compras:
    mes_gasto = int(gasto[0].split('/')[1])
    data_gasto = gasto[0]

    # Transformar data de gasto em timestamp
    timestamp_data_gasto = time.mktime(datetime.strptime(
                                data_gasto, '%d/%m/%Y').timetuple())
    
    # Pegar data de fechamento equivalente ao mês do gasto
    range = f'{dicionario_meses[mes_gasto+1]}!F5'
    fechamento_anterior = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range=range).execute().get('values', [])[0][0]
    
    # Transformar data de fechamento em timestamp
    timestamp_data_fechamento = time.mktime(datetime.strptime(
                                fechamento_anterior, '%d/%m/%Y').timetuple())
    
    # Condição em que determina qual mês o gasto será armazenado
    if timestamp_data_gasto < timestamp_data_fechamento:
        # Pegando todos os gastos armazenados e determinando a próxima linha vazia
        range = f'{dicionario_meses[mes_gasto+1]}!B2:D100'
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])
        next_empty_row = len(result) + 2

        # Condição que compara se gasto se foi armazenado
        if gasto not in result:
            # Armazenando os gastos na planilha
            range = f'{dicionario_meses[mes_gasto+1]}!B{next_empty_row}'
            sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range=range,
                        valueInputOption="USER_ENTERED",
                        body={"values": [gasto]}).execute()
    else:
        # Pegando todos os gastos armazenados e determinando a próxima linha vazia
        range = f'{dicionario_meses[mes_gasto+2]}!B2:D100'
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range).execute().get('values', [])
        next_empty_row = len(result) + 2

        # Condição que compara se gasto se foi armazenado
        if gasto not in result:
            # Armazenando os gastos na planilha
            range = f'{dicionario_meses[mes_gasto+2]}!B{next_empty_row}'
            sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range=range,
                        valueInputOption="USER_ENTERED",
                        body={"values": [gasto]}).execute()

# Fechar objeto de conexão com a api do googlesheet
sheet.close()