import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv

load_dotenv()

# Configurar Twilio
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM', '+14155238886')
TWILIO_SMS_FROM = os.getenv('TWILIO_SMS_FROM')

# Cliente Twilio (lazy initialization)
_twilio_client = None


def get_twilio_client():
    """Retorna cliente Twilio (singleton)"""
    global _twilio_client
    if _twilio_client is None and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client


def is_twilio_configured():
    """Verifica se Twilio está configurado"""
    return bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)


def format_phone_number(phone):
    """Formata número de telefone para formato internacional"""
    if not phone:
        return None

    # Remove caracteres não numéricos
    digits = ''.join(filter(str.isdigit, phone))

    # Se já começa com +, retorna como está
    if phone.startswith('+'):
        return phone

    # Se é brasileiro (11 dígitos), adiciona +55
    if len(digits) == 11:
        return f'+55{digits}'

    # Se tem 10 dígitos, pode ser sem DDD (adiciona 11 = SP como default)
    if len(digits) == 10:
        return f'+55{digits}'

    # Se já tem código do país (13 dígitos para Brasil)
    if len(digits) == 13 and digits.startswith('55'):
        return f'+{digits}'

    # Retorna com + se parece válido
    if len(digits) >= 10:
        return f'+{digits}'

    return None


def send_whatsapp(to_phone, message, media_url=None):
    """
    Envia mensagem WhatsApp via Twilio

    Args:
        to_phone: Número de telefone do destinatário
        message: Texto da mensagem
        media_url: URL opcional de mídia (imagem, documento)

    Returns:
        tuple: (success, message_sid or error)
    """
    if not is_twilio_configured():
        return False, 'Twilio não configurado'

    client = get_twilio_client()
    if not client:
        return False, 'Cliente Twilio não disponível'

    formatted_phone = format_phone_number(to_phone)
    if not formatted_phone:
        return False, f'Número de telefone inválido: {to_phone}'

    try:
        kwargs = {
            'from_': f'whatsapp:{TWILIO_WHATSAPP_FROM}',
            'to': f'whatsapp:{formatted_phone}',
            'body': message
        }

        if media_url:
            kwargs['media_url'] = [media_url]

        msg = client.messages.create(**kwargs)

        return True, msg.sid

    except TwilioRestException as e:
        error_msg = f'Erro Twilio: {e.code} - {e.msg}'
        print(error_msg)
        return False, error_msg

    except Exception as e:
        error_msg = f'Erro ao enviar WhatsApp: {str(e)}'
        print(error_msg)
        return False, error_msg


def send_sms(to_phone, message):
    """
    Envia SMS via Twilio

    Args:
        to_phone: Número de telefone do destinatário
        message: Texto da mensagem (máximo 160 caracteres recomendado)

    Returns:
        tuple: (success, message_sid or error)
    """
    if not is_twilio_configured():
        return False, 'Twilio não configurado'

    if not TWILIO_SMS_FROM:
        return False, 'Número SMS não configurado (TWILIO_SMS_FROM)'

    client = get_twilio_client()
    if not client:
        return False, 'Cliente Twilio não disponível'

    formatted_phone = format_phone_number(to_phone)
    if not formatted_phone:
        return False, f'Número de telefone inválido: {to_phone}'

    try:
        msg = client.messages.create(
            from_=TWILIO_SMS_FROM,
            to=formatted_phone,
            body=message[:1600]  # Twilio aceita até 1600 caracteres
        )

        return True, msg.sid

    except TwilioRestException as e:
        error_msg = f'Erro Twilio: {e.code} - {e.msg}'
        print(error_msg)
        return False, error_msg

    except Exception as e:
        error_msg = f'Erro ao enviar SMS: {str(e)}'
        print(error_msg)
        return False, error_msg


def get_message_status(message_sid):
    """
    Verifica status de uma mensagem enviada

    Returns:
        dict: Status da mensagem ou None se erro
    """
    if not is_twilio_configured():
        return None

    client = get_twilio_client()
    if not client:
        return None

    try:
        message = client.messages(message_sid).fetch()
        return {
            'sid': message.sid,
            'status': message.status,  # queued, sending, sent, delivered, failed, undelivered
            'error_code': message.error_code,
            'error_message': message.error_message,
            'date_sent': message.date_sent.isoformat() if message.date_sent else None
        }
    except Exception as e:
        print(f'Erro ao verificar status: {str(e)}')
        return None


def create_appointment_reminder_message(appointment, client_name, business_name, include_confirmation_link=False, confirmation_url=None):
    """
    Cria mensagem de lembrete de agendamento

    Args:
        appointment: Objeto Appointment
        client_name: Nome do cliente
        business_name: Nome da empresa
        include_confirmation_link: Se deve incluir link de confirmação
        confirmation_url: URL para confirmação

    Returns:
        str: Mensagem formatada
    """
    from datetime import datetime

    # Formatar data
    date_str = appointment.appointment_date.strftime('%d/%m/%Y')
    time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]

    # Buscar nome do serviço
    service_name = appointment.service.name if appointment.service else 'Serviço'

    # Buscar nome do profissional
    professional_name = appointment.professional.name if appointment.professional else 'Profissional'

    message = f"""Olá {client_name}! 👋

Lembrete do seu agendamento na {business_name}:

📅 Data: {date_str}
⏰ Horário: {time_str}
💇 Serviço: {service_name}
👤 Profissional: {professional_name}

"""

    if include_confirmation_link and confirmation_url:
        message += f"""Para confirmar sua presença, acesse:
{confirmation_url}

"""

    message += f"""Em caso de imprevistos, entre em contato para remarcar.

Aguardamos você! ✨
{business_name}"""

    return message


def create_confirmation_message(appointment, client_name, business_name):
    """
    Cria mensagem de confirmação de agendamento
    """
    date_str = appointment.appointment_date.strftime('%d/%m/%Y')
    time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]
    service_name = appointment.service.name if appointment.service else 'Serviço'

    return f"""✅ Agendamento Confirmado!

Olá {client_name},

Seu agendamento foi confirmado com sucesso:

📅 {date_str} às {time_str}
💇 {service_name}

Obrigado pela confirmação!
{business_name}"""


def create_cancellation_message(appointment, client_name, business_name, reason=None):
    """
    Cria mensagem de cancelamento de agendamento
    """
    date_str = appointment.appointment_date.strftime('%d/%m/%Y')
    time_str = appointment.start_time.strftime('%H:%M') if hasattr(appointment.start_time, 'strftime') else str(appointment.start_time)[:5]

    message = f"""❌ Agendamento Cancelado

Olá {client_name},

Seu agendamento para {date_str} às {time_str} foi cancelado.
"""

    if reason:
        message += f"\nMotivo: {reason}\n"

    message += f"""
Para reagendar, acesse nosso sistema ou entre em contato.

{business_name}"""

    return message
