from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from src.models.user import db, User
from src.models.appointment import Appointment
from src.models.client import Client
from src.models.professional import Professional
from src.models.service import Service
from src.models.notification import Notification
from datetime import datetime, date, time, timedelta
from src.services.notification_service import NotificationService
# Import reminder scheduler conditionally
try:
    from src.services.reminder_scheduler import reminder_scheduler
    REMINDER_SCHEDULER_AVAILABLE = True
except ImportError:
    reminder_scheduler = None
    REMINDER_SCHEDULER_AVAILABLE = False


def get_business_info(user_id):
    """Obtem informacoes da empresa para notificacoes"""
    user = User.query.get(user_id)
    if not user:
        return 'Agenda+', None
    business_name = user.business_name or user.name
    booking_url = None
    if user.slug and user.online_booking_enabled:
        frontend_url = 'https://agendamais.site'
        booking_url = f"{frontend_url}/agendar/{user.slug}"
    return business_name, booking_url

appointments_bp = Blueprint('appointments', __name__)


def get_current_user_id():
    """Obtém o ID do usuário logado"""
    return int(get_jwt_identity())


@appointments_bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Listar agendamentos',
    'description': 'Retorna uma lista paginada de agendamentos com filtros',
    'parameters': [
        {'name': 'start_date', 'in': 'query', 'type': 'string', 'format': 'date', 'description': 'Data inicial (YYYY-MM-DD)'},
        {'name': 'end_date', 'in': 'query', 'type': 'string', 'format': 'date', 'description': 'Data final (YYYY-MM-DD)'},
        {'name': 'professional_id', 'in': 'query', 'type': 'integer'},
        {'name': 'client_id', 'in': 'query', 'type': 'integer'},
        {'name': 'service_id', 'in': 'query', 'type': 'integer'},
        {'name': 'status', 'in': 'query', 'type': 'string', 'enum': ['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']},
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 50}
    ],
    'responses': {
        200: {
            'description': 'Lista de agendamentos',
            'schema': {
                'type': 'object',
                'properties': {
                    'appointments': {'type': 'array', 'items': {'$ref': '#/definitions/Appointment'}},
                    'pagination': {'$ref': '#/definitions/Pagination'}
                }
            }
        }
    }
})
def get_appointments():
    """Listar agendamentos com filtros"""
    try:
        user_id = get_current_user_id()

        # Parâmetros de filtro
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        professional_id = request.args.get('professional_id')
        client_id = request.args.get('client_id')
        service_id = request.args.get('service_id')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        # Query base - FILTRAR POR EMPRESA
        query = Appointment.query.filter_by(user_id=user_id)
        
        # Aplicar filtros
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Appointment.appointment_date >= start_date_obj)
            except ValueError:
                return jsonify(message='Formato de data inválido. Use YYYY-MM-DD'), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Appointment.appointment_date <= end_date_obj)
            except ValueError:
                return jsonify(message='Formato de data inválido. Use YYYY-MM-DD'), 400
        
        if professional_id:
            query = query.filter(Appointment.professional_id == int(professional_id))

        if client_id:
            query = query.filter(Appointment.client_id == int(client_id))

        if service_id:
            query = query.filter(Appointment.service_id == int(service_id))
        
        if status:
            query = query.filter(Appointment.status == status)
        
        # Ordenar por data e hora
        query = query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc())
        
        # Paginação
        appointments = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Serializar dados com informações detalhadas
        appointments_data = [appointment.to_dict_detailed() for appointment in appointments.items]
        
        return jsonify(
            appointments=appointments_data,
            pagination={
                'page': appointments.page,
                'pages': appointments.pages,
                'per_page': appointments.per_page,
                'total': appointments.total
            }
        ), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao listar agendamentos: {str(e)}'), 500

@appointments_bp.route('/<int:appointment_id>', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Obter agendamento específico',
    'parameters': [
        {'name': 'appointment_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Dados do agendamento'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def get_appointment(appointment_id):
    """Obter agendamento específico"""
    try:
        user_id = get_current_user_id()
        appointment = Appointment.query.filter_by(id=appointment_id, user_id=user_id).first()

        if not appointment:
            return jsonify(message='Agendamento não encontrado'), 404

        return jsonify(appointment=appointment.to_dict_detailed()), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter agendamento: {str(e)}'), 500

@appointments_bp.route('', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Criar novo agendamento',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['client_id', 'professional_id', 'service_id', 'appointment_date', 'start_time'],
                'properties': {
                    'client_id': {'type': 'integer', 'example': 1},
                    'professional_id': {'type': 'integer', 'example': 1},
                    'service_id': {'type': 'integer', 'example': 1},
                    'appointment_date': {'type': 'string', 'format': 'date', 'example': '2024-01-15'},
                    'start_time': {'type': 'string', 'example': '09:00'},
                    'status': {'type': 'string', 'enum': ['scheduled', 'confirmed'], 'default': 'scheduled'},
                    'notes': {'type': 'string'},
                    'price': {'type': 'number'},
                    'payment_method': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Agendamento criado com sucesso'},
        400: {'description': 'Dados inválidos ou conflito de horário'},
        404: {'description': 'Cliente, profissional ou serviço não encontrado'}
    }
})
def create_appointment():
    """Criar novo agendamento"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Validar dados obrigatórios
        required_fields = ['client_id', 'professional_id', 'service_id', 'appointment_date', 'start_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify(message=f'{field} é obrigatório'), 400

        # Validar e converter data
        try:
            appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify(message='Formato de data inválido. Use YYYY-MM-DD'), 400

        # Validar e converter horário
        try:
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            return jsonify(message='Formato de horário inválido. Use HH:MM'), 400

        # Verificar se entidades existem E PERTENCEM AO USUÁRIO
        client = Client.query.filter_by(id=data['client_id'], user_id=user_id).first()
        if not client:
            return jsonify(message='Cliente não encontrado'), 404

        professional = Professional.query.filter_by(id=data['professional_id'], user_id=user_id).first()
        if not professional or not professional.active:
            return jsonify(message='Profissional não encontrado ou inativo'), 404

        service = Service.query.filter_by(id=data['service_id'], user_id=user_id).first()
        if not service or not service.active:
            return jsonify(message='Serviço não encontrado ou inativo'), 404
        
        # Verificar se profissional realiza o serviço
        if service not in professional.services:
            return jsonify(message='Profissional não realiza este serviço'), 400
        
        # Calcular horário de fim
        start_datetime = datetime.combine(appointment_date, start_time)
        end_datetime = start_datetime + timedelta(minutes=service.duration)
        end_time = end_datetime.time()
        
        # Verificar conflitos de horário
        if Appointment.check_conflict(professional.id, appointment_date, start_time, end_time):
            return jsonify(message='Conflito de horário detectado. Profissional já possui agendamento neste horário'), 400
        
        # Criar agendamento
        appointment = Appointment(
            user_id=user_id,
            client_id=client.id,
            professional_id=professional.id,
            service_id=service.id,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            status=data.get('status', 'scheduled'),
            notes=data.get('notes'),
            price=data.get('price', service.price),
            payment_method=data.get('payment_method')
        )
        
        db.session.add(appointment)

        # Criar notificacao in-app para o dashboard
        try:
            Notification.notify_new_appointment(
                user_id=user_id,
                appointment=appointment,
                client=client,
                service=service,
                professional=professional
            )
        except Exception as e:
            print(f"Erro ao criar notificacao in-app: {str(e)}")

        db.session.commit()

        response_data = {
            'message': 'Agendamento criado com sucesso',
            'appointment': appointment.to_dict_detailed()
        }

        # Criar lembretes automáticos para o agendamento se disponível
        if REMINDER_SCHEDULER_AVAILABLE and reminder_scheduler:
            try:
                reminder_result = reminder_scheduler.create_reminders_for_appointment(appointment.id)

                # Incluir informações dos lembretes criados
                if reminder_result['success']:
                    response_data['reminders_created'] = reminder_result['reminders_created']
                    response_data['total_reminders'] = reminder_result['total_reminders']
                else:
                    response_data['reminder_warning'] = f"Agendamento criado, mas houve problema ao criar lembretes: {reminder_result['error']}"
            except Exception as e:
                response_data['reminder_warning'] = f"Agendamento criado, mas lembretes não puderam ser criados: {str(e)}"

        # Enviar notificacao de agendamento criado
        send_notification = data.get('send_notification', True)
        if send_notification and (client.email or client.phone):
            try:
                business_name, booking_url = get_business_info(user_id)
                channels = data.get('notification_channels', ['email', 'whatsapp'])

                notification_results = NotificationService.send_appointment_created_notification(
                    appointment=appointment,
                    client=client,
                    professional=professional,
                    service=service,
                    business_name=business_name,
                    booking_code=appointment.booking_code,
                    booking_url=booking_url,
                    channels=channels
                )
                response_data['notifications'] = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in notification_results.items()}
            except Exception as e:
                response_data['notification_warning'] = f"Agendamento criado, mas notificacao falhou: {str(e)}"

        return jsonify(**response_data), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao criar agendamento: {str(e)}'), 500

@appointments_bp.route('/<int:appointment_id>', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Atualizar agendamento (reagendar)',
    'parameters': [
        {'name': 'appointment_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['client_id', 'professional_id', 'service_id', 'appointment_date', 'start_time'],
                'properties': {
                    'client_id': {'type': 'integer'},
                    'professional_id': {'type': 'integer'},
                    'service_id': {'type': 'integer'},
                    'appointment_date': {'type': 'string', 'format': 'date'},
                    'start_time': {'type': 'string'},
                    'status': {'type': 'string'},
                    'notes': {'type': 'string'},
                    'price': {'type': 'number'},
                    'payment_method': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Agendamento atualizado com sucesso'},
        400: {'description': 'Conflito de horário ou dados inválidos'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def update_appointment(appointment_id):
    """Atualizar agendamento (reagendar)"""
    try:
        user_id = get_current_user_id()
        appointment = Appointment.query.filter_by(id=appointment_id, user_id=user_id).first()

        if not appointment:
            return jsonify(message='Agendamento não encontrado'), 404

        data = request.get_json()

        # Validar dados obrigatórios
        required_fields = ['client_id', 'professional_id', 'service_id', 'appointment_date', 'start_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify(message=f'{field} é obrigatório'), 400

        # Validar e converter data
        try:
            appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify(message='Formato de data inválido. Use YYYY-MM-DD'), 400

        # Validar e converter horário
        try:
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            return jsonify(message='Formato de horário inválido. Use HH:MM'), 400

        # Verificar se entidades existem E PERTENCEM AO USUÁRIO
        client = Client.query.filter_by(id=data['client_id'], user_id=user_id).first()
        if not client:
            return jsonify(message='Cliente não encontrado'), 404

        professional = Professional.query.filter_by(id=data['professional_id'], user_id=user_id).first()
        if not professional or not professional.active:
            return jsonify(message='Profissional não encontrado ou inativo'), 404

        service = Service.query.filter_by(id=data['service_id'], user_id=user_id).first()
        if not service or not service.active:
            return jsonify(message='Serviço não encontrado ou inativo'), 404
        
        # Verificar se profissional realiza o serviço
        if service not in professional.services:
            return jsonify(message='Profissional não realiza este serviço'), 400
        
        # Calcular horário de fim
        start_datetime = datetime.combine(appointment_date, start_time)
        end_datetime = start_datetime + timedelta(minutes=service.duration)
        end_time = end_datetime.time()
        
        # Verificar conflitos de horário (excluindo o agendamento atual)
        if Appointment.check_conflict(professional.id, appointment_date, start_time, end_time, appointment.id):
            return jsonify(message='Conflito de horário detectado. Profissional já possui agendamento neste horário'), 400

        # Guardar dados antigos para notificacao de reagendamento
        old_date = appointment.appointment_date
        old_time = appointment.start_time
        date_changed = old_date != appointment_date or old_time != start_time

        # Atualizar agendamento
        appointment.client_id = client.id
        appointment.professional_id = professional.id
        appointment.service_id = service.id
        appointment.appointment_date = appointment_date
        appointment.start_time = start_time
        appointment.end_time = end_time
        appointment.status = data.get('status', appointment.status)
        appointment.notes = data.get('notes', appointment.notes)
        appointment.price = data.get('price', service.price)
        appointment.payment_method = data.get('payment_method', appointment.payment_method)

        db.session.commit()

        response_data = {
            'message': 'Agendamento atualizado com sucesso',
            'appointment': appointment.to_dict_detailed()
        }

        # Enviar notificacao de reagendamento se data/horario mudou
        send_notification = data.get('send_notification', True)
        if send_notification and date_changed and (client.email or client.phone):
            try:
                business_name, _ = get_business_info(user_id)
                channels = data.get('notification_channels', ['email', 'whatsapp'])

                notification_results = NotificationService.send_appointment_rescheduled_notification(
                    appointment=appointment,
                    client=client,
                    professional=professional,
                    service=service,
                    business_name=business_name,
                    old_date=old_date,
                    old_time=old_time,
                    channels=channels
                )
                response_data['notifications'] = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in notification_results.items()}
            except Exception as e:
                response_data['notification_warning'] = f"Agendamento atualizado, mas notificacao falhou: {str(e)}"

        return jsonify(**response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar agendamento: {str(e)}'), 500

@appointments_bp.route('/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Excluir agendamento',
    'parameters': [
        {'name': 'appointment_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Agendamento excluído com sucesso'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def delete_appointment(appointment_id):
    """Excluir agendamento"""
    try:
        user_id = get_current_user_id()
        appointment = Appointment.query.filter_by(id=appointment_id, user_id=user_id).first()

        if not appointment:
            return jsonify(message='Agendamento não encontrado'), 404

        # DEBUG
        print(f"DEBUG - Excluindo agendamento ID: {appointment_id}")

        # Excluir lembretes relacionados primeiro (se existirem)
        try:
            from src.models.reminder import Reminder
            reminders = Reminder.query.filter_by(appointment_id=appointment_id).all()
            print(f"DEBUG - Lembretes encontrados: {len(reminders)}")

            for reminder in reminders:
                print(f"DEBUG - Excluindo lembrete ID: {reminder.id}")
                db.session.delete(reminder)
        except ImportError:
            # Se modelo Reminder não existir, apenas continua
            print("DEBUG - Modelo Reminder não disponível")
            pass

        # Agora excluir o agendamento
        db.session.delete(appointment)
        db.session.commit()

        print(f"DEBUG - Agendamento {appointment_id} excluído com sucesso")
        return jsonify(message='Agendamento excluído com sucesso'), 200

    except Exception as e:
        db.session.rollback()
        print(f"DEBUG - Erro ao excluir: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify(message=f'Erro ao excluir agendamento: {str(e)}'), 500

@appointments_bp.route('/<int:appointment_id>/status', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Atualizar status do agendamento',
    'parameters': [
        {'name': 'appointment_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['status'],
                'properties': {
                    'status': {'type': 'string', 'enum': ['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']},
                    'notes': {'type': 'string'},
                    'price': {'type': 'number'},
                    'payment_method': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Status atualizado com sucesso'},
        400: {'description': 'Status inválido'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def update_appointment_status(appointment_id):
    """Atualizar status do agendamento"""
    try:
        user_id = get_current_user_id()
        appointment = Appointment.query.filter_by(id=appointment_id, user_id=user_id).first()

        if not appointment:
            return jsonify(message='Agendamento não encontrado'), 404
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify(message='Status é obrigatório'), 400
        
        valid_statuses = ['scheduled', 'completed', 'cancelled', 'no_show', 'confirmed']
        if new_status not in valid_statuses:
            return jsonify(message=f'Status inválido. Use: {", ".join(valid_statuses)}'), 400
        
        # Guardar status antigo para notificacao
        old_status = appointment.status

        # Se o status for 'completed', usar função específica para calcular valores
        if new_status == 'completed':
            completion_info = appointment.complete_appointment()
            appointment.notes = data.get('notes', appointment.notes)

            # Criar notificacao in-app de conclusao
            try:
                Notification.notify_appointment_completed(
                    user_id=user_id,
                    appointment=appointment,
                    client=appointment.client,
                    service=appointment.service
                )
            except Exception as e:
                print(f"Erro ao criar notificacao in-app de conclusao: {str(e)}")

            db.session.commit()

            response_data = {
                'message': 'Agendamento concluído com sucesso',
                'appointment': appointment.to_dict_detailed(),
                'calculation': completion_info
            }

            # Enviar notificacao de conclusao (email/whatsapp)
            send_notification = data.get('send_notification', True)
            client = appointment.client
            if send_notification and client and (client.email or client.phone):
                try:
                    business_name, booking_url = get_business_info(user_id)
                    channels = data.get('notification_channels', ['email', 'whatsapp'])

                    notification_results = NotificationService.send_appointment_completed_notification(
                        appointment=appointment,
                        client=client,
                        professional=appointment.professional,
                        service=appointment.service,
                        business_name=business_name,
                        booking_url=booking_url,
                        channels=channels
                    )
                    response_data['notifications'] = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in notification_results.items()}
                except Exception as e:
                    response_data['notification_warning'] = f"Agendamento concluido, mas notificacao falhou: {str(e)}"

            return jsonify(**response_data), 200

        # Para outros status, atualização normal
        appointment.status = new_status
        appointment.notes = data.get('notes', appointment.notes)

        # Permitir override manual do preço
        if 'price' in data and data['price'] is not None:
            appointment.price = data['price']

        # Permitir definir forma de pagamento
        if 'payment_method' in data and data['payment_method'] is not None:
            appointment.payment_method = data['payment_method']

        # Criar notificacoes in-app baseadas na mudanca de status
        try:
            if new_status == 'confirmed' and old_status != 'confirmed':
                Notification.notify_appointment_confirmed(
                    user_id=user_id,
                    appointment=appointment,
                    client=appointment.client
                )
            elif new_status == 'cancelled' and old_status != 'cancelled':
                reason = data.get('cancellation_reason') or data.get('notes')
                Notification.notify_appointment_cancelled(
                    user_id=user_id,
                    appointment=appointment,
                    client=appointment.client,
                    reason=reason
                )
        except Exception as e:
            print(f"Erro ao criar notificacao in-app: {str(e)}")

        db.session.commit()

        response_data = {
            'message': f'Status do agendamento atualizado para {new_status}',
            'appointment': appointment.to_dict_detailed()
        }

        # Enviar notificacoes baseadas na mudanca de status (email/whatsapp)
        send_notification = data.get('send_notification', True)
        client = appointment.client
        if send_notification and client and (client.email or client.phone):
            try:
                business_name, booking_url = get_business_info(user_id)
                channels = data.get('notification_channels', ['email', 'whatsapp'])

                notification_results = {}

                if new_status == 'confirmed' and old_status != 'confirmed':
                    notification_results = NotificationService.send_appointment_confirmed_notification(
                        appointment=appointment,
                        client=client,
                        professional=appointment.professional,
                        service=appointment.service,
                        business_name=business_name,
                        channels=channels
                    )
                elif new_status == 'cancelled' and old_status != 'cancelled':
                    reason = data.get('cancellation_reason') or data.get('notes')
                    notification_results = NotificationService.send_appointment_cancelled_notification(
                        appointment=appointment,
                        client=client,
                        service=appointment.service,
                        business_name=business_name,
                        reason=reason,
                        booking_url=booking_url,
                        channels=channels
                    )

                if notification_results:
                    response_data['notifications'] = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in notification_results.items()}
            except Exception as e:
                response_data['notification_warning'] = f"Status atualizado, mas notificacao falhou: {str(e)}"

        return jsonify(**response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar status do agendamento: {str(e)}'), 500

@appointments_bp.route('/<int:appointment_id>/complete', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Concluir agendamento',
    'description': 'Marca o agendamento como concluído com cálculo automático de valores',
    'parameters': [
        {'name': 'appointment_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'notes': {'type': 'string'},
                    'custom_price': {'type': 'number', 'description': 'Preço customizado (override)'},
                    'payment_method': {'type': 'string', 'example': 'pix'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Agendamento concluído com sucesso'},
        400: {'description': 'Agendamento já concluído ou cancelado'},
        404: {'description': 'Agendamento não encontrado'}
    }
})
def complete_appointment(appointment_id):
    """Marcar agendamento como concluído com cálculo automático de valores"""
    try:
        user_id = get_current_user_id()
        appointment = Appointment.query.filter_by(id=appointment_id, user_id=user_id).first()

        if not appointment:
            return jsonify(message='Agendamento não encontrado'), 404
        
        # Verificar se o agendamento pode ser concluído
        if appointment.status == 'completed':
            return jsonify(message='Agendamento já está concluído'), 400
        
        if appointment.status in ['cancelled', 'no_show']:
            return jsonify(message=f'Não é possível concluir agendamento com status {appointment.status}'), 400
        
        data = request.get_json() or {}
        
        # Marcar como concluído e calcular valores
        completion_info = appointment.complete_appointment()
        
        # Permitir observações adicionais
        if data.get('notes'):
            if appointment.notes:
                appointment.notes += f"\n\nObservações da conclusão: {data['notes']}"
            else:
                appointment.notes = f"Observações da conclusão: {data['notes']}"
        
        # Permitir override manual do preço se fornecido
        if 'custom_price' in data and data['custom_price'] is not None:
            appointment.price = data['custom_price']
            completion_info['price_calculated'] = float(data['custom_price'])
            completion_info['price_override'] = True
        
        # Definir forma de pagamento
        if 'payment_method' in data and data['payment_method'] is not None:
            appointment.payment_method = data['payment_method']
            completion_info['payment_method'] = data['payment_method']
        
        db.session.commit()
        
        # Estatísticas adicionais
        service_stats = {
            'service_name': appointment.service.name,
            'service_duration': appointment.service.duration,
            'original_price': float(appointment.service.price),
            'final_price': float(appointment.price),
            'professional': appointment.professional.name,
            'client': appointment.client.name,
            'date': appointment.appointment_date.isoformat(),
            'time': f"{appointment.start_time.strftime('%H:%M')} - {appointment.end_time.strftime('%H:%M')}"
        }

        response_data = {
            'message': 'Agendamento concluído com sucesso e valores calculados',
            'appointment': appointment.to_dict_detailed(),
            'calculation': completion_info,
            'service_details': service_stats
        }

        # Enviar notificacao de conclusao
        send_notification = data.get('send_notification', True)
        client = appointment.client
        if send_notification and client and (client.email or client.phone):
            try:
                business_name, booking_url = get_business_info(user_id)
                channels = data.get('notification_channels', ['email', 'whatsapp'])

                notification_results = NotificationService.send_appointment_completed_notification(
                    appointment=appointment,
                    client=client,
                    professional=appointment.professional,
                    service=appointment.service,
                    business_name=business_name,
                    price=float(appointment.price) if appointment.price else None,
                    payment_method=appointment.payment_method,
                    booking_url=booking_url,
                    channels=channels
                )
                response_data['notifications'] = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in notification_results.items()}
            except Exception as e:
                response_data['notification_warning'] = f"Agendamento concluido, mas notificacao falhou: {str(e)}"

        return jsonify(**response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao concluir agendamento: {str(e)}'), 500

@appointments_bp.route('/calendar', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Obter agendamentos para calendário',
    'description': 'Retorna agendamentos formatados para visualização em calendário',
    'parameters': [
        {'name': 'start_date', 'in': 'query', 'type': 'string', 'format': 'date', 'required': True},
        {'name': 'end_date', 'in': 'query', 'type': 'string', 'format': 'date', 'required': True},
        {'name': 'professional_id', 'in': 'query', 'type': 'integer'}
    ],
    'responses': {
        200: {'description': 'Eventos do calendário'},
        400: {'description': 'Datas obrigatórias não fornecidas'}
    }
})
def get_calendar_appointments():
    """Obter agendamentos para visualização em calendário"""
    try:
        user_id = get_current_user_id()

        # Parâmetros obrigatórios
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify(message='start_date e end_date são obrigatórios'), 400

        # Validar datas
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify(message='Formato de data inválido. Use YYYY-MM-DD'), 400

        # Filtros opcionais
        professional_id = request.args.get('professional_id')

        # Query - FILTRAR POR EMPRESA
        query = Appointment.query.filter(
            Appointment.user_id == user_id,
            Appointment.appointment_date >= start_date_obj,
            Appointment.appointment_date <= end_date_obj
        )

        if professional_id:
            query = query.filter(Appointment.professional_id == int(professional_id))

        appointments = query.order_by(
            Appointment.appointment_date,
            Appointment.start_time
        ).all()
        
        # Formatar para calendário
        calendar_events = []
        for appointment in appointments:
            event = {
                'id': appointment.id,
                'title': f'{appointment.client.name} - {appointment.service.name}',
                'start': f'{appointment.appointment_date}T{appointment.start_time}',
                'end': f'{appointment.appointment_date}T{appointment.end_time}',
                'backgroundColor': appointment.professional.color,
                'borderColor': appointment.professional.color,
                'textColor': '#ffffff',
                'extendedProps': {
                    'appointment': appointment.to_dict_detailed()
                }
            }
            calendar_events.append(event)
        
        return jsonify(events=calendar_events), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao obter agendamentos do calendário: {str(e)}'), 500

@appointments_bp.route('/check-availability', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Verificar disponibilidade de horário',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['professional_id', 'service_id', 'appointment_date', 'start_time'],
                'properties': {
                    'professional_id': {'type': 'integer'},
                    'service_id': {'type': 'integer'},
                    'appointment_date': {'type': 'string', 'format': 'date'},
                    'start_time': {'type': 'string', 'example': '09:00'},
                    'exclude_appointment_id': {'type': 'integer', 'description': 'ID do agendamento a excluir (para reagendamento)'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Disponibilidade verificada',
            'schema': {
                'type': 'object',
                'properties': {
                    'available': {'type': 'boolean'},
                    'end_time': {'type': 'string'}
                }
            }
        }
    }
})
def check_availability():
    """Verificar disponibilidade de horário"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Validar dados obrigatórios
        required_fields = ['professional_id', 'service_id', 'appointment_date', 'start_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify(message=f'{field} é obrigatório'), 400

        # Validar e converter data
        try:
            appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify(message='Formato de data inválido. Use YYYY-MM-DD'), 400

        # Validar e converter horário
        try:
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            return jsonify(message='Formato de horário inválido. Use HH:MM'), 400

        # Buscar serviço para obter duração - VERIFICAR SE PERTENCE AO USUÁRIO
        service = Service.query.filter_by(id=data['service_id'], user_id=user_id).first()
        if not service:
            return jsonify(message='Serviço não encontrado'), 404
        
        # Calcular horário de fim
        start_datetime = datetime.combine(appointment_date, start_time)
        end_datetime = start_datetime + timedelta(minutes=service.duration)
        end_time = end_datetime.time()
        
        # Verificar disponibilidade
        exclude_id = data.get('exclude_appointment_id')  # Para reagendamento
        is_available = not Appointment.check_conflict(
            data['professional_id'], 
            appointment_date, 
            start_time, 
            end_time, 
            exclude_id
        )
        
        return jsonify(
            available=is_available,
            end_time=end_time.strftime('%H:%M')
        ), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao verificar disponibilidade: {str(e)}'), 500

@appointments_bp.route('/financial-report', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Agendamentos'],
    'summary': 'Relatório financeiro',
    'description': 'Retorna relatório financeiro dos agendamentos concluídos',
    'parameters': [
        {'name': 'start_date', 'in': 'query', 'type': 'string', 'format': 'date'},
        {'name': 'end_date', 'in': 'query', 'type': 'string', 'format': 'date'},
        {'name': 'professional_id', 'in': 'query', 'type': 'integer'},
        {'name': 'service_id', 'in': 'query', 'type': 'integer'}
    ],
    'responses': {
        200: {
            'description': 'Relatório financeiro',
            'schema': {
                'type': 'object',
                'properties': {
                    'financial_summary': {
                        'type': 'object',
                        'properties': {
                            'total_revenue': {'type': 'number'},
                            'total_appointments': {'type': 'integer'},
                            'average_ticket': {'type': 'number'}
                        }
                    },
                    'service_breakdown': {'type': 'object'},
                    'professional_breakdown': {'type': 'object'},
                    'payment_breakdown': {'type': 'object'}
                }
            }
        }
    }
})
def get_financial_report():
    """Obter relatório financeiro dos agendamentos concluídos"""
    try:
        user_id = get_current_user_id()

        # Parâmetros de filtro
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        professional_id = request.args.get('professional_id')
        service_id = request.args.get('service_id')

        # Query base para agendamentos concluídos - FILTRAR POR EMPRESA
        query = Appointment.query.filter(
            Appointment.user_id == user_id,
            Appointment.status == 'completed'
        )
        
        # Aplicar filtros de data
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Appointment.appointment_date >= start_date_obj)
            except ValueError:
                return jsonify(message='Formato de data inválido para start_date. Use YYYY-MM-DD'), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Appointment.appointment_date <= end_date_obj)
            except ValueError:
                return jsonify(message='Formato de data inválido para end_date. Use YYYY-MM-DD'), 400
        
        # Filtros adicionais
        if professional_id:
            query = query.filter(Appointment.professional_id == int(professional_id))

        if service_id:
            query = query.filter(Appointment.service_id == int(service_id))
        
        # Buscar agendamentos
        completed_appointments = query.order_by(Appointment.appointment_date.desc()).all()
        
        # Calcular estatísticas financeiras
        total_revenue = sum(float(apt.price) if apt.price else 0 for apt in completed_appointments)
        total_appointments = len(completed_appointments)
        average_ticket = total_revenue / total_appointments if total_appointments > 0 else 0
        
        # Relatório por serviço
        service_summary = {}
        for apt in completed_appointments:
            service_name = apt.service.name
            if service_name not in service_summary:
                service_summary[service_name] = {
                    'count': 0,
                    'total_revenue': 0,
                    'service_id': apt.service_id,
                    'average_price': 0
                }
            
            service_summary[service_name]['count'] += 1
            service_summary[service_name]['total_revenue'] += float(apt.price) if apt.price else 0
        
        # Calcular médias
        for service in service_summary.values():
            service['average_price'] = service['total_revenue'] / service['count'] if service['count'] > 0 else 0
        
        # Relatório por profissional
        professional_summary = {}
        for apt in completed_appointments:
            prof_name = apt.professional.name
            if prof_name not in professional_summary:
                professional_summary[prof_name] = {
                    'count': 0,
                    'total_revenue': 0,
                    'professional_id': apt.professional_id,
                    'average_ticket': 0
                }
            
            professional_summary[prof_name]['count'] += 1
            professional_summary[prof_name]['total_revenue'] += float(apt.price) if apt.price else 0
        
        # Calcular médias para profissionais
        for prof in professional_summary.values():
            prof['average_ticket'] = prof['total_revenue'] / prof['count'] if prof['count'] > 0 else 0
        
        # Relatório por forma de pagamento
        payment_summary = {}
        for apt in completed_appointments:
            payment_method = apt.payment_method or 'não_informado'
            if payment_method not in payment_summary:
                payment_summary[payment_method] = {
                    'count': 0,
                    'total_revenue': 0,
                    'average_ticket': 0
                }
            
            payment_summary[payment_method]['count'] += 1
            payment_summary[payment_method]['total_revenue'] += float(apt.price) if apt.price else 0
        
        # Calcular médias para formas de pagamento
        for payment in payment_summary.values():
            payment['average_ticket'] = payment['total_revenue'] / payment['count'] if payment['count'] > 0 else 0
        
        # Detalhes dos agendamentos
        appointment_details = [
            {
                'id': apt.id,
                'date': apt.appointment_date.isoformat(),
                'client': apt.client.name,
                'professional': apt.professional.name,
                'service': apt.service.name,
                'price': float(apt.price) if apt.price else 0,
                'payment_method': apt.payment_method,
                'duration': apt.service.duration,
                'start_time': apt.start_time.strftime('%H:%M'),
                'end_time': apt.end_time.strftime('%H:%M'),
                'notes': apt.notes
            } for apt in completed_appointments
        ]
        
        return jsonify(
            financial_summary={
                'total_revenue': round(total_revenue, 2),
                'total_appointments': total_appointments,
                'average_ticket': round(average_ticket, 2),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            },
            service_breakdown=service_summary,
            professional_breakdown=professional_summary,
            payment_breakdown=payment_summary,
            appointment_details=appointment_details
        ), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao gerar relatório financeiro: {str(e)}'), 500

