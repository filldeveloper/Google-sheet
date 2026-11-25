"""Preenche a planilha de cartões com as transações vindas da Pluggy (Open Finance).

Substitui o scraping com Selenium. Cada cartão tem um bloco de colunas na aba do
mês e cada aba guarda os gastos da fatura que FECHA no mês anterior. Exemplo:
compras entre o fechamento de outubro e o fechamento de novembro vão para a aba
Dezembro.

Uso:
    python pluggy_cartoes.py --listar-contas   # mostra os cartões de cada item
    python pluggy_cartoes.py                   # só mostra o que seria gravado
    python pluggy_cartoes.py --gravar          # grava na planilha

Variáveis de ambiente:
    PLUGGY_CLIENT_ID, PLUGGY_CLIENT_SECRET     credenciais da aplicação Pluggy
    GOOGLE_APPLICATION_CREDENTIALS             caminho do JSON da conta de serviço
    CONFIG_CARTOES (opcional)                  caminho do config (padrão config_cartoes.json)
"""

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

import requests

API = "https://api.pluggy.ai"
BRT = timezone(timedelta(hours=-3))

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


# --------------------------------------------------------------------------
# Pluggy
# --------------------------------------------------------------------------

class Pluggy:
    def __init__(self, client_id, client_secret):
        r = requests.post(f"{API}/auth", json={"clientId": client_id,
                                               "clientSecret": client_secret},
                          timeout=30)
        r.raise_for_status()
        self.s = requests.Session()
        self.s.headers["X-API-KEY"] = r.json()["apiKey"]

    def get(self, path, **params):
        r = self.s.get(f"{API}{path}", params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    def contas_credito(self, item_id):
        return self.get("/accounts", itemId=item_id, type="CREDIT")["results"]

    def faturas(self, account_id):
        """{bill_id: data de vencimento} das faturas da conta."""
        try:
            dados = self.get("/bills", accountId=account_id, pageSize=500)
        except requests.HTTPError:
            return {}
        return {b["id"]: data_local(b["dueDate"])
                for b in dados.get("results", []) if b.get("dueDate")}

    def transacoes(self, account_id, desde):
        """Todas as transações da conta a partir de `desde` (cursor da v2)."""
        dados = self.get("/v2/transactions", accountId=account_id,
                         dateFrom=desde.isoformat())
        resultados = list(dados["results"])
        while dados.get("next"):
            r = self.s.get(f"{API}/v2/transactions{dados['next']}", timeout=60)
            r.raise_for_status()
            dados = r.json()
            resultados += dados["results"]
        return resultados


# --------------------------------------------------------------------------
# Regras de fatura
# --------------------------------------------------------------------------

def proximo_mes(ano, mes, n=1):
    total = ano * 12 + (mes - 1) + n
    return total // 12, total % 12 + 1


def data_local(iso):
    """Data (sem hora) de um campo da Pluggy.

    Usa a data como veio. Converter de UTC para Brasília joga as compras
    gravadas como 00:00 UTC para o dia anterior.
    """
    return date.fromisoformat(str(iso)[:10])


def parse_data_planilha(texto, ano_padrao):
    """'28/10', '3/10' ou '28/10/2026' -> date. None se não reconhecer."""
    m = re.match(r"^\s*(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\s*$", str(texto or ""))
    if not m:
        return None
    dia, mes, ano = int(m[1]), int(m[2]), m[3]
    ano = int(ano) if ano else ano_padrao
    if ano < 100:
        ano += 2000
    try:
        return date(ano, mes, dia)
    except ValueError:
        return None


def parse_valor(texto):
    """'R$ 1.234,56' -> 1234.56. Aceita número também."""
    if isinstance(texto, (int, float)):
        return round(float(texto), 2)
    t = str(texto or "").replace("R$", "").replace(" ", "").replace("\xa0", "")
    if not t:
        return None
    t = t.replace(".", "").replace(",", ".")
    try:
        return round(float(t), 2)
    except ValueError:
        return None


class Fechamentos:
    """Sabe a data de fechamento de cada aba (ano, mês) para um cartão.

    A aba (ano, mês) guarda a fatura que fecha no mês anterior. A data vem da
    célula de fechamento da aba quando preenchida. Senão, usa o dia de
    fechamento do config no mês anterior.
    """

    def __init__(self, planilha, cartao):
        self.planilha = planilha
        self.cartao = cartao
        self.cache = {}

    def da_aba(self, ano, mes):
        chave = (ano, mes)
        if chave not in self.cache:
            texto = self.planilha.ler_celula(ano, mes, self.cartao["celula_fechamento"])
            data = parse_data_planilha(texto, ano) if texto else None
            if data is not None and not self._plausivel(data, ano, mes):
                # Data velha copiada de outro ano (ex.: 24/12/2024 na aba
                # Janeiro de 2027). Ignora e usa o dia padrão.
                print(f"[{self.cartao['nome']}] {MESES[mes - 1]} {ano}: fechamento "
                      f"{texto} na planilha não bate com a aba, usando o dia "
                      f"{self.cartao['dia_fechamento']}.")
                data = None
            if data is None:
                a, m = proximo_mes(ano, mes, -1)
                dia = min(self.cartao["dia_fechamento"], 28)
                data = date(a, m, dia)
            self.cache[chave] = data
        return self.cache[chave]

    @staticmethod
    def _plausivel(data, ano, mes):
        """O fechamento da aba (ano, mes) tem que cair no mês anterior (ou na 1ª semana do mês)."""
        anterior = proximo_mes(ano, mes, -1)
        return ((data.year, data.month) == anterior
                or ((data.year, data.month) == (ano, mes) and data.day <= 7))

    def aba_da_compra(self, d):
        """Primeira aba cujo fechamento é depois da data da compra.

        Uma compra feita no dia do fechamento já vai para a fatura seguinte,
        igual ao script antigo.
        """
        # A fatura que fecha no mês da compra fica na aba do mês seguinte.
        ano, mes = proximo_mes(d.year, d.month, 1)
        for _ in range(3):
            if d < self.da_aba(ano, mes):
                return ano, mes
            ano, mes = proximo_mes(ano, mes, 1)
        return ano, mes


# --------------------------------------------------------------------------
# Google Sheets
# --------------------------------------------------------------------------

class Planilha:
    def __init__(self, planilhas_por_ano, credenciais, gravar):
        self.ids = {int(k): v for k, v in planilhas_por_ano.items()}
        self.gravar = gravar
        self._api = None
        self._credenciais = credenciais
        self.cache_celulas = {}

    @property
    def api(self):
        if self._api is None:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            creds = service_account.Credentials.from_service_account_file(
                self._credenciais,
                scopes=["https://www.googleapis.com/auth/spreadsheets"])
            self._api = build("sheets", "v4", credentials=creds).spreadsheets()
        return self._api

    def tem_ano(self, ano):
        return ano in self.ids

    def _get(self, ano, faixa):
        return self.api.values().get(spreadsheetId=self.ids[ano],
                                     range=faixa).execute().get("values", [])

    def ler_celula(self, ano, mes, celula):
        if not self.tem_ano(ano):
            return None
        chave = (ano, mes, celula)
        if chave not in self.cache_celulas:
            v = self._get(ano, f"{MESES[mes - 1]}!{celula}")
            self.cache_celulas[chave] = v[0][0] if v and v[0] else None
        return self.cache_celulas[chave]

    def ler_bloco(self, ano, mes, colunas):
        ini, fim = colunas.split(":")
        linhas = self._get(ano, f"{MESES[mes - 1]}!{ini}2:{fim}500")
        return [(l + ["", "", ""])[:3] for l in linhas]

    def escrever(self, ano, mes, faixa, valores):
        if not self.gravar:
            return
        self.api.values().update(
            spreadsheetId=self.ids[ano], range=f"{MESES[mes - 1]}!{faixa}",
            valueInputOption="USER_ENTERED",
            body={"values": valores}).execute()


# --------------------------------------------------------------------------
# Montagem das linhas
# --------------------------------------------------------------------------

def normalizar(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip()


PARC_RE = re.compile(r"\s*\bPARC(?:ELA)?\.?\s*(\d{1,2})\s*/\s*(\d{1,2})\b", re.I)
FIM_RE = re.compile(r"\s+(\d{1,2})\s*/\s*(\d{1,2})\s*$")


def limpar_descricao(texto):
    """Tira o 'PARC 09/10' do meio da descrição e devolve (descricao, k, n)."""
    t = normalizar(html.unescape(texto))
    k = n = None
    m = PARC_RE.search(t) or FIM_RE.search(t)
    if m:
        k, n = int(m[1]), int(m[2])
        t = (t[:m.start()] + t[m.end():]).strip()
    return re.sub(r"\s+", " ", t), k, n


def linhas_da_transacao(t, fechamentos, faturas):
    """Gera (aba, data_compra, descricao, valor, serie) da compra e das parcelas futuras.

    A aba vem da fatura em que o banco lançou a compra (mês do vencimento).
    Sem fatura (fatura ainda aberta), usa a data da transação e o fechamento.
    """
    valor = round(float(t["amount"]), 2)
    if valor <= 0:
        return []  # pagamento de fatura, estorno ou crédito

    meta = t.get("creditCardMetadata") or {}
    data_tx = data_local(t["date"])
    data_compra = data_local(meta.get("purchaseDate") or t["date"])
    descricao, k, n = limpar_descricao(t.get("description") or t.get("descriptionRaw") or "Compra")
    if not n:
        k = int(meta.get("installmentNumber") or 1)
        n = int(meta.get("totalInstallments") or 1)

    vencimento = faturas.get(meta.get("billId"))
    if vencimento:
        aba = (vencimento.year, vencimento.month)
    else:
        aba = fechamentos.aba_da_compra(data_tx if n > 1 else data_compra)

    if n <= 1:
        return [(aba, data_compra, descricao, valor, None)]
    # A mesma compra parcelada aparece uma vez por fatura, às vezes com data
    # diferente e com 1 centavo de diferença entre parcelas. O que identifica a
    # série é a descrição, o número de parcelas, o valor aproximado e a aba em
    # que cairia a 1ª parcela.
    serie = (descricao.lower(), n, round(valor), proximo_mes(*aba, -(k - 1)))
    # Esta parcela e as próximas, uma aba depois da outra.
    return [(proximo_mes(*aba, j - k), data_compra, f"{descricao} {j}/{n}", valor, (serie, j))
            for j in range(k, n + 1)]


def ja_existe(ja_tem, d, v):
    """Procura um gasto igual na planilha: mesmo valor (até 1 centavo) e data com até 1 dia de diferença.

    A descrição fica de fora de propósito: você costuma renomear os gastos na
    planilha, e isso não pode gerar duplicata.
    """
    for dd in (d, d - timedelta(days=1), d + timedelta(days=1)):
        for vv in (v, round(v - 0.01, 2), round(v + 0.01, 2)):
            if ja_tem[(dd.day, dd.month, vv)] > 0:
                ja_tem[(dd.day, dd.month, vv)] -= 1
                return True
    return False


def sincronizar_cartao(pluggy, planilha, cartao, desde, hoje, a_partir_de=None, depurar=False):
    fech = Fechamentos(planilha, cartao)
    contas = pluggy.contas_credito(cartao["item_id"])
    escolhidas = cartao.get("account_ids") or cartao.get("account_id") or []
    if isinstance(escolhidas, str):
        escolhidas = [escolhidas]
    if escolhidas:
        contas = [c for c in contas if c["id"] in escolhidas]
    if not contas:
        print(f"[{cartao['nome']}] nenhuma conta de cartão encontrada no item.")
        return

    por_aba = defaultdict(list)
    # Uma série de parcelas pode vir várias vezes (uma por fatura). Para
    # cada parcela, vale a que veio da fatura real, não a projetada.
    parcelas = {}
    for conta in contas:
        faturas = pluggy.faturas(conta["id"])
        sem_fatura = 0
        transacoes = pluggy.transacoes(conta["id"], desde)
        if depurar:
            print(f"[{cartao['nome']}] conta {conta.get('name')} final {conta.get('number')}:")
            for t in sorted(transacoes, key=lambda t: t["date"]):
                meta = t.get("creditCardMetadata") or {}
                print(f"    date={t['date'][:10]} purchaseDate={str(meta.get('purchaseDate'))[:10]}"
                      f" parcela={meta.get('installmentNumber')}/{meta.get('totalInstallments')}"
                      f" status={t.get('status')} bill={'sim' if meta.get('billId') else 'nao'}"
                      f" valor={t['amount']} | {t.get('description')}")
        for t in transacoes:
            if float(t["amount"]) > 0 and (t.get("creditCardMetadata") or {}).get("billId") not in faturas:
                sem_fatura += 1
            for i, (aba, d, desc, v, serie) in enumerate(linhas_da_transacao(t, fech, faturas)):
                if serie is None:
                    por_aba[aba].append((d, desc, v))
                elif serie not in parcelas or (i == 0 and parcelas[serie][1] != 0):
                    parcelas[serie] = ((aba, d, desc, v), i)

    # Todas as parcelas de uma série com a mesma data (a mais antiga vista).
    primeira = {}
    for (raiz, _j), ((_aba, d, _desc, _v), _i) in parcelas.items():
        primeira[raiz] = min(d, primeira.get(raiz, d))
    for (raiz, _j), ((aba, _d, desc, v), _i) in parcelas.items():
        por_aba[aba].append((primeira[raiz], desc, v))
    if depurar:
        return

    if a_partir_de is None:
        aba_atual = fech.aba_da_compra(hoje)
        a_partir_de = proximo_mes(*aba_atual, -1)
    for (ano, mes) in sorted(por_aba):
        nome_aba = f"{MESES[mes - 1]} {ano}"
        if (ano, mes) < a_partir_de:
            continue
        if not planilha.tem_ano(ano):
            print(f"[{cartao['nome']}] {nome_aba}: sem planilha para {ano} no config, pulando.")
            continue

        existentes = planilha.ler_bloco(ano, mes, cartao["colunas"])
        ja_tem = Counter()
        for d_txt, _desc, v_txt in existentes:
            d = parse_data_planilha(d_txt, ano)
            v = parse_valor(v_txt)
            if d and v is not None:
                ja_tem[(d.day, d.month, v)] += 1

        sufixo = cartao.get("sufixo_descricao", "").strip()
        novas = []
        for d, desc, v in sorted(por_aba[(ano, mes)]):
            if not ja_existe(ja_tem, d, v):
                novas.append([d.strftime("%d/%m/%Y"), f"{desc} {sufixo}" if sufixo else desc, v])

        if not novas:
            print(f"[{cartao['nome']}] {nome_aba}: nada novo.")
            continue

        # Primeira linha vazia depois do último gasto do bloco.
        ultima = max((i for i, l in enumerate(existentes) if any(c for c in l)),
                     default=-1)
        linha = ultima + 3  # +2 pelo cabeçalho na linha 1, +1 para a próxima
        ini, fim = cartao["colunas"].split(":")
        print(f"[{cartao['nome']}] {nome_aba}: {len(novas)} gasto(s) novo(s)"
              f"{'' if planilha.gravar else ' (teste, nada gravado)'}")
        for n in novas:
            print(f"    {n[0]}  {n[1]:<45}  R$ {n[2]:>10.2f}")
        planilha.escrever(ano, mes, f"{ini}{linha}:{fim}{linha + len(novas) - 1}", novas)

    # Data de fechamento da fatura aberta, se a célula estiver vazia.
    for conta in contas:
        fecha = (conta.get("creditData") or {}).get("balanceCloseDate")
        if not fecha:
            continue
        d = data_local(fecha)
        ano, mes = proximo_mes(d.year, d.month, 1)
        if planilha.tem_ano(ano) and not planilha.ler_celula(ano, mes, cartao["celula_fechamento"]):
            print(f"[{cartao['nome']}] {MESES[mes - 1]} {ano}: fechamento {d:%d/%m/%Y}")
            planilha.escrever(ano, mes, cartao["celula_fechamento"], [[d.strftime("%d/%m/%Y")]])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gravar", action="store_true",
                    help="grava na planilha (sem isso, só mostra o que faria)")
    ap.add_argument("--listar-contas", action="store_true",
                    help="lista os cartões de cada item_id do config e sai")
    ap.add_argument("--a-partir-de", metavar="MM/AAAA",
                    help="só mexe nas abas a partir deste mês (ex.: 01/2027). "
                         "Padrão: a fatura que acabou de fechar e as seguintes")
    ap.add_argument("--depurar", action="store_true",
                    help="mostra os dados brutos de cada transação e não grava nada")
    ap.add_argument("--dias", type=int, default=75,
                    help="quantos dias para trás buscar (padrão 75)")
    args = ap.parse_args()

    with open(os.environ.get("CONFIG_CARTOES", "config_cartoes.json"), encoding="utf-8") as f:
        config = json.load(f)

    try:
        pluggy = Pluggy(os.environ["PLUGGY_CLIENT_ID"], os.environ["PLUGGY_CLIENT_SECRET"])
    except KeyError as e:
        sys.exit(f"Defina a variável de ambiente {e.args[0]}.")

    if args.listar_contas:
        for cartao in config["cartoes"]:
            print(f"{cartao['nome']} (item {cartao['item_id']}):")
            for c in pluggy.contas_credito(cartao["item_id"]):
                cd = c.get("creditData") or {}
                print(f"  account_id={c['id']}  {c.get('name')}  final {c.get('number')}"
                      f"  fecha {cd.get('balanceCloseDate')}  vence {cd.get('balanceDueDate')}")
        return

    planilha = Planilha(config["planilhas_por_ano"],
                        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "keys.json"),
                        gravar=args.gravar)
    hoje = datetime.now(BRT).date()
    desde = hoje - timedelta(days=args.dias)
    a_partir_de = None
    if args.a_partir_de:
        m, a = args.a_partir_de.split("/")
        a_partir_de = (int(a), int(m))
    for cartao in config["cartoes"]:
        sincronizar_cartao(pluggy, planilha, cartao, desde, hoje, a_partir_de, args.depurar)


if __name__ == "__main__":
    main()
