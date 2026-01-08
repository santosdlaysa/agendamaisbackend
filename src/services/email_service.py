from flask_mail import Mail, Message
from flask import current_app, render_template_string
import os

mail = Mail()

# Template HTML para email de verificação
VERIFICATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
        .button { display: inline-block; background-color: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
        .footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
        .code { background-color: #e5e7eb; padding: 10px 20px; font-size: 24px; letter-spacing: 4px; border-radius: 4px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Agenda+</h1>
        </div>
        <div class="content">
            <h2>Confirme seu email</h2>
            <p>Olá <strong>{{ name }}</strong>,</p>
            <p>Obrigado por se cadastrar no Agenda+! Para completar seu cadastro, por favor confirme seu email clicando no botão abaixo:</p>

            <p style="text-align: center;">
                <a href="{{ verification_url }}" class="button">Confirmar Email</a>
            </p>

            <p>Ou copie e cole este link no seu navegador:</p>
            <p style="word-break: break-all; color: #4F46E5;">{{ verification_url }}</p>

            <p><strong>Este link expira em 24 horas.</strong></p>

            <p>Se você não criou uma conta no Agenda+, ignore este email.</p>
        </div>
        <div class="footer">
            <p>&copy; {{ year }} Agenda+ - Sistema de Agendamentos</p>
            <p>Este é um email automático, não responda.</p>
        </div>
    </div>
</body>
</html>
"""

def send_email(subject, recipient, html_body, text_body=None):
    """Envia um email genérico"""
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=html_body,
            body=text_body or html_body
        )
        mail.send(msg)
        return True, 'Email enviado com sucesso'
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False, str(e)


def send_verification_email(user, verification_url):
    """Envia email de verificação de cadastro"""
    from datetime import datetime

    html_body = render_template_string(
        VERIFICATION_EMAIL_TEMPLATE,
        name=user.name,
        verification_url=verification_url,
        year=datetime.now().year
    )

    text_body = f"""
    Olá {user.name},

    Obrigado por se cadastrar no Agenda+!

    Para confirmar seu email, acesse: {verification_url}

    Este link expira em 24 horas.

    Se você não criou uma conta no Agenda+, ignore este email.

    Agenda+ - Sistema de Agendamentos
    """

    return send_email(
        subject='Confirme seu email - Agenda+',
        recipient=user.email,
        html_body=html_body,
        text_body=text_body
    )
