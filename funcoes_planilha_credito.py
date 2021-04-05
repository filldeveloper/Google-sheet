from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
from pprint import pprint
import credentials


def extrato_bb():

    option = Options()
    # option.headless = True
    chrome = webdriver.Chrome(options=option)
    chrome.get('https://www2.bancobrasil.com.br/aapf/login.jsp')

    time.sleep(10)

    agencia = credentials.agencia_bb
    conta = credentials.conta_bb
    senha = credentials.senha_bb
    # Preencher o campo agência
    chrome.find_element_by_id("dependenciaOrigem").send_keys(agencia)
    # Preencher o campo conta e apertar enter
    chrome.find_element_by_id(
        "numeroContratoOrigem").send_keys(conta, Keys.ENTER)

    time.sleep(4)
    # Preencher o campo senha e apertar Enter
    chrome.find_element_by_id("senhaConta").send_keys(senha, Keys.ENTER)

    time.sleep(6)
    # Digita Cartões no campo de busca e aperta Enter
    chrome.find_element_by_id("acheFacil").send_keys("cartões", Keys.ENTER)
    # Escolhe a opção de extrato e entra
    act = ActionChains(chrome)
    act.click(chrome.find_element_by_xpath(
        "//a[contains(text(),'Cartões - Fatura - Extrato')]")).perform()

    time.sleep(4)

    # Seleciona o Cartão Visa Infinite
    chrome.find_element_by_xpath('//*[@id="carousel1"]/div/div/img[1]').click()

    time.sleep(2)
    # Extrair a data de fechamento da próxima fatura
    elemento = chrome.find_element_by_xpath(
        '//*[@id="fatura2"]/table/tbody/tr[4]/td/div/ul/li/span')
    html_content = elemento.get_attribute('outerHTML')
    soup = BeautifulSoup(html_content, 'html.parser')
    fechamento_fatura_visa = soup.get_text('\n')
    time.sleep(2)
    # Clica em fatura atual para ver os histórico de compras recente
    chrome.find_element_by_xpath("//*[@id='faturasAtual']/li[12]").click()

    time.sleep(2)
    # Rola a página para baixo
    chrome.execute_script("window.scrollTo(0,document.body.scrollHeight)")

    time.sleep(4)
    # Captura a tabela de informações presente na página
    visa = []
    try:
        elemento = chrome.find_element_by_xpath(
            "//*[@id='fatura2']/div[9]//table")
        html_content = elemento.get_attribute('outerHTML')
        # Método organiza as informações em html
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find(name='table')
        # Método que extrai as informações do html e coloca num data frame
        extrato_full = pd.read_html(str(table))[0]
        extrato = extrato_full[[0, 1, 2]]
        extrato.columns = ['Data', 'Descrição', 'Valor']
        extrato = extrato.drop([0, 1], axis=0)
        # Extrai os dados do data frame e manda para um dicionário
        historico_compras = {}
        historico_compras['extrato'] = extrato.to_dict('records')

        lista = []
        visa = []
        for linha in historico_compras['extrato']:
            lista.append(linha['Data'])
            lista.append(linha['Descrição'])
            lista.append(int(linha['Valor'])/100)
            visa.append(lista)
            lista = []
    except Exception:
        print('Nenhum dado encontrado no extrato do cartão Visa')

    # Seleciona o Cartão Smiles
    chrome.execute_script("window.scrollTo(0,0)")

    time.sleep(3)

    chrome.find_element_by_xpath('//*[@id="carousel1"]/div/div/img[2]').click()

    time.sleep(2)

    elemento = chrome.find_element_by_xpath(
        '//*[@id="fatura2"]/table/tbody/tr[4]/td/div/ul/li/span')
    html_content = elemento.get_attribute('outerHTML')
    soup = BeautifulSoup(html_content, 'html.parser')
    fechamento_fatura_smiles = soup.get_text('\n')
    time.sleep(2)

    chrome.find_element_by_xpath("//*[@id='faturasAtual']/li[12]").click()

    time.sleep(2)

    chrome.execute_script("window.scrollTo(0,document.body.scrollHeight)")

    time.sleep(4)

    smiles = []
    try:
        elemento = chrome.find_element_by_xpath(
            "//*[@id='fatura2']/div[9]//table")
        html_content = elemento.get_attribute('outerHTML')

        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find(name='table')

        extrato_full = pd.read_html(str(table))[0]
        extrato = extrato_full[[0, 1, 2]]
        extrato.columns = ['Data', 'Descrição', 'Valor']
        extrato = extrato.drop([0, 1], axis=0)

        historico_compras = {}
        historico_compras['extrato'] = extrato.to_dict('records')

        lista = []
        smiles = []
        for linha in historico_compras['extrato']:
            lista.append(linha['Data'])
            lista.append(linha['Descrição'])
            lista.append(int(linha['Valor'])/100)
            smiles.append(lista)
            lista = []
    except Exception:
        print('Nenhum dado encontrado no extrato do cartão Smiles')

    # Seleciona o Cartão Elo Nanquim
    chrome.execute_script("window.scrollTo(0,0)")

    time.sleep(2)
    # Voltando para a imagem do cartão visa pra deixa a imagem do elo visível
    chrome.find_element_by_xpath('//*[@id="carousel1"]/div/div/img[1]').click()

    time.sleep(3)

    chrome.find_element_by_xpath('//*[@id="carousel1"]/div/div/img[4]').click()

    time.sleep(2)

    elemento = chrome.find_element_by_xpath(
        '//*[@id="fatura2"]/table/tbody/tr[4]/td/div/ul/li/span')
    html_content = elemento.get_attribute('outerHTML')
    soup = BeautifulSoup(html_content, 'html.parser')
    fechamento_fatura_elo = soup.get_text('\n')
    time.sleep(2)

    chrome.find_element_by_xpath("//*[@id='faturasAtual']/li[12]").click()

    time.sleep(2)

    chrome.execute_script("window.scrollTo(0,document.body.scrollHeight)")

    time.sleep(4)

    nanquim = []
    try:
        elemento = chrome.find_element_by_xpath(
            "//*[@id='fatura2']/div[9]//table")
        html_content = elemento.get_attribute('outerHTML')

        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find(name='table')

        extrato_full = pd.read_html(str(table))[0]
        extrato = extrato_full[[0, 1, 2]]
        extrato.columns = ['Data', 'Descrição', 'Valor']
        extrato = extrato.drop([0, 1], axis=0)

        historico_compras = {}
        historico_compras['extrato'] = extrato.to_dict('records')

        lista = []
        nanquim = []
        for linha in historico_compras['extrato']:
            lista.append(linha['Data'])
            lista.append(linha['Descrição'])
            lista.append(int(linha['Valor'])/100)
            nanquim.append(lista)
            lista = []
    except Exception:
        print('Nenhum dado encontrado no extrato do cartão Elo')

    # if visa:
    #     lista
    # if smiles:
    #     pprint(f'Extrato Smiles: {smiles}')
    # if nanquim:
    #     pprint(f'Extrato Nanquim: {nanquim}')

    lista_definitiva = visa + smiles + nanquim
    chrome.close()

    return visa, smiles, nanquim, fechamento_fatura_visa, fechamento_fatura_smiles, fechamento_fatura_elo


def extrato_caixa():
    option = Options()
    # option.headless = True
    chrome = webdriver.Chrome(options=option)
    chrome.get('https://internetbanking.caixa.gov.br/sinbc/#!nb/login')
    time.sleep(5)

    usuario = credentials.usuario_caixa

    chrome.find_element_by_id("nomeUsuario").send_keys(usuario)

    chrome.find_element_by_name("btnLogin").click()

    time.sleep(5)

    chrome.find_element_by_id('lnkInitials').click()

    time.sleep(5)

    # Inserção de senha no teclado virtual
    chrome.find_element_by_xpath('//*[@id="teclado"]/ul/li[15]').click()
    time.sleep(1)
    chrome.find_element_by_xpath('//*[@id="teclado"]/ul/li[27]').click()
    time.sleep(1)
    chrome.find_element_by_xpath('//*[@id="teclado"]/ul/li[22]').click()
    time.sleep(1)
    chrome.find_element_by_xpath('//*[@id="teclado"]/ul/li[18]').click()
    time.sleep(1)
    chrome.find_element_by_xpath('//*[@id="teclado"]/ul/li[23]').click()
    time.sleep(1)
    chrome.find_element_by_xpath('//*[@id="teclado"]/ul/li[13]').click()
    time.sleep(1)
    chrome.find_element_by_xpath('//*[@id="teclado"]/ul/li[2]').click()
    time.sleep(1)
    chrome.find_element_by_xpath('//*[@id="teclado"]/ul/li[3]').click()
    time.sleep(1)
    chrome.find_element_by_id('btnConfirmar').click()
    time.sleep(5)

    try:
        chrome.find_element_by_name('btnPromoFechar').click()
    except Exception:
        print("Não possuia o pop'up de promoção")
    time.sleep(5)

    chrome.find_element_by_id('btnAccountsExchange').click()
    time.sleep(2)

    chrome.find_element_by_id('1').click()
    time.sleep(8)
    # Clicando em cartões na home
    chrome.find_element_by_xpath(
        '//*[@id="carrosselLista"]/li[2]/div[1]/div').click()

    time.sleep(5)
    # Clicandoo em Faturas para pegar a data de fechamento
    chrome.find_element_by_xpath(
        '//*[@id="submenu"]/div[3]/ul/li[2]/a').click()

    time.sleep(5)

    chrome.find_element_by_xpath('//*[@id="linhaTabelaInicio"]/tr[2]').click()

    time.sleep(5)

    elemento = chrome.find_element_by_xpath('//*[@id="tb_list_Inicio"]')
    html_content = elemento.get_attribute('outerHTML')
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find(name='table')
    table_content = pd.read_html(str(table))[0]
    data_fechamento = table_content[[0, 1]]
    data = data_fechamento.to_dict('records')
    data_definitiva = data[1][1]
    print(f'A data de fechamento da próxima fatura é: {data_definitiva}')

    time.sleep(2)
    # Volta para a home
    chrome.find_element_by_xpath(
        '//*[@id="home"]/div[1]/div[2]/div[2]/div[2]/div/div[1]/div').click()

    time.sleep(4)

    # Clicando em cartões
    chrome.find_element_by_xpath(
        '//*[@id="carrosselLista"]/li[2]/div[1]/div').click()

    time.sleep(5)

    # Histórico de compras
    chrome.find_element_by_xpath(
        '//*[@id="submenu"]/div[3]/ul/li[3]/a').click()

    time.sleep(5)

    chrome.execute_script("window.scrollTo(0,document.body.scrollHeight)")

    time.sleep(5)

    elemento = chrome.find_element_by_xpath('//*[@id="tb_list_Inicio"]')
    html_content = elemento.get_attribute('outerHTML')
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find(name='table')

    extrato_full = pd.read_html(str(table))[0]

    extrato = extrato_full[[0, 1]]

    historico_compras = {}
    historico_compras['extrato'] = extrato.to_dict('records')

    lista = []
    caixa = []
    for linha in historico_compras['extrato']:
        if 'Cancelada' in linha[0]:
            continue
        elif 'Negada' in linha[0]:
            continue
        data = linha[0].split(' - ')
        data = data[0].split('-')
        data = data[0] + '/' + data[1] + '/' + data[2]
        lista.append(data)

        description = linha[0].split('Aprovada')
        description = description[0]
        description = description[22:-1]
        lista.append(description)

        valor = linha[1].split('R$ ')
        valor = valor[1].split(' ')
        valor = 'R$ ' + valor[0]
        lista.append(valor)
        caixa.append(lista)
        lista = []

    chrome.close()

    return caixa, data_definitiva


def mensagem_bot_telegram(mensagem):
    import requests
    import urllib.parse

    # Ler msgs que estão sendo mandadas para o bot
    chat_id = '-1001410402288'
    token = '1775549137:AAHNBuPFWmvq-K1aI2SHhojVqQC2unQBGoA'
    mensagem_bot = mensagem
    msg_url = urllib.parse.quote(mensagem_bot)
    # url_base = f'https://api.telegram.org/bot{token}/getUpdates'
    url_send = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={msg_url}'
    resultado = requests.post(url_send)

    return resultado
