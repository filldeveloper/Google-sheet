"""Configuração central do projeto.

Todos os valores sensíveis (senhas, tokens, caminhos) vêm de variáveis de
ambiente. Para desenvolvimento local, copie `.env.example` para `.env` e
preencha os valores: o arquivo `.env` é carregado automaticamente.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _get(nome, padrao=None, obrigatorio=False):
    valor = os.getenv(nome, padrao)
    if obrigatorio and not valor:
        raise RuntimeError(
            f"Variável de ambiente '{nome}' não definida. "
            "Confira o arquivo .env (veja .env.example)."
        )
    return valor


def exigir(nome):
    """Retorna a variável de ambiente ou falha com uma mensagem clara."""
    return _get(nome, obrigatorio=True)


# Google Sheets
GOOGLE_SERVICE_ACCOUNT_FILE = _get(
    "GOOGLE_SERVICE_ACCOUNT_FILE", str(BASE_DIR / "keys.json")
)
SPREADSHEET_ID = _get("SPREADSHEET_ID")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Banco do Brasil
BB_AGENCIA = _get("BB_AGENCIA")
BB_CONTA = _get("BB_CONTA")
BB_SENHA = _get("BB_SENHA")

# Caixa (a senha é a sequência de posições no teclado virtual, ex: 31415926)
CAIXA_USUARIO = _get("CAIXA_USUARIO")
CAIXA_SENHA = _get("CAIXA_SENHA")

# Telegram
TELEGRAM_TOKEN = _get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = _get("TELEGRAM_CHAT_ID")

# WhatsApp Cloud API
WHATSAPP_PHONE_ID = _get("WHATSAPP_PHONE_ID")
WHATSAPP_TOKEN = _get("WHATSAPP_TOKEN")
WHATSAPP_NUMBER = _get("WHATSAPP_NUMBER")

# E-mail (Gmail: use uma senha de app, não a senha da conta)
GMAIL_USER = _get("GMAIL_USER")
GMAIL_APP_PASSWORD = _get("GMAIL_APP_PASSWORD")
EMAIL_DESTINATARIO = _get("EMAIL_DESTINATARIO")
