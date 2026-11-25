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
    """Converte o ISO8601 UTC da Pluggy para a data no horário de Brasília."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BRT).date()


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
            if data is None:
                a, m = proximo_mes(ano, mes, -1)
                dia = min(self.cartao["dia_fechamento"], 28)
                data = date(a, m, dia)
            self.cache[chave] = data
        return self.cache[chave]

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


def linhas_da_transacao(t, fechamentos):
    """Gera (aba, data_compra, descricao, valor) para a compra e parcelas futuras."""
    valor = round(float(t["amount"]), 2)
    if valor <= 0:
        return []  # pagamento de fatura, estorno ou crédito

    meta = t.get("creditCardMetadata") or {}
    data_compra = data_local(meta.get("purchaseDate") or t["date"])
    parcela = int(meta.get("installmentNumber") or 1)
    total_parcelas = int(meta.get("totalInstallments") or 1)
    descricao = normalizar(t.get("description") or t.get("descriptionRaw") or "Compra")
    # Tira um "3/10" que o banco já tenha posto na descrição.
    descricao = re.sub(r"\s*(?:parc(?:ela)?\.?\s*)?\d{1,2}\s*/\s*\d{1,2}\s*$", "",
                       descricao, flags=re.I)

    ano, mes = fechamentos.aba_da_compra(data_compra)
    linhas = []
    if total_parcelas <= 1:
        linhas.append(((ano, mes), data_compra, descricao, valor))
    else:
        # A 1ª parcela cai na aba da compra; a k-ésima, k-1 abas depois.
        for k in range(parcela, total_parcelas + 1):
            aba = proximo_mes(ano, mes, k - 1)
            linhas.append((aba, data_compra, f"{descricao} {k}/{total_parcelas}", valor))
    return linhas


def chave(data_compra, valor):
    """Identifica um gasto pela data (dia/mês) e valor.

    A descrição fica de fora de propósito: você costuma renomear os gastos na
    planilha, e isso não pode gerar duplicata.
    """
    return (data_compra.day, data_compra.month, round(valor, 2))


def sincronizar_cartao(pluggy, planilha, cartao, desde, hoje):
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
    parcelas_vistas = set()
    for conta in contas:
        for t in pluggy.transacoes(conta["id"], desde):
            for aba, d, desc, v in linhas_da_transacao(t, fech):
                if re.search(r" \d+/\d+$", desc):
                    # A Pluggy pode mandar a 1ª parcela e também as futuras
                    # (pendentes). Cada parcela entra uma vez só.
                    if (aba, d, desc, v) in parcelas_vistas:
                        continue
                    parcelas_vistas.add((aba, d, desc, v))
                por_aba[aba].append((d, desc, v))

    aba_atual = fech.aba_da_compra(hoje)
    for (ano, mes) in sorted(por_aba):
        nome_aba = f"{MESES[mes - 1]} {ano}"
        if not planilha.tem_ano(ano):
            print(f"[{cartao['nome']}] {nome_aba}: sem planilha para {ano} no config, pulando.")
            continue
        if (ano, mes) < proximo_mes(*aba_atual, -1) and not cartao.get("reescrever_passado"):
            # Fatura já fechada e paga: não mexe no que você já conferiu.
            continue

        existentes = planilha.ler_bloco(ano, mes, cartao["colunas"])
        ja_tem = Counter()
        for d_txt, _desc, v_txt in existentes:
            d = parse_data_planilha(d_txt, ano)
            v = parse_valor(v_txt)
            if d and v is not None:
                ja_tem[chave(d, v)] += 1

        novas = []
        for d, desc, v in sorted(por_aba[(ano, mes)]):
            k = chave(d, v)
            if ja_tem[k] > 0:
                ja_tem[k] -= 1
                continue
            novas.append([d.strftime("%d/%m/%Y"), desc, v])

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
    for cartao in config["cartoes"]:
        sincronizar_cartao(pluggy, planilha, cartao, desde, hoje)


if __name__ == "__main__":
    main()
