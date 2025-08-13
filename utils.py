import smtplib
from email.mime.text import MIMEText
from flask import url_for
from email_config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL
import re

def send_reset_email(to_email, token):
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    subject = 'Сброс пароля для ERP-приложения'
    body = f'''
    Здравствуйте,

    Администратор инициировал сброс вашего пароля. Пожалуйста, перейдите по следующей ссылке, чтобы установить новый пароль:
    {reset_url}

    Ссылка действительна в течение 1 часа. Если вы не запрашивали сброс пароля, обратитесь к администратору.

    С уважением,
    Команда ERP
    '''
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False
    return True

def validate_password(password):
    """
    Проверяет сложность пароля.
    Возвращает кортеж (is_valid, message).
    """
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов."
    if not re.search(r"[A-Z]", password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву."
    if not re.search(r"[a-z]", password):
        return False, "Пароль должен содержать хотя бы одну строчную букву."
    if not re.search(r"\d", password):
        return False, "Пароль должен содержать хотя бы одну цифру."
    if not re.search(r"[!@#$%^&*]", password):
        return False, "Пароль должен содержать хотя бы один специальный символ (!@#$%^&*)."
    return True, "Пароль соответствует требованиям."