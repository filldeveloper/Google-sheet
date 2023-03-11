from googleapiclient.discovery import build
from google.oauth2 import service_account
from funcoes_planilha_credito import extrato_bb, extrato_caixa
from datetime import datetime, date
from time import mktime
import time
from pprint import pprint


# Chamando a função que pega os valores do extrato CAIXA
try:
    cartao_caixa = extrato_caixa()
    data_proxima_fatura = cartao_caixa[1]
    historico_compras = cartao_caixa[0]

    dicionario_meses = {1: "janeiro", 2: "fevereiro", 3: "março",
                        4: "abril", 5: "maio", 6: "junho",
                        7: "julho", 8: "agosto", 9: "setembro",
                        10: "outubro", 11: "novembro", 12: "dezembro"}

    aba_mes = int(data_proxima_fatura.split('/')[1]) + 1
    if aba_mes == 13:
        aba_mes = 1

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
            # Condição onde verifica se compra foi parcelada. Se sim, alimentar planilha de acordo
            if gasto[3]: # Se vier com a flag de parcelado
                valor_total = float(gasto[2].replace(',', '.'))
                xparcelas = gasto[3]
                valor_parcela = str(round((valor_total / xparcelas),2)).replace('.', ',')
                valor_parcela = 'R$ ' + valor_parcela
                print(gasto)

                # Loop que fará o registro das parcelas de acordo
                count = 1
                while count <= xparcelas:
                    parcela = [gasto[0], f'{gasto[1]} {count}/{xparcelas}', valor_parcela]
                    # Pegando todos os gastos armazenados e determinando a próxima linha vazia
                    range = f'{dicionario_meses[mes_gasto + count]}!B2:D100'
                    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=range).execute().get('values', [])
                    next_empty_row = len(result) + 2
                    # Condição que compara se gasto se foi armazenado
                    if parcela not in result:
                        # Armazenando os gastos na planilha
                        range = f'{dicionario_meses[mes_gasto + count]}!B{next_empty_row}'
                        sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=range,
                                    valueInputOption="USER_ENTERED",
                                    body={"values": [parcela]}).execute()
        
                    count += 1
            else: # Se a flag de gasto parcelado vier 0
                valor_gasto = 'R$ ' + gasto[2]
                parcela = [gasto[0], gasto[1], valor_gasto]
                # Pegando todos os gastos armazenados e determinando a próxima linha vazia
                range = f'{dicionario_meses[mes_gasto+1]}!B2:D100'
                result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=range).execute().get('values', [])
                next_empty_row = len(result) + 2
                print(parcela)

                # Condição que compara se gasto se foi armazenado
                if parcela not in result:
                    # Armazenando os gastos na planilha
                    range = f'{dicionario_meses[mes_gasto+1]}!B{next_empty_row}'
                    sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=range,
                                valueInputOption="USER_ENTERED",
                                body={"values": [parcela]}).execute()
        else:
            # Condição onde verifica se compra foi parcelada. Se sim, alimentar planilha de acordo
            if gasto[3]: # Se vier com a flag de parcelado
                valor_total = float(gasto[2].replace(',', '.'))
                xparcelas = gasto[3]
                valor_parcela = str(round((valor_total / xparcelas),2)).replace('.', ',')
                valor_parcela = 'R$ ' + valor_parcela
                print(gasto)

                # Loop que fará o registro das parcelas de acordo
                count = 1
                while count <= xparcelas:
                    parcela = [gasto[0], f'{gasto[1]} {count}/{xparcelas}', valor_parcela]
                    # Pegando todos os gastos armazenados e determinando a próxima linha vazia
                    range = f'{dicionario_meses[mes_gasto + count + 1]}!B2:D100'
                    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                        range=range).execute().get('values', [])
                    next_empty_row = len(result) + 2
                    # Condição que compara se gasto se foi armazenado
                    if parcela not in result:
                        # Armazenando os gastos na planilha
                        range = f'{dicionario_meses[mes_gasto + count + 1]}!B{next_empty_row}'
                        sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=range,
                                    valueInputOption="USER_ENTERED",
                                    body={"values": [parcela]}).execute()
        
                    count += 1
            else:# Se a flag de gasto parcelado vier 0
                valor_gasto = 'R$ ' + gasto[2]
                parcela = [gasto[0], gasto[1], valor_gasto]
                # Pegando todos os gastos armazenados e determinando a próxima linha vazia
                range = f'{dicionario_meses[mes_gasto+2]}!B2:D100'
                result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=range).execute().get('values', [])
                next_empty_row = len(result) + 2

                # Condição que compara se gasto se foi armazenado
                if parcela not in result:
                    # Armazenando os gastos na planilha
                    range = f'{dicionario_meses[mes_gasto+2]}!B{next_empty_row}'
                    sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=range,
                                valueInputOption="USER_ENTERED",
                                body={"values": [parcela]}).execute()

    # Fechar objeto de conexão com a api do googlesheet
    sheet.close()
except:
    print('ERRO NO SCRIPT DA CAIXA!')
    
time.sleep(5)
# --------------------------------------------------------------------------------------

# Início da coleta de gastos dos cartões do Banco do Brasil
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
ano_atual = data_atual.year

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

# Enviar mensagem via telegram caso exista gasto a ser adicionado
# Alimentar a planilha com os dados do cartão Visa
for gasto in historico_compras:
    mes_gasto = int(gasto[0].split('/')[1])
    data_gasto = f'{gasto[0]}/{ano_atual}'

    # Transformar data de gasto em timestamp
    timestamp_data_gasto = mktime(datetime.strptime(
                                data_gasto, '%d/%m/%Y').timetuple())

    # Pegar data de fechamento equivalente ao mês do gasto
    range = f'{dicionario_meses[mes_gasto+1]}!F11'
    fechamento_anterior = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                        range=range).execute().get('values', [])[0][0]
    
    # Transformar data de fechamento em timestamp
    timestamp_data_fechamento = mktime(datetime.strptime(
                                fechamento_anterior, '%d/%m/%Y').timetuple())

    # Condição que determina qual mês o gasto será armazenado
    if timestamp_data_gasto < timestamp_data_fechamento:
        # Condição que verifica se o gasto foi parcelado
        if gasto[3]: # Se vier a flag de parcelado
            valor_total = float(gasto[2])
            xparcelas = gasto[3]
            valor_parcela = round((valor_total / xparcelas),2)
            valor_parcela = ("{:.2f}".format(valor_parcela)).replace('.', ',')
            valor_parcela = 'R$ ' + valor_parcela

            # Loop que fará o registro das parcelas de acordo
            count = 1
            while count <= xparcelas:
                parcela = [gasto[0], f'{gasto[1]} {count}/{xparcelas}', valor_parcela]
                # Pegando todos os gastos armazenados e determinando a próxima linha vazia
                range = f'{dicionario_meses[mes_gasto + count]}!H2:J100'
                result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=range).execute().get('values', [])
                next_empty_row = len(result) + 2
                # Condição que compara se gasto se foi armazenado
                if parcela not in result:
                    # Armazenando os gastos na planilha
                    range = f'{dicionario_meses[mes_gasto + count]}!H{next_empty_row}'
                    sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=range,
                                valueInputOption="USER_ENTERED",
                                body={"values": [parcela]}).execute()
                count += 1

        else: # Se a flag de gasto parcelado vier 0
            valor_gasto = 'R$ ' + ("{:.2f}".format(gasto[2])).replace('.', ',')

            # Condição para corrigir a inserção de valores maiores que um mil
            if len(valor_gasto) > 9:
                valor_gasto = valor_gasto[:4] + '.' + valor_gasto[4:]

            parcela = [gasto[0], gasto[1], valor_gasto]
            # Pegando todos os gastos armazenados e determinando a próxima linha vazia
            range = f'{dicionario_meses[mes_gasto+1]}!H2:J100'
            result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=range).execute().get('values', [])
            next_empty_row = len(result) + 2
            print(parcela)

            # Condição que compara se gasto se foi armazenado
            if parcela not in result:
                # Armazenando os gastos na planilha
                range = f'{dicionario_meses[mes_gasto+1]}!H{next_empty_row}'
                sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range,
                            valueInputOption="USER_ENTERED",
                            body={"values": [parcela]}).execute()
                
    else: # Se a compra for feita no mês anterior ao do fechamento da fatura
        # Condição que verifica se o gasto foi parcelado
        if gasto[3]: # Se vier a flag de parcelado
            valor_total = float(gasto[2])
            xparcelas = gasto[3]
            valor_parcela = round((valor_total / xparcelas),2)
            valor_parcela = ("{:.2f}".format(valor_parcela)).replace('.', ',')
            valor_parcela = 'R$ ' + valor_parcela
            print(gasto)

            # Loop que fará o registro das parcelas de acordo
            count = 1
            while count <= xparcelas:
                parcela = [gasto[0], f'{gasto[1]} {count}/{xparcelas}', valor_parcela]
                # Pegando todos os gastos armazenados e determinando a próxima linha vazia
                range = f'{dicionario_meses[mes_gasto + count + 1]}!H2:J100'
                result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=range).execute().get('values', [])
                next_empty_row = len(result) + 2
                # Condição que compara se gasto se foi armazenado
                if parcela not in result:
                    # Armazenando os gastos na planilha
                    range = f'{dicionario_meses[mes_gasto + count + 1]}!H{next_empty_row}'
                    sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=range,
                                valueInputOption="USER_ENTERED",
                                body={"values": [parcela]}).execute()
    
                count += 1
        else: # Se a flag de gasto parcelado vier 0
            valor_gasto = 'R$ ' + ("{:.2f}".format(gasto[2])).replace('.', ',')

            # Condição para corrigir a inserção de valores maiores que um mil
            if len(valor_gasto) > 9:
                valor_gasto = valor_gasto[:4] + '.' + valor_gasto[4:]
                
            parcela = [gasto[0], gasto[1], valor_gasto]
            # Pegando todos os gastos armazenados e determinando a próxima linha vazia
            range = f'{dicionario_meses[mes_gasto+2]}!H2:J100'
            result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=range).execute().get('values', [])
            next_empty_row = len(result) + 2
            print(parcela)

            # Condição que compara se gasto se foi armazenado
            if parcela not in result:
                # Armazenando os gastos na planilha
                range = f'{dicionario_meses[mes_gasto+2]}!H{next_empty_row}'
                sheet.values().update(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=range,
                            valueInputOption="USER_ENTERED",
                            body={"values": [parcela]}).execute()
            
# Fechar objeto de conexão com a api do googlesheet
sheet.close()