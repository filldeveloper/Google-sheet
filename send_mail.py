import smtplib
import ssl
import email.message

msg = email.message.Message()
msg['Subject'] = "Parem de me cobrar"
body = f"""
<p>Olá, Cobrafix</p>
<p>Solicito por gentileza que parem de me enviar e-mails de cobrança.</p>
<p>Parem tb de me ligar.</p>
<p>Essa atitude de vcs de ficarem me ameaçando é ridícula.</p>
<p>Atenciosamente</p>
"""

msg['From'] = 'felipebobsponja@gmail.com'
msg['To'] = 'boleto@grupocobrafix.com.br'
password = 'serpro10'
msg.add_header('Content-Type', 'text/html')
msg.set_payload(body)

context = ssl.create_default_context()
with smtplib.SMTP('smtp.gmail.com', 587) as conexao:
    conexao.ehlo()
    conexao.starttls(context=context)
    conexao.login(msg['From'], password)
    while True:
        conexao.sendmail(msg['From'], msg['To'],
                         msg.as_string().encode('utf-8'))
