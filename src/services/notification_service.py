"""
Serviço unificado de notificações para o sistema AgendaMais.
Centraliza o envio de notificações por Email, SMS e WhatsApp.
"""
import os
from datetime import datetime
from flask import render_template_string
from src.services.email_service import send_email
from src.services.twilio_service import send_whatsapp, send_sms, is_twilio_configured

# Tipos de notificação
NOTIFICATION_TYPES = {
    'NEW_CLIENT': 'new_client',
    'APPOINTMENT_CREATED': 'appointment_created',
    'APPOINTMENT_CONFIRMED': 'appointment_confirmed',
    'APPOINTMENT_CANCELLED': 'appointment_cancelled',
    'APPOINTMENT_RESCHEDULED': 'appointment_rescheduled',
    'APPOINTMENT_COMPLETED': 'appointment_completed',
    'APPOINTMENT_REMINDER': 'appointment_reminder',
}

# Templates de Email
NEW_CLIENT_EMAIL_TEMPLATE = """
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
<div class="header"><h1>{{ business_name }}</h1><p>Bem-vindo!</p></div>
<div class="content">
<h2>Ola {{ client_name }}!</h2>
<p>Seu cadastro foi realizado com sucesso na <strong>{{ business_name }}</strong>.</p>
<div class="highlight">
<p><strong>Agora voce pode:</strong></p>
<ul>
<li>Agendar servicos online</li>
<li>Acompanhar seus agendamentos</li>
<li>Receber lembretes automaticos</li>
</ul>
</div>
{% if booking_url %}
<p style="text-align: center;"><a href="{{ booking_url }}" class="button">Agendar Agora</a></p>
{% endif %}
<p>Obrigado por escolher a {{ business_name }}!</p>
</div>
<div class="footer"><p>{{ business_name }} - Powered by Agenda+</p></div>
</div>
</body>
</html>
"""

APPOINTMENT_CREATED_EMAIL_TEMPLATE = """
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
.appointment-box { background-color: #e0e7ff; padding: 20px; border-radius: 6px; margin: 15px 0; }
.detail-row { margin: 8px 0; }
.label { font-weight: bold; color: #4F46E5; }
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>{{ business_name }}</h1><p>Agendamento Realizado!</p></div>
<div class="content">
<h2>Ola {{ client_name }}!</h2>
<p>Seu agendamento foi realizado com sucesso.</p>
<div class="appointment-box">
<div class="detail-row"><span class="label">Data:</span> {{ appointment_date }}</div>
<div class="detail-row"><span class="label">Horario:</span> {{ appointment_time }}</div>
<div class="detail-row"><span class="label">Servico:</span> {{ service_name }}</div>
<div class="detail-row"><span class="label">Profissional:</span> {{ professional_name }}</div>
{% if booking_code %}
<div class="detail-row"><span class="label">Codigo:</span> {{ booking_code }}</div>
{% endif %}
{% if price %}
<div class="detail-row"><span class="label">Valor:</span> R$ {{ price }}</div>
{% endif %}
</div>
{% if confirmation_url %}
<p style="text-align: center;"><a href="{{ confirmation_url }}" class="button">Confirmar Agendamento</a></p>
{% endif %}
<p><strong>Importante:</strong> Em caso de imprevisto, por favor entre em contato para reagendar.</p>
</div>
<div class="footer"><p>{{ business_name }} - Powered by Agenda+</p></div>
</div>
</body>
</html>
"""

APPOINTMENT_CONFIRMED_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background-color: #10B981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
.content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
.footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
.appointment-box { background-color: #d1fae5; padding: 20px; border-radius: 6px; margin: 15px 0; }
.detail-row { margin: 8px 0; }
.label { font-weight: bold; color: #059669; }
.success-icon { font-size: 48px; margin-bottom: 10px; }
</style>
</head>
<body>
<div class="container">
<div class="header"><div class="success-icon">&#10004;</div><h1>Agendamento Confirmado!</h1></div>
<div class="content">
<h2>Ola {{ client_name }}!</h2>
<p>Seu agendamento foi confirmado com sucesso.</p>
<div class="appointment-box">
<div class="detail-row"><span class="label">Data:</span> {{ appointment_date }}</div>
<div class="detail-row"><span class="label">Horario:</span> {{ appointment_time }}</div>
<div class="detail-row"><span class="label">Servico:</span> {{ service_name }}</div>
<div class="detail-row"><span class="label">Profissional:</span> {{ professional_name }}</div>
</div>
<p>Aguardamos voce!</p>
</div>
<div class="footer"><p>{{ business_name }} - Powered by Agenda+</p></div>
</div>
</body>
</html>
"""

APPOINTMENT_CANCELLED_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background-color: #EF4444; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
.content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
.button { display: inline-block; background-color: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
.footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
.appointment-box { background-color: #fee2e2; padding: 20px; border-radius: 6px; margin: 15px 0; }
.detail-row { margin: 8px 0; }
.label { font-weight: bold; color: #DC2626; }
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>Agendamento Cancelado</h1></div>
<div class="content">
<h2>Ola {{ client_name }},</h2>
<p>Seu agendamento foi cancelado.</p>
<div class="appointment-box">
<div class="detail-row"><span class="label">Data:</span> {{ appointment_date }}</div>
<div class="detail-row"><span class="label">Horario:</span> {{ appointment_time }}</div>
<div class="detail-row"><span class="label">Servico:</span> {{ service_name }}</div>
{% if cancellation_reason %}
<div class="detail-row"><span class="label">Motivo:</span> {{ cancellation_reason }}</div>
{% endif %}
</div>
{% if booking_url %}
<p>Deseja reagendar?</p>
<p style="text-align: center;"><a href="{{ booking_url }}" class="button">Fazer Novo Agendamento</a></p>
{% endif %}
</div>
<div class="footer"><p>{{ business_name }} - Powered by Agenda+</p></div>
</div>
</body>
</html>
"""

APPOINTMENT_RESCHEDULED_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background-color: #F59E0B; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
.content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
.footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
.appointment-box { background-color: #fef3c7; padding: 20px; border-radius: 6px; margin: 15px 0; }
.old-schedule { text-decoration: line-through; color: #9CA3AF; }
.new-schedule { color: #059669; font-weight: bold; }
.detail-row { margin: 8px 0; }
.label { font-weight: bold; color: #D97706; }
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>Agendamento Reagendado</h1></div>
<div class="content">
<h2>Ola {{ client_name }},</h2>
<p>Seu agendamento foi reagendado.</p>
<div class="appointment-box">
{% if old_date and old_time %}
<div class="detail-row"><span class="label">Anterior:</span> <span class="old-schedule">{{ old_date }} as {{ old_time }}</span></div>
{% endif %}
<div class="detail-row"><span class="label">Nova Data:</span> <span class="new-schedule">{{ appointment_date }}</span></div>
<div class="detail-row"><span class="label">Novo Horario:</span> <span class="new-schedule">{{ appointment_time }}</span></div>
<div class="detail-row"><span class="label">Servico:</span> {{ service_name }}</div>
<div class="detail-row"><span class="label">Profissional:</span> {{ professional_name }}</div>
</div>
<p>Aguardamos voce no novo horario!</p>
</div>
<div class="footer"><p>{{ business_name }} - Powered by Agenda+</p></div>
</div>
</body>
</html>
"""

APPOINTMENT_COMPLETED_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
.container { max-width: 600px; margin: 0 auto; padding: 20px; }
.header { background-color: #10B981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
.content { background-color: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
.button { display: inline-block; background-color: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
.footer { text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }
.receipt-box { background-color: #d1fae5; padding: 20px; border-radius: 6px; margin: 15px 0; border: 2px dashed #10B981; }
.detail-row { margin: 8px 0; }
.label { font-weight: bold; color: #059669; }
.total { font-size: 24px; color: #059669; font-weight: bold; margin-top: 15px; }
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>Obrigado pela visita!</h1></div>
<div class="content">
<h2>Ola {{ client_name }}!</h2>
<p>Esperamos que tenha gostado do atendimento.</p>
<div class="receipt-box">
<h3>Resumo do Atendimento</h3>
<div class="detail-row"><span class="label">Data:</span> {{ appointment_date }}</div>
<div class="detail-row"><span class="label">Servico:</span> {{ service_name }}</div>
<div class="detail-row"><span class="label">Profissional:</span> {{ professional_name }}</div>
{% if price %}
<div class="total">Total: R$ {{ price }}</div>
{% endif %}
{% if payment_method %}
<div class="detail-row"><span class="label">Pagamento:</span> {{ payment_method }}</div>
{% endif %}
</div>
{% if booking_url %}
<p>Deseja agendar novamente?</p>
<p style="text-align: center;"><a href="{{ booking_url }}" class="button">Agendar Novamente</a></p>
{% endif %}
<p>Obrigado por escolher a {{ business_name }}!</p>
</div>
<div class="footer"><p>{{ business_name }} - Powered by Agenda+</p></div>
</div>
</body>
</html>
"""


# ============================================
# MENSAGENS WHATSAPP / SMS
# ============================================

def create_new_client_message(client_name, business_name, booking_url=None):
    """Cria mensagem de boas-vindas para novo cliente"""
    message = f"""Ola {client_name}!

Bem-vindo(a) a {business_name}!

Seu cadastro foi realizado com sucesso. Agora voce pode agendar servicos e receber lembretes automaticos.
"""
    if booking_url:
        message += f"\nPara agendar, acesse:\n{booking_url}\n"

    message += f"\nObrigado por nos escolher!\n{business_name}"
    return message


def create_appointment_created_message(client_name, appointment_date, appointment_time,
                                       service_name, professional_name, business_name,
                                       booking_code=None, price=None):
    """Cria mensagem de agendamento criado"""
    message = f"""Ola {client_name}!

Seu agendamento foi realizado na {business_name}:

Data: {appointment_date}
Horario: {appointment_time}
Servico: {service_name}
Profissional: {professional_name}
"""
    if booking_code:
        message += f"Codigo: {booking_code}\n"

    if price:
        message += f"Valor: R$ {price:.2f}\n"

    message += f"\nEm caso de imprevisto, entre em contato para reagendar.\n\nAguardamos voce!\n{business_name}"
    return message


def create_appointment_confirmed_message(client_name, appointment_date, appointment_time,
                                         service_name, business_name):
    """Cria mensagem de agendamento confirmado"""
    return f"""Agendamento Confirmado!

Ola {client_name},

Seu agendamento foi confirmado:

Data: {appointment_date}
Horario: {appointment_time}
Servico: {service_name}

Aguardamos voce!
{business_name}"""


def create_appointment_cancelled_message(client_name, appointment_date, appointment_time,
                                         service_name, business_name, reason=None):
    """Cria mensagem de agendamento cancelado"""
    message = f"""Agendamento Cancelado

Ola {client_name},

Seu agendamento para {appointment_date} as {appointment_time} foi cancelado.
Servico: {service_name}
"""
    if reason:
        message += f"Motivo: {reason}\n"

    message += f"\nPara reagendar, entre em contato.\n{business_name}"
    return message


def create_appointment_rescheduled_message(client_name, old_date, old_time, new_date, new_time,
                                           service_name, professional_name, business_name):
    """Cria mensagem de agendamento reagendado"""
    return f"""Agendamento Reagendado

Ola {client_name},

Seu agendamento foi alterado:

Anterior: {old_date} as {old_time}
Novo: {new_date} as {new_time}
Servico: {service_name}
Profissional: {professional_name}

Aguardamos voce no novo horario!
{business_name}"""


def create_appointment_completed_message(client_name, service_name, professional_name,
                                         business_name, price=None):
    """Cria mensagem de agendamento concluido"""
    message = f"""Obrigado pela visita!

Ola {client_name},

Esperamos que tenha gostado do atendimento.

Servico: {service_name}
Profissional: {professional_name}
"""
    if price:
        message += f"Valor: R$ {price:.2f}\n"

    message += f"\nObrigado por escolher a {business_name}!"
    return message


# ============================================
# FUNCOES PRINCIPAIS DE ENVIO
# ============================================

class NotificationResult:
    """Classe para resultado de notificacao"""
    def __init__(self, success=False, channel=None, message_id=None, error=None):
        self.success = success
        self.channel = channel
        self.message_id = message_id
        self.error = error

    def to_dict(self):
        return {
            'success': self.success,
            'channel': self.channel,
            'message_id': self.message_id,
            'error': self.error
        }


class NotificationService:
    """Servico centralizado de notificacoes"""

    @staticmethod
    def send_new_client_notification(client, business_name, booking_url=None,
                                     channels=None):
        """
        Envia notificacao de boas-vindas para novo cliente.

        Args:
            client: Objeto Client com name, email, phone
            business_name: Nome do estabelecimento
            booking_url: URL para agendamento online (opcional)
            channels: Lista de canais ['email', 'whatsapp', 'sms'] ou None para todos

        Returns:
            dict: Resultados por canal
        """
        if channels is None:
            channels = ['email', 'whatsapp']

        results = {}

        # Email
        if 'email' in channels and client.email:
            try:
                html_body = render_template_string(
                    NEW_CLIENT_EMAIL_TEMPLATE,
                    client_name=client.name,
                    business_name=business_name,
                    booking_url=booking_url,
                    year=datetime.now().year
                )
                text_body = create_new_client_message(client.name, business_name, booking_url)

                success, result = send_email(
                    subject=f"Bem-vindo(a) a {business_name}!",
                    recipient=client.email,
                    html_body=html_body,
                    text_body=text_body
                )
                results['email'] = NotificationResult(
                    success=success,
                    channel='email',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['email'] = NotificationResult(
                    success=False,
                    channel='email',
                    error=str(e)
                )

        # WhatsApp
        if 'whatsapp' in channels and client.phone and is_twilio_configured():
            try:
                message = create_new_client_message(client.name, business_name, booking_url)
                success, result = send_whatsapp(client.phone, message)
                results['whatsapp'] = NotificationResult(
                    success=success,
                    channel='whatsapp',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['whatsapp'] = NotificationResult(
                    success=False,
                    channel='whatsapp',
                    error=str(e)
                )

        # SMS
        if 'sms' in channels and client.phone and is_twilio_configured():
            try:
                message = create_new_client_message(client.name, business_name, booking_url)
                # SMS mais curto
                short_message = f"Bem-vindo(a) a {business_name}, {client.name}! Seu cadastro foi realizado com sucesso."
                success, result = send_sms(client.phone, short_message)
                results['sms'] = NotificationResult(
                    success=success,
                    channel='sms',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['sms'] = NotificationResult(
                    success=False,
                    channel='sms',
                    error=str(e)
                )

        return results

    @staticmethod
    def send_appointment_created_notification(appointment, client, professional, service,
                                              business_name, booking_code=None,
                                              confirmation_url=None, booking_url=None,
                                              channels=None):
        """
        Envia notificacao de agendamento criado.

        Args:
            appointment: Objeto Appointment
            client: Objeto Client
            professional: Objeto Professional
            service: Objeto Service
            business_name: Nome do estabelecimento
            booking_code: Codigo do agendamento
            confirmation_url: URL para confirmar agendamento
            booking_url: URL para novos agendamentos
            channels: Lista de canais ou None para todos

        Returns:
            dict: Resultados por canal
        """
        if channels is None:
            channels = ['email', 'whatsapp']

        results = {}

        # Formatar dados
        date_str = appointment.appointment_date.strftime('%d/%m/%Y')
        time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]
        price = float(appointment.price) if appointment.price else (float(service.price) if service and service.price else None)

        # Email
        if 'email' in channels and client.email:
            try:
                html_body = render_template_string(
                    APPOINTMENT_CREATED_EMAIL_TEMPLATE,
                    client_name=client.name,
                    business_name=business_name,
                    appointment_date=date_str,
                    appointment_time=time_str,
                    service_name=service.name if service else 'Servico',
                    professional_name=professional.name if professional else 'Profissional',
                    booking_code=booking_code,
                    price=f"{price:.2f}" if price else None,
                    confirmation_url=confirmation_url,
                    year=datetime.now().year
                )
                text_body = create_appointment_created_message(
                    client.name, date_str, time_str,
                    service.name if service else 'Servico',
                    professional.name if professional else 'Profissional',
                    business_name, booking_code, price
                )

                success, result = send_email(
                    subject=f"Agendamento Realizado - {business_name}",
                    recipient=client.email,
                    html_body=html_body,
                    text_body=text_body
                )
                results['email'] = NotificationResult(
                    success=success,
                    channel='email',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['email'] = NotificationResult(
                    success=False,
                    channel='email',
                    error=str(e)
                )

        # WhatsApp
        if 'whatsapp' in channels and client.phone and is_twilio_configured():
            try:
                message = create_appointment_created_message(
                    client.name, date_str, time_str,
                    service.name if service else 'Servico',
                    professional.name if professional else 'Profissional',
                    business_name, booking_code, price
                )
                success, result = send_whatsapp(client.phone, message)
                results['whatsapp'] = NotificationResult(
                    success=success,
                    channel='whatsapp',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['whatsapp'] = NotificationResult(
                    success=False,
                    channel='whatsapp',
                    error=str(e)
                )

        # SMS
        if 'sms' in channels and client.phone and is_twilio_configured():
            try:
                short_message = f"Agendamento confirmado na {business_name}: {date_str} as {time_str}. Servico: {service.name if service else 'Servico'}."
                if booking_code:
                    short_message += f" Codigo: {booking_code}"
                success, result = send_sms(client.phone, short_message)
                results['sms'] = NotificationResult(
                    success=success,
                    channel='sms',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['sms'] = NotificationResult(
                    success=False,
                    channel='sms',
                    error=str(e)
                )

        return results

    @staticmethod
    def send_appointment_confirmed_notification(appointment, client, professional, service,
                                                business_name, channels=None):
        """Envia notificacao de agendamento confirmado"""
        if channels is None:
            channels = ['email', 'whatsapp']

        results = {}

        date_str = appointment.appointment_date.strftime('%d/%m/%Y')
        time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]

        # Email
        if 'email' in channels and client.email:
            try:
                html_body = render_template_string(
                    APPOINTMENT_CONFIRMED_EMAIL_TEMPLATE,
                    client_name=client.name,
                    business_name=business_name,
                    appointment_date=date_str,
                    appointment_time=time_str,
                    service_name=service.name if service else 'Servico',
                    professional_name=professional.name if professional else 'Profissional',
                    year=datetime.now().year
                )
                text_body = create_appointment_confirmed_message(
                    client.name, date_str, time_str,
                    service.name if service else 'Servico',
                    business_name
                )

                success, result = send_email(
                    subject=f"Agendamento Confirmado - {business_name}",
                    recipient=client.email,
                    html_body=html_body,
                    text_body=text_body
                )
                results['email'] = NotificationResult(
                    success=success,
                    channel='email',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['email'] = NotificationResult(
                    success=False,
                    channel='email',
                    error=str(e)
                )

        # WhatsApp
        if 'whatsapp' in channels and client.phone and is_twilio_configured():
            try:
                message = create_appointment_confirmed_message(
                    client.name, date_str, time_str,
                    service.name if service else 'Servico',
                    business_name
                )
                success, result = send_whatsapp(client.phone, message)
                results['whatsapp'] = NotificationResult(
                    success=success,
                    channel='whatsapp',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['whatsapp'] = NotificationResult(
                    success=False,
                    channel='whatsapp',
                    error=str(e)
                )

        return results

    @staticmethod
    def send_appointment_cancelled_notification(appointment, client, service, business_name,
                                                reason=None, booking_url=None, channels=None):
        """Envia notificacao de agendamento cancelado"""
        if channels is None:
            channels = ['email', 'whatsapp']

        results = {}

        date_str = appointment.appointment_date.strftime('%d/%m/%Y')
        time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]

        # Email
        if 'email' in channels and client.email:
            try:
                html_body = render_template_string(
                    APPOINTMENT_CANCELLED_EMAIL_TEMPLATE,
                    client_name=client.name,
                    business_name=business_name,
                    appointment_date=date_str,
                    appointment_time=time_str,
                    service_name=service.name if service else 'Servico',
                    cancellation_reason=reason,
                    booking_url=booking_url,
                    year=datetime.now().year
                )
                text_body = create_appointment_cancelled_message(
                    client.name, date_str, time_str,
                    service.name if service else 'Servico',
                    business_name, reason
                )

                success, result = send_email(
                    subject=f"Agendamento Cancelado - {business_name}",
                    recipient=client.email,
                    html_body=html_body,
                    text_body=text_body
                )
                results['email'] = NotificationResult(
                    success=success,
                    channel='email',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['email'] = NotificationResult(
                    success=False,
                    channel='email',
                    error=str(e)
                )

        # WhatsApp
        if 'whatsapp' in channels and client.phone and is_twilio_configured():
            try:
                message = create_appointment_cancelled_message(
                    client.name, date_str, time_str,
                    service.name if service else 'Servico',
                    business_name, reason
                )
                success, result = send_whatsapp(client.phone, message)
                results['whatsapp'] = NotificationResult(
                    success=success,
                    channel='whatsapp',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['whatsapp'] = NotificationResult(
                    success=False,
                    channel='whatsapp',
                    error=str(e)
                )

        return results

    @staticmethod
    def send_appointment_rescheduled_notification(appointment, client, professional, service,
                                                  business_name, old_date, old_time,
                                                  channels=None):
        """Envia notificacao de agendamento reagendado"""
        if channels is None:
            channels = ['email', 'whatsapp']

        results = {}

        new_date_str = appointment.appointment_date.strftime('%d/%m/%Y')
        new_time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]
        old_date_str = old_date.strftime('%d/%m/%Y') if hasattr(old_date, 'strftime') else str(old_date)
        old_time_str = old_time.strftime('%H:%M') if hasattr(old_time, 'strftime') else str(old_time)[:5]

        # Email
        if 'email' in channels and client.email:
            try:
                html_body = render_template_string(
                    APPOINTMENT_RESCHEDULED_EMAIL_TEMPLATE,
                    client_name=client.name,
                    business_name=business_name,
                    old_date=old_date_str,
                    old_time=old_time_str,
                    appointment_date=new_date_str,
                    appointment_time=new_time_str,
                    service_name=service.name if service else 'Servico',
                    professional_name=professional.name if professional else 'Profissional',
                    year=datetime.now().year
                )
                text_body = create_appointment_rescheduled_message(
                    client.name, old_date_str, old_time_str, new_date_str, new_time_str,
                    service.name if service else 'Servico',
                    professional.name if professional else 'Profissional',
                    business_name
                )

                success, result = send_email(
                    subject=f"Agendamento Reagendado - {business_name}",
                    recipient=client.email,
                    html_body=html_body,
                    text_body=text_body
                )
                results['email'] = NotificationResult(
                    success=success,
                    channel='email',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['email'] = NotificationResult(
                    success=False,
                    channel='email',
                    error=str(e)
                )

        # WhatsApp
        if 'whatsapp' in channels and client.phone and is_twilio_configured():
            try:
                message = create_appointment_rescheduled_message(
                    client.name, old_date_str, old_time_str, new_date_str, new_time_str,
                    service.name if service else 'Servico',
                    professional.name if professional else 'Profissional',
                    business_name
                )
                success, result = send_whatsapp(client.phone, message)
                results['whatsapp'] = NotificationResult(
                    success=success,
                    channel='whatsapp',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['whatsapp'] = NotificationResult(
                    success=False,
                    channel='whatsapp',
                    error=str(e)
                )

        return results

    @staticmethod
    def send_appointment_completed_notification(appointment, client, professional, service,
                                                business_name, price=None, payment_method=None,
                                                booking_url=None, channels=None):
        """Envia notificacao de agendamento concluido"""
        if channels is None:
            channels = ['email', 'whatsapp']

        results = {}

        date_str = appointment.appointment_date.strftime('%d/%m/%Y')
        final_price = price or (float(appointment.price) if appointment.price else None)

        # Email
        if 'email' in channels and client.email:
            try:
                html_body = render_template_string(
                    APPOINTMENT_COMPLETED_EMAIL_TEMPLATE,
                    client_name=client.name,
                    business_name=business_name,
                    appointment_date=date_str,
                    service_name=service.name if service else 'Servico',
                    professional_name=professional.name if professional else 'Profissional',
                    price=f"{final_price:.2f}" if final_price else None,
                    payment_method=payment_method or appointment.payment_method,
                    booking_url=booking_url,
                    year=datetime.now().year
                )
                text_body = create_appointment_completed_message(
                    client.name,
                    service.name if service else 'Servico',
                    professional.name if professional else 'Profissional',
                    business_name, final_price
                )

                success, result = send_email(
                    subject=f"Obrigado pela visita! - {business_name}",
                    recipient=client.email,
                    html_body=html_body,
                    text_body=text_body
                )
                results['email'] = NotificationResult(
                    success=success,
                    channel='email',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['email'] = NotificationResult(
                    success=False,
                    channel='email',
                    error=str(e)
                )

        # WhatsApp
        if 'whatsapp' in channels and client.phone and is_twilio_configured():
            try:
                message = create_appointment_completed_message(
                    client.name,
                    service.name if service else 'Servico',
                    professional.name if professional else 'Profissional',
                    business_name, final_price
                )
                success, result = send_whatsapp(client.phone, message)
                results['whatsapp'] = NotificationResult(
                    success=success,
                    channel='whatsapp',
                    message_id=result if success else None,
                    error=result if not success else None
                )
            except Exception as e:
                results['whatsapp'] = NotificationResult(
                    success=False,
                    channel='whatsapp',
                    error=str(e)
                )

        return results


# Instancia global para uso facil
notification_service = NotificationService()
