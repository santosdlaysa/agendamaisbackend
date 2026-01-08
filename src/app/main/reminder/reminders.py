from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from datetime import datetime, timedelta
from src.config.database import db
from src.models.reminder import Reminder, ReminderLog
from src.models.reminder_settings import ReminderSettings
from src.models.appointment import Appointment
from src.models.user import User
from src.services.twilio_service import (
    send_whatsapp, send_sms, is_twilio_configured,
    create_appointment_reminder_message
)
from src.services.email_service import send_email

reminders_bp = Blueprint('reminders', __name__)


def get_current_user_id():
    """Obtém o ID do usuário logado"""
    return int(get_jwt_identity())


# ============================================
# CONFIGURAÇÕES DE LEMBRETES
# ============================================

@reminders_bp.route('/settings', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Obter configurações de lembretes',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Configurações atuais'}
    }
})
def get_settings():
    """Obter configurações de lembretes do usuário"""
    try:
        user_id = get_current_user_id()

        settings = ReminderSettings.query.filter_by(user_id=user_id).first()

        if not settings:
            # Criar configurações padrão
            settings = ReminderSettings(user_id=user_id)
            db.session.add(settings)
            db.session.commit()

        return jsonify({
            'settings': settings.to_dict(),
            'twilio_configured': is_twilio_configured()
        }), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter configurações: {str(e)}'), 500


@reminders_bp.route('/settings', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Atualizar configurações de lembretes',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'email_enabled': {'type': 'boolean'},
                    'email_hours_before': {'type': 'integer'},
                    'sms_enabled': {'type': 'boolean'},
                    'sms_hours_before': {'type': 'integer'},
                    'whatsapp_enabled': {'type': 'boolean'},
                    'whatsapp_hours_before': {'type': 'integer'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Configurações atualizadas'}
    }
})
def update_settings():
    """Atualizar configurações de lembretes"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        settings = ReminderSettings.query.filter_by(user_id=user_id).first()

        if not settings:
            settings = ReminderSettings(user_id=user_id)
            db.session.add(settings)

        # Atualizar campos
        if 'email_enabled' in data:
            settings.email_enabled = data['email_enabled']
        if 'email_hours_before' in data:
            settings.email_hours_before = max(1, min(72, int(data['email_hours_before'])))
        if 'sms_enabled' in data:
            settings.sms_enabled = data['sms_enabled']
        if 'sms_hours_before' in data:
            settings.sms_hours_before = max(1, min(72, int(data['sms_hours_before'])))
        if 'whatsapp_enabled' in data:
            settings.whatsapp_enabled = data['whatsapp_enabled']
        if 'whatsapp_hours_before' in data:
            settings.whatsapp_hours_before = max(1, min(72, int(data['whatsapp_hours_before'])))

        db.session.commit()

        return jsonify({
            'message': 'Configurações atualizadas com sucesso',
            'settings': settings.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar configurações: {str(e)}'), 500


# ============================================
# LISTAGEM E ESTATÍSTICAS
# ============================================

@reminders_bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Listar lembretes',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'status', 'in': 'query', 'type': 'string', 'description': 'Filtrar por status'},
        {'name': 'type', 'in': 'query', 'type': 'string', 'description': 'Filtrar por tipo'},
        {'name': 'date_from', 'in': 'query', 'type': 'string', 'description': 'Data inicial (YYYY-MM-DD)'},
        {'name': 'date_to', 'in': 'query', 'type': 'string', 'description': 'Data final (YYYY-MM-DD)'},
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 20}
    ],
    'responses': {
        200: {'description': 'Lista de lembretes'}
    }
})
def list_reminders():
    """Listar lembretes do usuário"""
    try:
        user_id = get_current_user_id()

        # Parâmetros
        status = request.args.get('status')
        reminder_type = request.args.get('type')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # Query base
        query = Reminder.query.filter_by(user_id=user_id)

        # Filtros
        if status:
            query = query.filter(Reminder.status == status)
        if reminder_type:
            query = query.filter(Reminder.type == reminder_type)
        if date_from:
            try:
                df = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Reminder.scheduled_at >= df)
            except ValueError:
                pass
        if date_to:
            try:
                dt = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Reminder.scheduled_at < dt)
            except ValueError:
                pass

        # Ordenar por data agendada (mais recentes primeiro)
        query = query.order_by(Reminder.scheduled_at.desc())

        # Paginação
        reminders = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify(
            reminders=[r.to_dict_with_appointment() for r in reminders.items],
            pagination={
                'page': reminders.page,
                'pages': reminders.pages,
                'per_page': reminders.per_page,
                'total': reminders.total
            }
        ), 200

    except Exception as e:
        return jsonify(message=f'Erro ao listar lembretes: {str(e)}'), 500


@reminders_bp.route('/stats', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Estatísticas de lembretes',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Estatísticas'}
    }
})
def get_stats():
    """Retorna estatísticas dos lembretes"""
    try:
        user_id = get_current_user_id()

        # Contadores por status
        total = Reminder.query.filter_by(user_id=user_id).count()
        pending = Reminder.query.filter_by(user_id=user_id, status='pending').count()
        scheduled = Reminder.query.filter_by(user_id=user_id, status='scheduled').count()
        sent = Reminder.query.filter_by(user_id=user_id, status='sent').count()
        failed = Reminder.query.filter_by(user_id=user_id, status='failed').count()

        # Contadores por tipo (últimos 30 dias)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent = Reminder.query.filter(
            Reminder.user_id == user_id,
            Reminder.created_at >= thirty_days_ago
        )

        by_type = {
            'email': recent.filter(Reminder.type == 'email').count(),
            'sms': recent.filter(Reminder.type == 'sms').count(),
            'whatsapp': recent.filter(Reminder.type == 'whatsapp').count()
        }

        # Próximos lembretes (pendentes)
        next_reminders = Reminder.query.filter(
            Reminder.user_id == user_id,
            Reminder.status.in_(['pending', 'scheduled']),
            Reminder.scheduled_at >= datetime.utcnow()
        ).order_by(Reminder.scheduled_at).limit(5).all()

        return jsonify({
            'total': total,
            'pending': pending,
            'scheduled': scheduled,
            'sent': sent,
            'failed': failed,
            'by_type': by_type,
            'next_reminders': [r.to_dict_with_appointment() for r in next_reminders],
            'twilio_configured': is_twilio_configured()
        }), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter estatísticas: {str(e)}'), 500


# ============================================
# OPERAÇÕES EM LEMBRETES
# ============================================

@reminders_bp.route('/<int:reminder_id>', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Obter lembrete específico',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'reminder_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Dados do lembrete'},
        404: {'description': 'Lembrete não encontrado'}
    }
})
def get_reminder(reminder_id):
    """Obter lembrete específico"""
    try:
        user_id = get_current_user_id()

        reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()

        if not reminder:
            return jsonify(message='Lembrete não encontrado'), 404

        data = reminder.to_dict_with_appointment()
        data['logs'] = [log.to_dict() for log in reminder.logs]

        return jsonify(reminder=data), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter lembrete: {str(e)}'), 500


@reminders_bp.route('/<int:reminder_id>/cancel', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Cancelar lembrete',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'reminder_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Lembrete cancelado'},
        400: {'description': 'Lembrete já foi enviado'},
        404: {'description': 'Lembrete não encontrado'}
    }
})
def cancel_reminder(reminder_id):
    """Cancelar lembrete pendente"""
    try:
        user_id = get_current_user_id()

        reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()

        if not reminder:
            return jsonify(message='Lembrete não encontrado'), 404

        if reminder.status == 'sent':
            return jsonify(message='Lembrete já foi enviado'), 400

        reminder.status = 'cancelled'
        db.session.commit()

        return jsonify(
            message='Lembrete cancelado',
            reminder=reminder.to_dict()
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao cancelar lembrete: {str(e)}'), 500


@reminders_bp.route('/<int:reminder_id>/retry', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Reenviar lembrete',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'reminder_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Lembrete reenviado'},
        400: {'description': 'Erro ao reenviar'},
        404: {'description': 'Lembrete não encontrado'}
    }
})
def retry_reminder(reminder_id):
    """Reenviar lembrete que falhou"""
    try:
        user_id = get_current_user_id()

        reminder = Reminder.query.filter_by(id=reminder_id, user_id=user_id).first()

        if not reminder:
            return jsonify(message='Lembrete não encontrado'), 404

        if reminder.status == 'sent':
            return jsonify(message='Lembrete já foi enviado com sucesso'), 400

        # Tentar enviar novamente
        success, result = send_reminder(reminder)

        if success:
            return jsonify(
                message='Lembrete enviado com sucesso',
                reminder=reminder.to_dict()
            ), 200
        else:
            return jsonify(
                message=f'Falha ao enviar: {result}',
                reminder=reminder.to_dict()
            ), 400

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao reenviar lembrete: {str(e)}'), 500


# ============================================
# CRIAR LEMBRETES PARA AGENDAMENTO
# ============================================

@reminders_bp.route('/create-for-appointment', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Criar lembretes para agendamento',
    'description': 'Cria lembretes baseado nas configurações do usuário',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['appointment_id'],
                'properties': {
                    'appointment_id': {'type': 'integer'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Lembretes criados'},
        400: {'description': 'Dados inválidos'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def create_for_appointment():
    """Criar lembretes para um agendamento"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        appointment_id = data.get('appointment_id')
        if not appointment_id:
            return jsonify(message='appointment_id é obrigatório'), 400

        # Buscar agendamento
        appointment = Appointment.query.filter_by(
            id=appointment_id,
            user_id=user_id
        ).first()

        if not appointment:
            return jsonify(message='Agendamento não encontrado'), 404

        # Buscar configurações
        settings = ReminderSettings.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = ReminderSettings(user_id=user_id)
            db.session.add(settings)

        # Calcular datetime do agendamento
        appointment_datetime = datetime.combine(
            appointment.appointment_date,
            appointment.start_time
        )

        created_reminders = []

        # Criar lembretes baseado nas configurações
        if settings.email_enabled:
            scheduled_at = appointment_datetime - timedelta(hours=settings.email_hours_before)
            if scheduled_at > datetime.utcnow():
                reminder = Reminder(
                    user_id=user_id,
                    appointment_id=appointment_id,
                    type='email',
                    scheduled_at=scheduled_at,
                    status='scheduled'
                )
                db.session.add(reminder)
                created_reminders.append(reminder)

        if settings.sms_enabled:
            scheduled_at = appointment_datetime - timedelta(hours=settings.sms_hours_before)
            if scheduled_at > datetime.utcnow():
                reminder = Reminder(
                    user_id=user_id,
                    appointment_id=appointment_id,
                    type='sms',
                    scheduled_at=scheduled_at,
                    status='scheduled'
                )
                db.session.add(reminder)
                created_reminders.append(reminder)

        if settings.whatsapp_enabled:
            scheduled_at = appointment_datetime - timedelta(hours=settings.whatsapp_hours_before)
            if scheduled_at > datetime.utcnow():
                reminder = Reminder(
                    user_id=user_id,
                    appointment_id=appointment_id,
                    type='whatsapp',
                    scheduled_at=scheduled_at,
                    status='scheduled'
                )
                db.session.add(reminder)
                created_reminders.append(reminder)

        db.session.commit()

        return jsonify(
            message=f'{len(created_reminders)} lembretes criados',
            reminders=[r.to_dict() for r in created_reminders]
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao criar lembretes: {str(e)}'), 500


# ============================================
# ENVIO MANUAL
# ============================================

@reminders_bp.route('/send-now', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Enviar lembrete agora',
    'description': 'Envia um lembrete imediatamente (para teste ou envio manual)',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['appointment_id', 'type'],
                'properties': {
                    'appointment_id': {'type': 'integer'},
                    'type': {'type': 'string', 'enum': ['email', 'sms', 'whatsapp']}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Lembrete enviado'},
        400: {'description': 'Erro ao enviar'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def send_now():
    """Enviar lembrete imediatamente"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        appointment_id = data.get('appointment_id')
        reminder_type = data.get('type')

        if not appointment_id or not reminder_type:
            return jsonify(message='appointment_id e type são obrigatórios'), 400

        if reminder_type not in ['email', 'sms', 'whatsapp']:
            return jsonify(message='type deve ser email, sms ou whatsapp'), 400

        # Buscar agendamento
        appointment = Appointment.query.filter_by(
            id=appointment_id,
            user_id=user_id
        ).first()

        if not appointment:
            return jsonify(message='Agendamento não encontrado'), 404

        # Criar lembrete
        reminder = Reminder(
            user_id=user_id,
            appointment_id=appointment_id,
            type=reminder_type,
            scheduled_at=datetime.utcnow(),
            status='pending'
        )
        db.session.add(reminder)
        db.session.flush()

        # Enviar
        success, result = send_reminder(reminder)

        db.session.commit()

        if success:
            return jsonify(
                message='Lembrete enviado com sucesso',
                reminder=reminder.to_dict()
            ), 200
        else:
            return jsonify(
                message=f'Falha ao enviar: {result}',
                reminder=reminder.to_dict()
            ), 400

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao enviar lembrete: {str(e)}'), 500


# ============================================
# SCHEDULER STATUS
# ============================================

@reminders_bp.route('/scheduler/status', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Lembretes'],
    'summary': 'Status do agendador de lembretes',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Status do agendador'}
    }
})
def scheduler_status():
    """Status do agendador de lembretes"""
    try:
        user_id = get_current_user_id()

        # Contar lembretes pendentes para hoje
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        pending_today = Reminder.query.filter(
            Reminder.user_id == user_id,
            Reminder.status.in_(['pending', 'scheduled']),
            Reminder.scheduled_at >= today_start,
            Reminder.scheduled_at < today_end
        ).count()

        # Próximo lembrete
        next_reminder = Reminder.query.filter(
            Reminder.user_id == user_id,
            Reminder.status.in_(['pending', 'scheduled']),
            Reminder.scheduled_at >= datetime.utcnow()
        ).order_by(Reminder.scheduled_at).first()

        return jsonify({
            'running': True,
            'pending_today': pending_today,
            'next_run': next_reminder.scheduled_at.isoformat() if next_reminder else None,
            'twilio_configured': is_twilio_configured(),
            'message': 'Sistema de lembretes ativo'
        }), 200

    except Exception as e:
        return jsonify(message=f'Erro ao verificar status: {str(e)}'), 500


# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def send_reminder(reminder):
    """
    Envia um lembrete via o canal apropriado

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
                # Criar HTML simples para email
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

    Esta função deve ser chamada periodicamente (cron/scheduler)
    """
    now = datetime.utcnow()

    pending = Reminder.query.filter(
        Reminder.status.in_(['pending', 'scheduled']),
        Reminder.scheduled_at <= now
    ).all()

    results = {
        'processed': 0,
        'sent': 0,
        'failed': 0
    }

    for reminder in pending:
        results['processed'] += 1
        success, _ = send_reminder(reminder)
        if success:
            results['sent'] += 1
        else:
            results['failed'] += 1

    return results
