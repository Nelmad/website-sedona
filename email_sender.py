import smtplib
import email.utils
from email.mime.text import MIMEText


def mime_text_factory(author: str, recipients: list, subject: str = '', msg: str = '') -> MIMEText:
    msg = MIMEText(msg)
    msg['To'] = email.utils.formataddr(('Recipient', ', '.join(recipients)))
    msg['From'] = email.utils.formataddr(('Python Sedona', author))
    msg['Subject'] = subject
    return msg


def send_message(address, port, login, password, msg, debug=False):
    server = smtplib.SMTP(address, port)
    server.set_debuglevel(debug)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(login, password)

    try:
        server.sendmail(msg.get('From'), msg.get('To').split(', '), msg.as_string())
    finally:
        server.quit()
