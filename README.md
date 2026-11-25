# Google Sheet: gastos do cartão de crédito

Automação que lê as faturas dos cartões (Caixa e Banco do Brasil: Elo Nanquim e Smiles Visa) e preenche uma planilha do Google Sheets com os gastos de cada mês, incluindo compras parceladas.

## Como funciona

- `funcoes_planilha_credito.py`: funções que entram no site dos bancos com Selenium e extraem os lançamentos (`extrato_caixa`, `extrato_bb`).
- `read.py`: script principal. Chama os extratos e grava os gastos na planilha, uma aba por mês (`janeiro` … `dezembro`).
  - Caixa: colunas `B:D`, data de fechamento em `F5`.
  - Banco do Brasil: colunas `H:J`, data de fechamento em `F11`.
- `config.py`: lê todas as configurações e senhas de variáveis de ambiente (ou do arquivo `.env`).
- `bot_telegram.py`, `conversation_bot.py`, `teste.py`: experimentos com bot do Telegram.
- `send_mail.py`: envio de e-mail pelo Gmail.

## Instalação

Requer Python 3.10+ e o Google Chrome instalado.

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

## Configuração

1. Copie o modelo e preencha os valores:

   ```bash
   cp .env.example .env
   ```

2. Crie uma conta de serviço no Google Cloud com a API do Google Sheets ativada, baixe a chave JSON e salve como `keys.json` na pasta do projeto (ou aponte outro caminho em `GOOGLE_SERVICE_ACCOUNT_FILE`).
3. Compartilhe a planilha com o e-mail da conta de serviço (permissão de editor) e coloque o ID da planilha em `SPREADSHEET_ID`. O ID é o trecho da URL entre `/d/` e `/edit`.
4. Para o Gmail, use uma [senha de app](https://myaccount.google.com/apppasswords), nunca a senha da conta.

| Variável | Para que serve |
| --- | --- |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Caminho do JSON da conta de serviço (padrão: `./keys.json`) |
| `SPREADSHEET_ID` | ID da planilha |
| `BB_AGENCIA`, `BB_CONTA`, `BB_SENHA` | Acesso ao Banco do Brasil |
| `CAIXA_USUARIO`, `CAIXA_SENHA` | Acesso à Caixa (a senha é a sequência de posições do teclado virtual) |
| `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` | Bot do Telegram |
| `WHATSAPP_PHONE_ID`, `WHATSAPP_TOKEN`, `WHATSAPP_NUMBER` | WhatsApp Cloud API |
| `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `EMAIL_DESTINATARIO` | Envio de e-mail |

Os arquivos `.env`, `keys.json` e `credenciais.py` estão no `.gitignore` e não devem ser commitados.

## Uso

```bash
python read.py
```

## Segurança

Versões antigas deste repositório tinham segredos no código e no histórico do git (chave da conta de serviço, token do Telegram e senha do Gmail). Esses valores devem ser considerados vazados: revogue a chave da conta de serviço no Google Cloud, gere um novo token no @BotFather e troque a senha do Gmail.
