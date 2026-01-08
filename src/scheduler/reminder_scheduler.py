"""
Scheduler para processamento de lembretes

Pode ser executado de várias formas:
1. Como script standalone: python -m src.scheduler.reminder_scheduler
2. Com APScheduler integrado ao Flask
3. Via cron job externo
4. Via Celery Beat (recomendado para produção)
"""

import os
import sys
from datetime import datetime, timedelta

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from src.config.database import db
from src.models.reminder import Reminder, ReminderLog
from src.models.appointment import Appointment
from src.models.user import User
from src.services.twilio_service import (
    send_whatsapp, send_sms, is_twilio_configured,
    create_appointment_reminder_message
)
from src.services.email_service import send_email


def send_single_reminder(reminder):
    """
    Envia um único lembrete

    Returns:
        tuple: (success, message_or_error)
    """
    try:
        appointment = reminder.appointment
        if not appointment:
            return False, 'Agendamento não encontrado'

        client = appointment.client
        if not client:
            return False, 'Cliente não encontrado'

        user = User.query.get(reminder.user_id)
        if not user:
            return False, 'Usuário não encontrado'

        business_name = user.business_name or user.name

        # Gerar mensagem
        message = create_appointment_reminder_message(
            appointment=appointment,
            client_name=client.name,
            business_name=business_name
        )

        reminder.message_content = message
        reminder.attempts += 1

        success = False
        result = None

        if reminder.type == 'whatsapp':
            if not client.phone:
                result = 'Cliente não tem telefone cadastrado'
            else:
                success, result = send_whatsapp(client.phone, message)

        elif reminder.type == 'sms':
            if not client.phone:
                result = 'Cliente não tem telefone cadastrado'
            else:
                success, result = send_sms(client.phone, message)

        elif reminder.type == 'email':
            if not client.email:
                result = 'Cliente não tem email cadastrado'
            else:
                html_body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #4F46E5;">Lembrete de Agendamento</h2>
                    <pre style="white-space: pre-wrap;">{message}</pre>
                </div>
                """
                success, result = send_email(
                    subject=f'Lembrete: Agendamento em {business_name}',
                    recipient=client.email,
                    html_body=html_body,
                    text_body=message
                )

        # Registrar log
        log = ReminderLog(
            reminder_id=reminder.id,
            success=success,
            error_message=result if not success else None,
            external_id=result if success else None
        )
        db.session.add(log)

        # Atualizar status
        if success:
            reminder.status = 'sent'
            reminder.sent_at = datetime.utcnow()
            reminder.external_id = result
        else:
            if reminder.attempts >= reminder.max_attempts:
                reminder.status = 'failed'
            reminder.error_message = result

        db.session.commit()
        return success, result

    except Exception as e:
        reminder.error_message = str(e)
        reminder.status = 'failed'
        db.session.commit()
        return False, str(e)


def process_pending_reminders():
    """
    Processa todos os lembretes pendentes que devem ser enviados

    Returns:
        dict: Estatísticas do processamento
    """
    now = datetime.utcnow()

    pending = Reminder.query.filter(
        Reminder.status.in_(['pending', 'scheduled']),
        Reminder.scheduled_at <= now
    ).all()

    results = {
        'processed': 0,
        'sent': 0,
        'failed': 0,
        'timestamp': now.isoformat()
    }

    for reminder in pending:
        results['processed'] += 1
        success, _ = send_single_reminder(reminder)
        if success:
            results['sent'] += 1
        else:
            results['failed'] += 1

    return results


def create_reminders_for_upcoming_appointments():
    """
    Cria lembretes automaticamente para agendamentos futuros
    que ainda não têm lembretes criados

    Returns:
        dict: Estatísticas de criação
    """
    from src.models.reminder_settings import ReminderSettings

    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)

    # Buscar agendamentos para as próximas 24h que não têm lembretes
    appointments = Appointment.query.filter(
        Appointment.status == 'scheduled',
        Appointment.appointment_date >= now.date(),
        Appointment.appointment_date <= tomorrow.date()
    ).all()

    results = {
        'appointments_checked': 0,
        'reminders_created': 0,
        'timestamp': now.isoformat()
    }

    for appointment in appointments:
        results['appointments_checked'] += 1

        # Verificar se já tem lembretes
        existing = Reminder.query.filter_by(appointment_id=appointment.id).first()
        if existing:
            continue

        # Buscar configurações do usuário
        settings = ReminderSettings.query.filter_by(user_id=appointment.user_id).first()
        if not settings:
            continue

        # Calcular datetime do agendamento
        appointment_datetime = datetime.combine(
            appointment.appointment_date,
            appointment.start_time
        )

        # Criar lembretes baseado nas configurações
        if settings.email_enabled:
            scheduled_at = appointment_datetime - timedelta(hours=settings.email_hours_before)
            if scheduled_at > now:
                reminder = Reminder(
                    user_id=appointment.user_id,
                    appointment_id=appointment.id,
                    type='email',
                    scheduled_at=scheduled_at,
                    status='scheduled'
                )
                db.session.add(reminder)
                results['reminders_created'] += 1

        if settings.sms_enabled:
            scheduled_at = appointment_datetime - timedelta(hours=settings.sms_hours_before)
            if scheduled_at > now:
                reminder = Reminder(
                    user_id=appointment.user_id,
                    appointment_id=appointment.id,
                    type='sms',
                    scheduled_at=scheduled_at,
                    status='scheduled'
                )
                db.session.add(reminder)
                results['reminders_created'] += 1

        if settings.whatsapp_enabled:
            scheduled_at = appointment_datetime - timedelta(hours=settings.whatsapp_hours_before)
            if scheduled_at > now:
                reminder = Reminder(
                    user_id=appointment.user_id,
                    appointment_id=appointment.id,
                    type='whatsapp',
                    scheduled_at=scheduled_at,
                    status='scheduled'
                )
                db.session.add(reminder)
                results['reminders_created'] += 1

    db.session.commit()
    return results


def run_scheduler():
    """
    Executa o scheduler uma vez (para uso com cron)
    """
    print(f"[{datetime.utcnow().isoformat()}] Iniciando processamento de lembretes...")

    # Verificar configuração Twilio
    if not is_twilio_configured():
        print("AVISO: Twilio não está configurado. SMS/WhatsApp não funcionarão.")

    # 1. Criar lembretes para agendamentos futuros
    creation_results = create_reminders_for_upcoming_appointments()
    print(f"  Agendamentos verificados: {creation_results['appointments_checked']}")
    print(f"  Lembretes criados: {creation_results['reminders_created']}")

    # 2. Processar lembretes pendentes
    send_results = process_pending_reminders()
    print(f"  Lembretes processados: {send_results['processed']}")
    print(f"  Enviados com sucesso: {send_results['sent']}")
    print(f"  Falhas: {send_results['failed']}")

    print(f"[{datetime.utcnow().isoformat()}] Processamento concluído.\n")

    return {
        'creation': creation_results,
        'sending': send_results
    }


def start_background_scheduler(app, interval_minutes=5):
    """
    Inicia scheduler em background usando APScheduler

    Args:
        app: Instância do Flask app
        interval_minutes: Intervalo entre execuções
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = BackgroundScheduler()

        def job():
            with app.app_context():
                run_scheduler()

        scheduler.add_job(
            func=job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id='reminder_scheduler',
            name='Processar lembretes pendentes',
            replace_existing=True
        )

        scheduler.start()
        print(f"Scheduler de lembretes iniciado (intervalo: {interval_minutes} min)")

        return scheduler

    except ImportError:
        print("APScheduler não instalado. Use: pip install apscheduler")
        return None


if __name__ == '__main__':
    # Executar como script standalone
    from app import create_app

    app = create_app()

    with app.app_context():
        run_scheduler()
