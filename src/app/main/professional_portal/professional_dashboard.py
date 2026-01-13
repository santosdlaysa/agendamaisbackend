from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from flasgger import swag_from
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from src.config.database import db
from src.models.appointment import Appointment
from src.models.client import Client
from src.models.service import Service
from src.models.professional import Professional
from src.models.working_hours import WorkingHours, ProfessionalBlockedDate

professional_dashboard_bp = Blueprint('professional_dashboard', __name__)


def get_current_professional_id():
    """Helper para obter ID do profissional do token JWT"""
    claims = get_jwt()
    if claims.get('type') != 'professional':
        return None
    return claims.get('professional_id')


def professional_required(f):
    """Decorator para verificar se e um profissional"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        claims = get_jwt()
        if claims.get('type') != 'professional':
            return jsonify({'message': 'Acesso restrito a profissionais'}), 403
        return f(*args, **kwargs)
    return decorated_function


@professional_dashboard_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Obter dados da dashboard',
    'description': 'Retorna estatisticas e agenda do profissional',
    'responses': {
        200: {'description': 'Dados da dashboard'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def get_dashboard():
    """Retorna dados da dashboard do profissional"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        month_start = today.replace(day=1)
        next_month = month_start + timedelta(days=32)
        month_end = next_month.replace(day=1) - timedelta(days=1)

        # Stats de hoje
        today_appointments = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional_id,
                Appointment.appointment_date == today
            )
        ).count()

        today_completed = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional_id,
                Appointment.appointment_date == today,
                Appointment.status == 'completed'
            )
        ).count()

        # Stats da semana
        week_appointments = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional_id,
                Appointment.appointment_date >= week_start,
                Appointment.appointment_date <= week_end
            )
        ).count()

        # Stats do mes
        month_query = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional_id,
                Appointment.appointment_date >= month_start,
                Appointment.appointment_date <= month_end
            )
        )

        month_appointments = month_query.count()
        month_completed = month_query.filter(Appointment.status == 'completed').count()
        month_cancelled = month_query.filter(Appointment.status == 'cancelled').count()

        # Receita do mes
        month_revenue = db.session.query(func.sum(Appointment.price)).filter(
            and_(
                Appointment.professional_id == professional_id,
                Appointment.appointment_date >= month_start,
                Appointment.appointment_date <= month_end,
                Appointment.status == 'completed'
            )
        ).scalar() or 0

        # Taxa de conclusao
        total_finished = month_completed + month_cancelled
        completion_rate = round((month_completed / total_finished * 100), 1) if total_finished > 0 else 0

        # Agenda de hoje
        today_schedule = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional_id,
                Appointment.appointment_date == today
            )
        ).order_by(Appointment.start_time).all()

        # Proximos agendamentos
        upcoming = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional_id,
                Appointment.appointment_date >= today,
                Appointment.status.in_(['scheduled', 'confirmed'])
            )
        ).order_by(Appointment.appointment_date, Appointment.start_time).limit(10).all()

        return jsonify({
            'stats': {
                'today_appointments': today_appointments,
                'today_completed': today_completed,
                'today_pending': today_appointments - today_completed,
                'week_appointments': week_appointments,
                'month_appointments': month_appointments,
                'month_completed': month_completed,
                'month_cancelled': month_cancelled,
                'month_revenue': float(month_revenue),
                'completion_rate': completion_rate
            },
            'today_schedule': [{
                'id': apt.id,
                'client_name': apt.client.name if apt.client else 'Cliente',
                'client_phone': apt.client.phone if apt.client else '',
                'service_name': apt.service.name if apt.service else 'Servico',
                'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
                'end_time': apt.end_time.strftime('%H:%M') if apt.end_time else None,
                'status': apt.status,
                'price': float(apt.price) if apt.price else 0
            } for apt in today_schedule],
            'upcoming_appointments': [{
                'id': apt.id,
                'client_name': apt.client.name if apt.client else 'Cliente',
                'appointment_date': apt.appointment_date.strftime('%d/%m/%Y'),
                'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
                'service_name': apt.service.name if apt.service else 'Servico'
            } for apt in upcoming]
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao carregar dashboard: {str(e)}'}), 500


@professional_dashboard_bp.route('/appointments', methods=['GET'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Listar agendamentos',
    'description': 'Lista agendamentos do profissional com filtros',
    'parameters': [
        {'name': 'date', 'in': 'query', 'type': 'string', 'description': 'Data (YYYY-MM-DD)'},
        {'name': 'status', 'in': 'query', 'type': 'string', 'description': 'Status do agendamento'},
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 20}
    ],
    'responses': {
        200: {'description': 'Lista de agendamentos'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def get_appointments():
    """Lista agendamentos do profissional"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        # Filtros
        date = request.args.get('date')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = Appointment.query.filter(Appointment.professional_id == professional_id)

        if date:
            query = query.filter(Appointment.appointment_date == date)

        if status:
            query = query.filter(Appointment.status == status)

        query = query.order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'appointments': [{
                'id': apt.id,
                'client_name': apt.client.name if apt.client else 'Cliente',
                'client_phone': apt.client.phone if apt.client else '',
                'service_name': apt.service.name if apt.service else 'Servico',
                'appointment_date': apt.appointment_date.strftime('%Y-%m-%d'),
                'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
                'end_time': apt.end_time.strftime('%H:%M') if apt.end_time else None,
                'status': apt.status,
                'price': float(apt.price) if apt.price else 0,
                'notes': apt.notes
            } for apt in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao listar agendamentos: {str(e)}'}), 500


@professional_dashboard_bp.route('/appointments/<int:appointment_id>/complete', methods=['PUT'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Concluir agendamento',
    'description': 'Marca agendamento como concluido',
    'parameters': [
        {'name': 'appointment_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'notes': {'type': 'string'},
                    'price': {'type': 'number'},
                    'payment_method': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Agendamento concluido'},
        400: {'description': 'Agendamento nao pode ser concluido'},
        403: {'description': 'Acesso nao autorizado'},
        404: {'description': 'Agendamento nao encontrado'}
    }
})
def complete_appointment(appointment_id):
    """Marca agendamento como concluido"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        appointment = Appointment.query.get(appointment_id)

        if not appointment:
            return jsonify({'message': 'Agendamento nao encontrado'}), 404

        if appointment.professional_id != professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        if appointment.status not in ['scheduled', 'confirmed']:
            return jsonify({'message': 'Agendamento nao pode ser concluido'}), 400

        data = request.get_json() or {}

        appointment.status = 'completed'
        appointment.notes = data.get('notes', appointment.notes)

        if data.get('price'):
            appointment.price = data.get('price')

        if data.get('payment_method'):
            appointment.payment_method = data.get('payment_method')

        db.session.commit()

        return jsonify({'message': 'Agendamento concluido com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao concluir agendamento: {str(e)}'}), 500


@professional_dashboard_bp.route('/schedule', methods=['GET'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Obter agenda',
    'description': 'Retorna agenda do profissional para um periodo',
    'parameters': [
        {'name': 'start_date', 'in': 'query', 'type': 'string', 'required': True, 'description': 'Data inicial (YYYY-MM-DD)'},
        {'name': 'end_date', 'in': 'query', 'type': 'string', 'required': True, 'description': 'Data final (YYYY-MM-DD)'}
    ],
    'responses': {
        200: {'description': 'Agenda do periodo'},
        400: {'description': 'Datas sao obrigatorias'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def get_schedule():
    """Retorna agenda do profissional para um periodo"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            return jsonify({'message': 'start_date e end_date sao obrigatorios'}), 400

        appointments = Appointment.query.filter(
            and_(
                Appointment.professional_id == professional_id,
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date
            )
        ).order_by(Appointment.appointment_date, Appointment.start_time).all()

        return jsonify({
            'appointments': [{
                'id': apt.id,
                'client_name': apt.client.name if apt.client else 'Cliente',
                'service_name': apt.service.name if apt.service else 'Servico',
                'appointment_date': apt.appointment_date.strftime('%Y-%m-%d'),
                'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
                'end_time': apt.end_time.strftime('%H:%M') if apt.end_time else None,
                'status': apt.status
            } for apt in appointments]
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao obter agenda: {str(e)}'}), 500


@professional_dashboard_bp.route('/clients', methods=['GET'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Listar clientes',
    'description': 'Lista clientes atendidos pelo profissional',
    'parameters': [
        {'name': 'search', 'in': 'query', 'type': 'string', 'description': 'Buscar por nome ou telefone'}
    ],
    'responses': {
        200: {'description': 'Lista de clientes'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def get_clients():
    """Lista clientes atendidos pelo profissional"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        search = request.args.get('search', '')

        # Buscar clientes que tem agendamentos com este profissional
        subquery = db.session.query(Appointment.client_id).filter(
            Appointment.professional_id == professional_id
        ).distinct()

        query = Client.query.filter(Client.id.in_(subquery))

        if search:
            query = query.filter(
                db.or_(
                    Client.name.ilike(f'%{search}%'),
                    Client.phone.ilike(f'%{search}%')
                )
            )

        clients = query.order_by(Client.name).all()

        result = []
        for client in clients:
            # Contar agendamentos
            total = Appointment.query.filter(
                and_(
                    Appointment.client_id == client.id,
                    Appointment.professional_id == professional_id
                )
            ).count()

            completed = Appointment.query.filter(
                and_(
                    Appointment.client_id == client.id,
                    Appointment.professional_id == professional_id,
                    Appointment.status == 'completed'
                )
            ).count()

            result.append({
                'id': client.id,
                'name': client.name,
                'phone': client.phone,
                'email': client.email,
                'total_appointments': total,
                'completed_appointments': completed
            })

        return jsonify({'clients': result}), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao listar clientes: {str(e)}'}), 500


@professional_dashboard_bp.route('/clients/<int:client_id>', methods=['GET'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Detalhes do cliente',
    'description': 'Retorna detalhes de um cliente e historico de atendimentos',
    'parameters': [
        {'name': 'client_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Dados do cliente'},
        403: {'description': 'Acesso nao autorizado'},
        404: {'description': 'Cliente nao encontrado'}
    }
})
def get_client(client_id):
    """Retorna detalhes de um cliente e historico de atendimentos"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        client = Client.query.get(client_id)
        if not client:
            return jsonify({'message': 'Cliente nao encontrado'}), 404

        # Verificar se profissional ja atendeu este cliente
        has_appointments = Appointment.query.filter(
            and_(
                Appointment.client_id == client_id,
                Appointment.professional_id == professional_id
            )
        ).first()

        if not has_appointments:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        # Buscar historico
        appointments = Appointment.query.filter(
            and_(
                Appointment.client_id == client_id,
                Appointment.professional_id == professional_id
            )
        ).order_by(Appointment.appointment_date.desc()).all()

        return jsonify({
            'client': {
                'id': client.id,
                'name': client.name,
                'phone': client.phone,
                'email': client.email
            },
            'appointments': [{
                'id': apt.id,
                'service_name': apt.service.name if apt.service else 'Servico',
                'appointment_date': apt.appointment_date.strftime('%Y-%m-%d'),
                'start_time': apt.start_time.strftime('%H:%M') if apt.start_time else None,
                'status': apt.status,
                'price': float(apt.price) if apt.price else 0,
                'notes': apt.notes
            } for apt in appointments]
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao obter cliente: {str(e)}'}), 500


@professional_dashboard_bp.route('/working-hours', methods=['GET'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Obter horarios de trabalho',
    'responses': {
        200: {'description': 'Horarios de trabalho'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def get_working_hours():
    """Retorna horarios de trabalho do profissional"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        working_hours = WorkingHours.query.filter_by(
            professional_id=professional_id
        ).order_by(WorkingHours.day_of_week).all()

        return jsonify({
            'working_hours': [wh.to_dict() for wh in working_hours]
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao obter horarios: {str(e)}'}), 500


@professional_dashboard_bp.route('/working-hours', methods=['PUT'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Atualizar horarios de trabalho',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'working_hours': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'day_of_week': {'type': 'integer'},
                                'start_time': {'type': 'string'},
                                'end_time': {'type': 'string'},
                                'break_start': {'type': 'string'},
                                'break_end': {'type': 'string'},
                                'is_available': {'type': 'boolean'}
                            }
                        }
                    }
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Horarios atualizados'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def update_working_hours():
    """Atualiza horarios de trabalho"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        data = request.get_json()
        working_hours_data = data.get('working_hours', [])

        # Remover horarios existentes
        WorkingHours.query.filter_by(professional_id=professional_id).delete()

        # Criar novos horarios
        for wh_data in working_hours_data:
            day_of_week = wh_data.get('day_of_week')
            if day_of_week is None or day_of_week < 0 or day_of_week > 6:
                continue

            try:
                start_time = datetime.strptime(wh_data.get('start_time', '08:00'), '%H:%M').time()
                end_time = datetime.strptime(wh_data.get('end_time', '18:00'), '%H:%M').time()

                break_start = None
                break_end = None
                if wh_data.get('break_start'):
                    break_start = datetime.strptime(wh_data['break_start'], '%H:%M').time()
                if wh_data.get('break_end'):
                    break_end = datetime.strptime(wh_data['break_end'], '%H:%M').time()

                wh = WorkingHours(
                    professional_id=professional_id,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    break_start=break_start,
                    break_end=break_end,
                    is_available=wh_data.get('is_available', True)
                )
                db.session.add(wh)
            except ValueError:
                continue

        db.session.commit()

        return jsonify({'message': 'Horarios atualizados com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao atualizar horarios: {str(e)}'}), 500


@professional_dashboard_bp.route('/blocked-dates', methods=['GET'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Obter datas bloqueadas',
    'parameters': [
        {'name': 'start_date', 'in': 'query', 'type': 'string'},
        {'name': 'end_date', 'in': 'query', 'type': 'string'}
    ],
    'responses': {
        200: {'description': 'Datas bloqueadas'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def get_blocked_dates():
    """Retorna datas bloqueadas do profissional"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        query = ProfessionalBlockedDate.query.filter_by(professional_id=professional_id)

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            query = query.filter(ProfessionalBlockedDate.blocked_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(ProfessionalBlockedDate.blocked_date <= datetime.strptime(end_date, '%Y-%m-%d').date())

        blocked_dates = query.order_by(ProfessionalBlockedDate.blocked_date).all()

        return jsonify({
            'blocked_dates': [bd.to_dict() for bd in blocked_dates]
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao obter datas bloqueadas: {str(e)}'}), 500


@professional_dashboard_bp.route('/blocked-dates', methods=['POST'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Adicionar data bloqueada',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['date'],
                'properties': {
                    'date': {'type': 'string', 'example': '2025-01-15'},
                    'reason': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Data bloqueada'},
        400: {'description': 'Data ja bloqueada'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def add_blocked_date():
    """Adiciona data bloqueada"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        data = request.get_json()
        date_str = data.get('date')
        reason = data.get('reason', '')

        if not date_str:
            return jsonify({'message': 'Data e obrigatoria'}), 400

        try:
            blocked_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Formato de data invalido. Use YYYY-MM-DD'}), 400

        # Verificar se ja esta bloqueada
        existing = ProfessionalBlockedDate.query.filter_by(
            professional_id=professional_id,
            blocked_date=blocked_date
        ).first()

        if existing:
            return jsonify({'message': 'Esta data ja esta bloqueada'}), 400

        blocked = ProfessionalBlockedDate(
            professional_id=professional_id,
            blocked_date=blocked_date,
            reason=reason
        )

        db.session.add(blocked)
        db.session.commit()

        return jsonify({
            'message': 'Data bloqueada com sucesso',
            'blocked_date': blocked.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao bloquear data: {str(e)}'}), 500


@professional_dashboard_bp.route('/blocked-dates/<int:blocked_id>', methods=['DELETE'])
@jwt_required()
@professional_required
@swag_from({
    'tags': ['Portal do Profissional - Dashboard'],
    'summary': 'Remover data bloqueada',
    'parameters': [
        {'name': 'blocked_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Data desbloqueada'},
        403: {'description': 'Acesso nao autorizado'},
        404: {'description': 'Data bloqueada nao encontrada'}
    }
})
def remove_blocked_date(blocked_id):
    """Remove data bloqueada"""
    try:
        professional_id = get_current_professional_id()
        if not professional_id:
            return jsonify({'message': 'Acesso nao autorizado'}), 403

        blocked = ProfessionalBlockedDate.query.filter_by(
            id=blocked_id,
            professional_id=professional_id
        ).first()

        if not blocked:
            return jsonify({'message': 'Data bloqueada nao encontrada'}), 404

        db.session.delete(blocked)
        db.session.commit()

        return jsonify({'message': 'Bloqueio removido com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao remover bloqueio: {str(e)}'}), 500
