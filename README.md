# Google-sheet

Preenche a planilha de cartões (Cartões 2026, 2027...) com os gastos do cartão de crédito.

## Pluggy (atual)

`pluggy_cartoes.py` busca as transações dos cartões no Open Finance pela Pluggy (Meu Pluggy)
e grava cada gasto no bloco do cartão, na aba da fatura certa. Substitui o scraping com Selenium.

Regra das abas: a aba de um mês guarda a fatura que fecha no mês anterior. Uma compra feita
antes do fechamento de novembro vai para Dezembro; uma compra no dia do fechamento ou depois
vai para a aba seguinte. A data de fechamento vem da célula de fechamento da aba (F5 para o
Nubank, F11 para o BB). Se ela estiver vazia, o script usa o `dia_fechamento` do config, e
preenche a célula com a data que a Pluggy informar para a fatura aberta.

Quando a Pluggy informa a fatura da compra, a aba é o mês do vencimento dessa fatura (vale também
para as parcelas). As datas de fechamento só são usadas para a fatura ainda aberta.

Compras parceladas: cada parcela vai para a aba correspondente, com "k/n" na descrição, e as
parcelas futuras já são lançadas nas abas seguintes.

Para não duplicar, um gasto é reconhecido pela data da compra (dia/mês, com 1 dia de folga) e pelo
valor (com 1 centavo de folga). A
descrição não entra na comparação, então você pode renomear os gastos na planilha à vontade.

Por padrão, só mexe da fatura que acabou de fechar em diante. Use `--a-partir-de 01/2027` para
começar de uma aba específica (útil para não mexer em abas que você já preencheu à mão).

### Configuração

1. No dashboard da Pluggy, crie uma Development Application e pegue o `client_id` e o `client_secret`
   (o secret vale 180 dias).
2. Copie `config_cartoes.example.json` para `config_cartoes.json` e cole o `item_id` de cada banco
   (aparece no dashboard da Pluggy). Rode `python pluggy_cartoes.py --listar-contas` para ver os
   cartões de cada item; se um item tiver mais de um cartão, coloque em `account_ids` só os que entram no bloco
   (vazio = todos os cartões do item).
3. Compartilhe as planilhas de cada ano (como editor) com o e-mail da conta de serviço do Google.
4. Defina as variáveis de ambiente:

```
export PLUGGY_CLIENT_ID=...
export PLUGGY_CLIENT_SECRET=...
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/conta-de-servico.json
```

`sufixo_descricao` (opcional) é um texto colocado no fim de toda descrição daquele cartão,
por exemplo o nome de quem usa o cartão.

### Uso

```
pip install -r requirements.txt
python pluggy_cartoes.py            # modo teste: só mostra o que seria gravado
python pluggy_cartoes.py --gravar   # grava na planilha
```

### Rodar todo dia (GitHub Actions)

O workflow `.github/workflows/cartoes-diario.yml` roda `python pluggy_cartoes.py --gravar` todo dia
às 7h (horário de Brasília). Ele precisa de 4 Secrets, cadastrados em **Settings → Secrets and
variables → Actions → New repository secret**:

| Secret | Conteúdo |
| --- | --- |
| `PLUGGY_CLIENT_ID` | o `client_id` da Pluggy |
| `PLUGGY_CLIENT_SECRET` | o `client_secret` da Pluggy (vence em 180 dias; atualize aqui quando trocar) |
| `GOOGLE_CREDENTIALS_JSON` | o conteúdo inteiro do JSON da conta de serviço (`keys.json`) |
| `CONFIG_CARTOES_JSON` | o conteúdo inteiro do seu `config_cartoes.json` |

Para testar, abra a aba **Actions**, escolha "Preencher planilha de cartões" e clique em
**Run workflow**. Com a caixa "gravar" desmarcada, ele só mostra no log o que seria gravado.
Quando uma execução falha, o GitHub manda e-mail.

## Scripts antigos

`read.py` e `funcoes_planilha_credito.py` faziam scraping da Caixa e do BB com Selenium e não
funcionam mais.
