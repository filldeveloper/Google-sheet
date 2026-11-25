import smtplib
import ssl
import email.message

import config

msg = email.message.Message()
msg['Subject'] = "Parem de me cobrar"
body = f"""
<p>Olá, Cobrafix</p>
<p>Solicito por gentileza que parem de me enviar e-mails de cobrança.</p>
<p>Parem tb de me ligar.</p>
<p>Essa atitude de vcs de ficarem me ameaçando é ridícula.</p>
<p>Atenciosamente</p>
"""

msg['From'] = config.exigir('GMAIL_USER')
msg['To'] = config.exigir('EMAIL_DESTINATARIO')
password = config.exigir('GMAIL_APP_PASSWORD')
msg.add_header('Content-Type', 'text/html')
msg.set_payload(body)

context = ssl.create_default_context()
with smtplib.SMTP('smtp.gmail.com', 587) as conexao:
    conexao.ehlo()
    conexao.starttls(context=context)
    conexao.login(msg['From'], password)
    conexao.sendmail(msg['From'], msg['To'],
                     msg.as_string().encode('utf-8'))
