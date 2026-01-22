import resend
from flask import render_template_string
import os

resend.api_key = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "Agenda+ <suporte@agendarmais.com>")

VERIFICATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
.content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
.button { display: inline-block; background-color: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
.footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>Agenda+</h1></div>
<div class="content">
<h2>Confirme seu email</h2>
<p>Ola <strong>{{ name }}</strong>,</p>
<p>Obrigado por se cadastrar no Agenda+! Para completar seu cadastro, confirme seu email:</p>
<p style="text-align: center;"><a href="{{ verification_url }}" class="button">Confirmar Email</a></p>
<p>Ou acesse: <span style="color: #4F46E5;">{{ verification_url }}</span></p>
<p><strong>Este link expira em 24 horas.</strong></p>
</div>
<div class="footer"><p>Agenda+ - Sistema de Agendamentos</p></div>
</div>
</body>
</html>
"""

PROFESSIONAL_INVITE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
.content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
.button { display: inline-block; background-color: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
.footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
.highlight { background-color: #e0e7ff; padding: 15px; border-radius: 6px; margin: 15px 0; }
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>Agenda+</h1><p>Portal do Profissional</p></div>
<div class="content">
<h2>Voce foi convidado!</h2>
<p>Ola <strong>{{ professional_name }}</strong>,</p>
<p>Voce recebeu um convite para o <strong>Portal do Profissional</strong> do Agenda+.</p>
<div class="highlight">
<p><strong>Com o portal voce podera:</strong></p>
<ul><li>Visualizar sua agenda</li><li>Gerenciar horarios</li><li>Acompanhar estatisticas</li></ul>
</div>
<p style="text-align: center;"><a href="{{ activation_url }}" class="button">Ativar Minha Conta</a></p>
<p>Ou acesse: <span style="color: #4F46E5;">{{ activation_url }}</span></p>
<p><strong>Este link expira em 48 horas.</strong></p>
</div>
<div class="footer"><p>Agenda+ - Sistema de Agendamentos</p></div>
</div>
</body>
</html>
"""

PROFESSIONAL_RESET_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background-color: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
.content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
.button { display: inline-block; background-color: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
.footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
.warning { background-color: #fef3c7; padding: 15px; border-radius: 6px; margin: 15px 0; border-left: 4px solid #f59e0b; }
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>Agenda+</h1><p>Portal do Profissional</p></div>
<div class="content">
<h2>Recuperacao de Senha</h2>
<p>Ola <strong>{{ professional_name }}</strong>,</p>
<p>Recebemos uma solicitacao para redefinir sua senha.</p>
<p style="text-align: center;"><a href="{{ reset_url }}" class="button">Redefinir Senha</a></p>
<p>Ou acesse: <span style="color: #4F46E5;">{{ reset_url }}</span></p>
<div class="warning">
<p><strong>Atencao:</strong> Este link expira em 1 hora.</p>
<p>Se voce nao solicitou, ignore este email.</p>
</div>
</div>
<div class="footer"><p>Agenda+ - Sistema de Agendamentos</p></div>
</div>
</body>
</html>
"""


def send_email(subject, recipient, html_body, text_body=None):
    """Envia um email generico usando Resend"""
    try:
        params = {
            "from": FROM_EMAIL,
            "to": [recipient],
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            params["text"] = text_body
        response = resend.Emails.send(params)
        print(f"Email enviado com sucesso: {response}")
        return True, "Email enviado com sucesso"
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False, str(e)


def send_verification_email(user, verification_url):
    """Envia email de verificacao de cadastro"""
    from datetime import datetime
    html_body = render_template_string(
        VERIFICATION_EMAIL_TEMPLATE,
        name=user.name,
        verification_url=verification_url,
        year=datetime.now().year
    )
    text_body = f"Ola {user.name}, para confirmar seu email acesse: {verification_url}"
    return send_email(
        subject="Confirme seu email - Agenda+",
        recipient=user.email,
        html_body=html_body,
        text_body=text_body
    )


def send_professional_invite_email(email, professional_name, activation_url):
    """Envia email de convite para profissional"""
    from datetime import datetime
    html_body = render_template_string(
        PROFESSIONAL_INVITE_TEMPLATE,
        professional_name=professional_name,
        activation_url=activation_url,
        year=datetime.now().year
    )
    text_body = f"Ola {professional_name}, voce foi convidado para o Portal do Profissional. Acesse: {activation_url}"
    return send_email(
        subject="Voce foi convidado para o Portal do Profissional - Agenda+",
        recipient=email,
        html_body=html_body,
        text_body=text_body
    )


def send_professional_reset_email(email, professional_name, reset_url):
    """Envia email de recuperacao de senha para profissional"""
    from datetime import datetime
    html_body = render_template_string(
        PROFESSIONAL_RESET_TEMPLATE,
        professional_name=professional_name,
        reset_url=reset_url,
        year=datetime.now().year
    )
    text_body = f"Ola {professional_name}, para redefinir sua senha acesse: {reset_url}"
    return send_email(
        subject="Recuperacao de Senha - Portal do Profissional - Agenda+",
        recipient=email,
        html_body=html_body,
        text_body=text_body
    )

