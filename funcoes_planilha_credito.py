from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd 
from time import sleep
from pprint import pprint
import credenciais


def extrato_bb():

    options = webdriver.ChromeOptions()
    # options.add_argument('--no-sandbox')
    # options.add_argument('--headless')
    # options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-blink-features=AutomationControlled')
    url = 'https://www2.bancobrasil.com.br/aapf/login.html?1638208647003#/acesso-aapf-agencia-conta-1'

    chrome = webdriver.Chrome(
        options=options,
        service=ChromeService(ChromeDriverManager().install())
        )

    chrome.get(url)
    sleep(7)

    agencia = credenciais.agencia_bb
    conta = credenciais.conta_bb
    senha = credenciais.senha_bb

    # Preencher o campo agência
    chrome.find_element(By.ID,"dependenciaOrigem").send_keys(agencia)
    # Preencher o campo conta e apertar enter
    chrome.find_element(
        By.ID,"numeroContratoOrigem"
        ).send_keys(conta, Keys.ENTER)
    sleep(4)

    # Preencher o campo senha e apertar Enter
    chrome.find_element(By.ID,"senhaConta").send_keys(senha, Keys.ENTER)
    sleep(10)

    # Digita Cartões no campo de busca e aperta Enter
    chrome.find_element(By.ID,"acheFacil").send_keys("cartões", Keys.ENTER)
    sleep(3)

    # Escolhe a opção de extrato e entra
    act = ActionChains(chrome)
    act.click(chrome.find_element(
        By.XPATH,"//a[contains(text(),'Cartões - Fatura - Extrato')]"
        )).perform()
    sleep(7)

    # Seleciona o Cartão Elo Nanquim
    chrome.find_element(By.XPATH,'//*[@id="carousel1"]/div/div/img[2]').click()
    sleep(3)

    # Extrair a data de fechamento da próxima fatura
    chrome.find_element(By.XPATH,'//*[@id="faturasAtual"]/li[11]/a').click()
    sleep(2)

    elemento = chrome.find_element(
        By.XPATH,'//*[@id="fatura2"]/table/tbody/tr[4]/td/div/ul/li/span'
        )
    html_content = elemento.get_attribute('outerHTML')
    soup = BeautifulSoup(html_content, 'html.parser')
    fechamento_fatura_elo = soup.get_text('\n')
    print(fechamento_fatura_elo)
    sleep(5)

    # Clica em fatura atual para ver os histórico de compras recente
    chrome.find_element(By.XPATH,"//*[@id='faturasAtual']/li[12]").click()
    sleep(2)

    # Rola a página para baixo
    chrome.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    sleep(4)

    # Captura a tabela de informações presente na página
    elo_nanquim = []
    try:
        elemento = chrome.find_element(
            By.XPATH,"//*[@id='fatura2']/div[9]/table")
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
        elo_nanquim = []
        for linha in historico_compras['extrato']:

            if 'PARC=' in linha['Descrição']:
                xparcelas = int(linha['Descrição'][7])
                lista.append(linha['Data'])
                lista.append(linha['Descrição'][8:-1])
                lista.append(int(linha['Valor'])/100)
                lista.append(xparcelas)
                elo_nanquim.append(lista)
                lista = []
            else:
                lista.append(linha['Data'])
                lista.append(linha['Descrição'])
                lista.append(int(linha['Valor'])/100)
                lista.append(0)
                elo_nanquim.append(lista)
                lista = []
    except Exception as err:
        print(err)
    
    # Seleciona o Cartão Smiles Visa Infinite
    chrome.execute_script("window.scrollTo(0,0)")
    sleep(2)

    # Selecionar cartão Elo Nanquim
    chrome.find_element(By.XPATH,'//*[@id="carousel1"]/div/div/img[3]').click()
    sleep(2)

    chrome.find_element(By.CLASS_NAME,"inactive").click()
    sleep(2)

    chrome.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    sleep(4)

    visa = []
    try:
        elemento = chrome.find_element(
            By.XPATH,"//*[@id='fatura2']/div[9]//table")
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
        visa = []
        for linha in historico_compras['extrato']:

            if 'PARC=' in linha['Descrição']:
                xparcelas = int(linha['Descrição'][7])
                lista.append(linha['Data'])
                lista.append(linha['Descrição'][8:-1])
                lista.append(int(linha['Valor'])/100)
                lista.append(xparcelas)
                visa.append(lista)
                lista = []
            else:
                lista.append(linha['Data'])
                lista.append(linha['Descrição'])
                lista.append(int(linha['Valor'])/100)
                lista.append(0)
                visa.append(lista)
                lista = []
    except Exception as err:
        print(err)

    lista_definitiva = visa + elo_nanquim

    chrome.close()
    return visa, elo_nanquim, fechamento_fatura_elo, chrome


def extrato_caixa():
    options = webdriver.ChromeOptions()
    # options.add_argument('--no-sandbox')
    # options.add_argument('--headless')
    # options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    url = 'https://internetbanking.caixa.gov.br/sinbc/#!nb/login'

    chrome = webdriver.Chrome(
        options=options,
        service=ChromeService(ChromeDriverManager().install())
        )
    chrome.get(url)
    sleep(7)

    usuario = credenciais.usuario_caixa
    for letra in usuario:
        chrome.find_element(By.ID,"nomeUsuario").send_keys(letra)
        sleep(0.3)
    chrome.find_element(By.NAME,"btnLogin").click()
    sleep(4)

    # Clicar no botão 
    chrome.find_element(By.ID,'lnkInitials').click()
    sleep(4)

    # Inserção de senha no teclado virtual
    chrome.find_element(By.XPATH,f'//*[@id="teclado"]/ul/li[{credenciais.senha_caixa[0]}]').click()
    sleep(1)
    chrome.find_element(By.XPATH,f'//*[@id="teclado"]/ul/li[{credenciais.senha_caixa[1]}]').click()
    sleep(1)
    chrome.find_element(By.XPATH,f'//*[@id="teclado"]/ul/li[{credenciais.senha_caixa[2]}]').click()
    sleep(1)
    chrome.find_element(By.XPATH,f'//*[@id="teclado"]/ul/li[{credenciais.senha_caixa[3]}]').click()
    sleep(1)
    chrome.find_element(By.XPATH,f'//*[@id="teclado"]/ul/li[{credenciais.senha_caixa[4]}]').click()
    sleep(1)
    chrome.find_element(By.XPATH,f'//*[@id="teclado"]/ul/li[{credenciais.senha_caixa[5]}]').click()
    sleep(1)
    chrome.find_element(By.XPATH,f'//*[@id="teclado"]/ul/li[{credenciais.senha_caixa[6]}]').click()
    sleep(1)
    chrome.find_element(By.XPATH,f'//*[@id="teclado"]/ul/li[{credenciais.senha_caixa[7]}]').click()
    sleep(1)
    chrome.find_element(By.ID,'btnConfirmar').click()
    sleep(9)

    # Caso exista o popup de promoção, clicar em fechar
    try:
        chrome.find_element(By.NAME,'btnPromoFechar').click()
    except Exception:
        print("Não possuía o popup de promoção")
    sleep(4)

    # Clicando em cartões na home
    chrome.find_element(
        By.XPATH,
        '//*[@id="carrosselLista"]/li[2]/div[1]/div').click()
    sleep(4)

    # Clicando em Faturas para pegar a data de fechamento
    chrome.find_element(
        By.XPATH,
        '//*[@id="submenu"]/div[3]/ul/li[2]/a').click()
    sleep(4)

    chrome.find_element(By.XPATH,'//*[@id="linhaTabelaInicio"]/tr[2]').click()
    sleep(3)

    elemento = chrome.find_element(By.XPATH,'//*[@id="tb_list_Inicio"]')
    html_content = elemento.get_attribute('outerHTML')
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find(name='table')
    table_content = pd.read_html(str(table))[0]
    data_fechamento = table_content[[0, 1]]
    data = data_fechamento.to_dict('records')
    data_definitiva = data[1][1]
    print(f'A data de fechamento da próxima fatura é: {data_definitiva}')

    # Volta para a home
    chrome.find_element(
        By.XPATH,
        '//*[@id="home"]/div[1]/div[2]/div[2]/div[2]/div/div[1]/div').click()
    sleep(3)

    # Clicando em cartões
    chrome.find_element(
        By.XPATH,
        '//*[@id="carrosselLista"]/li[2]/div[1]/div').click()
    sleep(2)

    # Histórico de compras
    chrome.find_element(
        By.XPATH,
        '//*[@id="submenu"]/div[3]/ul/li[3]/a').click()
    sleep(4)

    # Rolar página para baixo e carregar o HTML caso esteja oculto ainda
    chrome.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    sleep(2)

    elemento = chrome.find_element(By.XPATH,'//*[@id="tb_list_Inicio"]')
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

        # Condição que verifica se a compra foi parcelada, se for envia o número de parcelas
        valor = linha[1].split('R$ ')
        if 'Parcelado em' in valor[0]:
            valor_total = valor[1].split(' ')[0]
            xparcelas = int(valor[0].split(' ')[2])
            lista.append(valor_total)
            lista.append(xparcelas)
            caixa.append(lista)
            lista = []
        # Se não for parcelada envia uma flag 0
        else:
            valor = valor[1].split(' ')[0]
            xparcelas = 0
            lista.append(valor)
            lista.append(xparcelas)
            caixa.append(lista)
            lista = []
    
    chrome.close()


    return caixa, data_definitiva