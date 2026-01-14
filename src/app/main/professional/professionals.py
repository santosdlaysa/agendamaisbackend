from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from datetime import datetime, time, timedelta
import secrets
from src.models.user import db
from src.models.professional import Professional
from src.models.professional_user import ProfessionalUser
from src.models.service import Service
from src.models.working_hours import WorkingHours, ProfessionalBlockedDate
from src.services.email_service import send_professional_invite_email

professionals_bp = Blueprint('professionals', __name__)


def get_current_user_id():
    """Obtém o ID do usuário logado"""
    return int(get_jwt_identity())

@professionals_bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Listar todos os profissionais',
    'description': 'Retorna uma lista de profissionais com filtros opcionais',
    'parameters': [
        {'name': 'search', 'in': 'query', 'type': 'string', 'description': 'Buscar por nome ou função'},
        {'name': 'active_only', 'in': 'query', 'type': 'boolean', 'default': False, 'description': 'Filtrar apenas ativos'},
        {'name': 'include_services', 'in': 'query', 'type': 'boolean', 'default': False, 'description': 'Incluir serviços'},
        {'name': 'include_stats', 'in': 'query', 'type': 'boolean', 'default': False, 'description': 'Incluir estatísticas'}
    ],
    'responses': {
        200: {
            'description': 'Lista de profissionais',
            'schema': {
                'type': 'object',
                'properties': {
                    'professionals': {'type': 'array', 'items': {'$ref': '#/definitions/Professional'}}
                }
            }
        }
    }
})
def get_professionals():
    """Listar todos os profissionais"""
    try:
        user_id = get_current_user_id()

        # Parâmetros de busca e filtros
        search = request.args.get('search', '')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        include_services = request.args.get('include_services', 'false').lower() == 'true'
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'

        # Query base - FILTRAR POR EMPRESA
        query = Professional.query.filter_by(user_id=user_id)

        # Aplicar filtro de busca
        if search:
            query = query.filter(
                db.or_(
                    Professional.name.ilike(f'%{search}%'),
                    Professional.role.ilike(f'%{search}%')
                )
            )

        # Filtrar apenas ativos
        if active_only:
            query = query.filter(Professional.active == True)

        # Ordenar por nome
        professionals = query.order_by(Professional.name).all()

        # Serializar dados
        if include_stats:
            professionals_data = [prof.to_dict_with_stats() for prof in professionals]
        elif include_services:
            professionals_data = [prof.to_dict_with_services() for prof in professionals]
        else:
            professionals_data = [prof.to_dict() for prof in professionals]

        return jsonify(professionals=professionals_data), 200

    except Exception as e:
        return jsonify(message=f'Erro ao listar profissionais: {str(e)}'), 500

@professionals_bp.route('/<int:professional_id>', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Obter profissional específico',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'include_services', 'in': 'query', 'type': 'boolean', 'default': True},
        {'name': 'include_stats', 'in': 'query', 'type': 'boolean', 'default': False}
    ],
    'responses': {
        200: {'description': 'Dados do profissional'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def get_professional(professional_id):
    """Obter profissional específico"""
    try:
        user_id = get_current_user_id()

        # Buscar profissional DA EMPRESA
        professional = Professional.query.filter_by(id=professional_id, user_id=user_id).first()

        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        include_services = request.args.get('include_services', 'true').lower() == 'true'
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'

        if include_stats:
            return jsonify(professional=professional.to_dict_with_stats()), 200
        elif include_services:
            return jsonify(professional=professional.to_dict_with_services()), 200
        else:
            return jsonify(professional=professional.to_dict()), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter profissional: {str(e)}'), 500

@professionals_bp.route('', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Criar novo profissional',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['name', 'role'],
                'properties': {
                    'name': {'type': 'string', 'example': 'Dr. Carlos Silva'},
                    'role': {'type': 'string', 'example': 'Fisioterapeuta'},
                    'phone': {'type': 'string', 'example': '(11) 99999-9999'},
                    'email': {'type': 'string', 'example': 'carlos@clinica.com'},
                    'color': {'type': 'string', 'example': '#3B82F6'},
                    'active': {'type': 'boolean', 'default': True},
                    'service_ids': {'type': 'array', 'items': {'type': 'integer'}, 'example': [1, 2, 3]}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Profissional criado com sucesso'},
        400: {'description': 'Nome e função são obrigatórios'}
    }
})
def create_professional():
    """Criar novo profissional"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Validar dados obrigatórios
        if not data.get('name') or not data.get('role'):
            return jsonify(message='Nome e função são obrigatórios'), 400

        # Criar profissional ASSOCIADO À EMPRESA
        professional = Professional(
            user_id=user_id,
            name=data['name'],
            role=data['role'],
            phone=data.get('phone'),
            email=data.get('email'),
            color=data.get('color', '#3B82F6'),
            active=data.get('active', True)
        )

        db.session.add(professional)
        db.session.flush()  # Para obter o ID

        # Associar serviços DA EMPRESA se fornecidos
        service_ids = data.get('service_ids', [])
        if service_ids:
            services = Service.query.filter(
                Service.id.in_(service_ids),
                Service.user_id == user_id
            ).all()
            professional.services = services

        db.session.commit()

        return jsonify(
            message='Profissional criado com sucesso',
            professional=professional.to_dict_with_services()
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao criar profissional: {str(e)}'), 500

@professionals_bp.route('/<int:professional_id>', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Atualizar profissional',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['name', 'role'],
                'properties': {
                    'name': {'type': 'string'},
                    'role': {'type': 'string'},
                    'phone': {'type': 'string'},
                    'email': {'type': 'string'},
                    'color': {'type': 'string'},
                    'active': {'type': 'boolean'},
                    'service_ids': {'type': 'array', 'items': {'type': 'integer'}}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Profissional atualizado com sucesso'},
        400: {'description': 'Nome e função são obrigatórios'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def update_professional(professional_id):
    """Atualizar profissional"""
    try:
        user_id = get_current_user_id()

        # Buscar profissional DA EMPRESA
        professional = Professional.query.filter_by(id=professional_id, user_id=user_id).first()

        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        data = request.get_json()

        # Validar dados obrigatórios
        if not data.get('name') or not data.get('role'):
            return jsonify(message='Nome e função são obrigatórios'), 400

        # Atualizar dados básicos
        professional.name = data['name']
        professional.role = data['role']
        professional.phone = data.get('phone')
        professional.email = data.get('email')
        professional.color = data.get('color', professional.color)
        professional.active = data.get('active', professional.active)

        # Atualizar serviços DA EMPRESA se fornecidos
        if 'service_ids' in data:
            service_ids = data['service_ids']
            services = Service.query.filter(
                Service.id.in_(service_ids),
                Service.user_id == user_id
            ).all()
            professional.services = services

        db.session.commit()

        return jsonify(
            message='Profissional atualizado com sucesso',
            professional=professional.to_dict_with_services()
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar profissional: {str(e)}'), 500

@professionals_bp.route('/<int:professional_id>', methods=['DELETE'])
@jwt_required()
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Excluir profissional',
    'description': 'Remove um profissional. Não é possível excluir com agendamentos futuros.',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Profissional excluído com sucesso'},
        400: {'description': 'Profissional possui agendamentos futuros'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def delete_professional(professional_id):
    """Excluir profissional"""
    try:
        user_id = get_current_user_id()

        # Buscar profissional DA EMPRESA
        professional = Professional.query.filter_by(id=professional_id, user_id=user_id).first()

        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        # Verificar se profissional tem agendamentos futuros
        from datetime import date
        future_appointments = [apt for apt in professional.appointments
                             if apt.appointment_date >= date.today() and apt.status == 'scheduled']

        if future_appointments:
            return jsonify(
                message='Não é possível excluir profissional com agendamentos futuros. Cancele os agendamentos primeiro.'
            ), 400

        db.session.delete(professional)
        db.session.commit()

        return jsonify(message='Profissional excluído com sucesso'), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao excluir profissional: {str(e)}'), 500

@professionals_bp.route('/<int:professional_id>/services', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Obter serviços de um profissional',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Lista de serviços do profissional'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def get_professional_services(professional_id):
    """Obter serviços de um profissional"""
    try:
        user_id = get_current_user_id()
        professional = Professional.query.filter_by(id=professional_id, user_id=user_id).first()

        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        services_data = [service.to_dict() for service in professional.services if service.active]

        return jsonify(services=services_data), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter serviços do profissional: {str(e)}'), 500

@professionals_bp.route('/<int:professional_id>/services', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Atualizar serviços de um profissional',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'service_ids': {'type': 'array', 'items': {'type': 'integer'}, 'example': [1, 2, 3]}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Serviços atualizados com sucesso'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def update_professional_services(professional_id):
    """Atualizar serviços de um profissional"""
    try:
        user_id = get_current_user_id()
        professional = Professional.query.filter_by(id=professional_id, user_id=user_id).first()

        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        data = request.get_json()
        service_ids = data.get('service_ids', [])

        # Buscar serviços (somente da mesma empresa)
        services = Service.query.filter(Service.id.in_(service_ids), Service.user_id == user_id).all()

        # Atualizar associação
        professional.services = services
        db.session.commit()

        return jsonify(
            message='Serviços do profissional atualizados com sucesso',
            services=[service.to_dict() for service in services]
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar serviços do profissional: {str(e)}'), 500

@professionals_bp.route('/<int:professional_id>/toggle-status', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Ativar/desativar profissional',
    'description': 'Alterna o status ativo/inativo do profissional',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Status alterado com sucesso'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def toggle_professional_status(professional_id):
    """Ativar/desativar profissional"""
    try:
        user_id = get_current_user_id()
        professional = Professional.query.filter_by(id=professional_id, user_id=user_id).first()

        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        professional.active = not professional.active
        db.session.commit()

        status = 'ativado' if professional.active else 'desativado'

        return jsonify(
            message=f'Profissional {status} com sucesso',
            professional=professional.to_dict()
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao alterar status do profissional: {str(e)}'), 500


# ============================================
# ROTAS DE HORÁRIOS DE TRABALHO
# ============================================

@professionals_bp.route('/<int:professional_id>/working-hours', methods=['GET'])
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Obter horários de trabalho do profissional',
    'description': 'Retorna os horários de trabalho configurados para o profissional',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Horários de trabalho'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def get_working_hours(professional_id):
    """Obter horários de trabalho do profissional"""
    try:
        professional = Professional.query.get(professional_id)
        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        working_hours = WorkingHours.query.filter_by(
            professional_id=professional_id
        ).order_by(WorkingHours.day_of_week).all()

        return jsonify({
            'professional_id': professional_id,
            'professional_name': professional.name,
            'working_hours': [wh.to_dict() for wh in working_hours]
        }), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter horários de trabalho: {str(e)}'), 500


@professionals_bp.route('/<int:professional_id>/working-hours', methods=['POST'])
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Configurar horários de trabalho',
    'description': 'Configura ou atualiza os horários de trabalho do profissional',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
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
                                'day_of_week': {'type': 'integer', 'minimum': 0, 'maximum': 6},
                                'start_time': {'type': 'string', 'example': '08:00'},
                                'end_time': {'type': 'string', 'example': '18:00'},
                                'break_start': {'type': 'string', 'example': '12:00'},
                                'break_end': {'type': 'string', 'example': '13:00'},
                                'is_available': {'type': 'boolean', 'default': True}
                            }
                        }
                    }
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Horários atualizados com sucesso'},
        400: {'description': 'Dados inválidos'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def set_working_hours(professional_id):
    """Configurar horários de trabalho do profissional"""
    try:
        professional = Professional.query.get(professional_id)
        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        data = request.get_json()
        working_hours_data = data.get('working_hours', [])

        if not working_hours_data:
            return jsonify(message='Lista de horários é obrigatória'), 400

        # Remover horários existentes
        WorkingHours.query.filter_by(professional_id=professional_id).delete()

        # Criar novos horários
        for wh_data in working_hours_data:
            day_of_week = wh_data.get('day_of_week')
            if day_of_week is None or day_of_week < 0 or day_of_week > 6:
                return jsonify(message=f'day_of_week inválido: {day_of_week}'), 400

            try:
                start_time = datetime.strptime(wh_data.get('start_time', '08:00'), '%H:%M').time()
                end_time = datetime.strptime(wh_data.get('end_time', '18:00'), '%H:%M').time()

                break_start = None
                break_end = None
                if wh_data.get('break_start'):
                    break_start = datetime.strptime(wh_data['break_start'], '%H:%M').time()
                if wh_data.get('break_end'):
                    break_end = datetime.strptime(wh_data['break_end'], '%H:%M').time()
            except ValueError as e:
                return jsonify(message=f'Formato de hora inválido: {str(e)}'), 400

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

        db.session.commit()

        # Retornar horários atualizados
        working_hours = WorkingHours.query.filter_by(
            professional_id=professional_id
        ).order_by(WorkingHours.day_of_week).all()

        return jsonify({
            'message': 'Horários de trabalho atualizados com sucesso',
            'working_hours': [wh.to_dict() for wh in working_hours]
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao configurar horários de trabalho: {str(e)}'), 500


@professionals_bp.route('/<int:professional_id>/working-hours/<int:day_of_week>', methods=['PUT'])
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Atualizar horário de um dia específico',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'day_of_week', 'in': 'path', 'type': 'integer', 'required': True, 'description': '0=Segunda, 6=Domingo'},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'start_time': {'type': 'string', 'example': '09:00'},
                    'end_time': {'type': 'string', 'example': '17:00'},
                    'break_start': {'type': 'string', 'example': '12:00'},
                    'break_end': {'type': 'string', 'example': '13:00'},
                    'is_available': {'type': 'boolean'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Horário atualizado'},
        404: {'description': 'Horário não encontrado'}
    }
})
def update_working_hours_day(professional_id, day_of_week):
    """Atualizar horário de um dia específico"""
    try:
        professional = Professional.query.get(professional_id)
        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        wh = WorkingHours.query.filter_by(
            professional_id=professional_id,
            day_of_week=day_of_week
        ).first()

        if not wh:
            return jsonify(message='Horário não encontrado para este dia'), 404

        data = request.get_json()

        if 'start_time' in data:
            wh.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        if 'end_time' in data:
            wh.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        if 'break_start' in data:
            wh.break_start = datetime.strptime(data['break_start'], '%H:%M').time() if data['break_start'] else None
        if 'break_end' in data:
            wh.break_end = datetime.strptime(data['break_end'], '%H:%M').time() if data['break_end'] else None
        if 'is_available' in data:
            wh.is_available = data['is_available']

        db.session.commit()

        return jsonify({
            'message': 'Horário atualizado com sucesso',
            'working_hour': wh.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar horário: {str(e)}'), 500


@professionals_bp.route('/<int:professional_id>/working-hours/default', methods=['POST'])
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Criar horários padrão',
    'description': 'Cria horários padrão para o profissional (Seg-Sex 08:00-18:00, Sáb 08:00-12:00)',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        201: {'description': 'Horários padrão criados'},
        400: {'description': 'Profissional já possui horários configurados'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def create_default_working_hours(professional_id):
    """Criar horários padrão para o profissional"""
    try:
        professional = Professional.query.get(professional_id)
        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        # Verificar se já tem horários
        existing = WorkingHours.query.filter_by(professional_id=professional_id).first()
        if existing:
            return jsonify(message='Profissional já possui horários configurados. Use PUT para atualizar.'), 400

        # Criar horários padrão
        default_hours = WorkingHours.create_default_schedule(professional_id)
        for wh in default_hours:
            db.session.add(wh)

        db.session.commit()

        working_hours = WorkingHours.query.filter_by(
            professional_id=professional_id
        ).order_by(WorkingHours.day_of_week).all()

        return jsonify({
            'message': 'Horários padrão criados com sucesso',
            'working_hours': [wh.to_dict() for wh in working_hours]
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao criar horários padrão: {str(e)}'), 500


# ============================================
# ROTAS DE DATAS BLOQUEADAS
# ============================================

@professionals_bp.route('/<int:professional_id>/blocked-dates', methods=['GET'])
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Obter datas bloqueadas do profissional',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'start_date', 'in': 'query', 'type': 'string', 'description': 'Data inicial (YYYY-MM-DD)'},
        {'name': 'end_date', 'in': 'query', 'type': 'string', 'description': 'Data final (YYYY-MM-DD)'}
    ],
    'responses': {
        200: {'description': 'Lista de datas bloqueadas'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def get_blocked_dates(professional_id):
    """Obter datas bloqueadas do profissional"""
    try:
        professional = Professional.query.get(professional_id)
        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        query = ProfessionalBlockedDate.query.filter_by(professional_id=professional_id)

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if start_date:
            query = query.filter(ProfessionalBlockedDate.blocked_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(ProfessionalBlockedDate.blocked_date <= datetime.strptime(end_date, '%Y-%m-%d').date())

        blocked_dates = query.order_by(ProfessionalBlockedDate.blocked_date).all()

        return jsonify({
            'professional_id': professional_id,
            'professional_name': professional.name,
            'blocked_dates': [bd.to_dict() for bd in blocked_dates]
        }), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter datas bloqueadas: {str(e)}'), 500


@professionals_bp.route('/<int:professional_id>/blocked-dates', methods=['POST'])
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Adicionar data bloqueada',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['blocked_date'],
                'properties': {
                    'blocked_date': {'type': 'string', 'example': '2025-01-15'},
                    'reason': {'type': 'string', 'example': 'Férias'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Data bloqueada adicionada'},
        400: {'description': 'Data já está bloqueada'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def add_blocked_date(professional_id):
    """Adicionar data bloqueada"""
    try:
        professional = Professional.query.get(professional_id)
        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        data = request.get_json()
        blocked_date_str = data.get('blocked_date')

        if not blocked_date_str:
            return jsonify(message='blocked_date é obrigatório'), 400

        try:
            blocked_date = datetime.strptime(blocked_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify(message='Formato de data inválido. Use YYYY-MM-DD'), 400

        # Verificar se já está bloqueada
        existing = ProfessionalBlockedDate.query.filter_by(
            professional_id=professional_id,
            blocked_date=blocked_date
        ).first()

        if existing:
            return jsonify(message='Esta data já está bloqueada'), 400

        blocked = ProfessionalBlockedDate(
            professional_id=professional_id,
            blocked_date=blocked_date,
            reason=data.get('reason')
        )

        db.session.add(blocked)
        db.session.commit()

        return jsonify({
            'message': 'Data bloqueada com sucesso',
            'blocked_date': blocked.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao bloquear data: {str(e)}'), 500


@professionals_bp.route('/<int:professional_id>/blocked-dates/bulk', methods=['POST'])
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Adicionar múltiplas datas bloqueadas',
    'description': 'Bloqueia um período de datas (ex: férias)',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['start_date', 'end_date'],
                'properties': {
                    'start_date': {'type': 'string', 'example': '2025-01-15'},
                    'end_date': {'type': 'string', 'example': '2025-01-30'},
                    'reason': {'type': 'string', 'example': 'Férias'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Datas bloqueadas'},
        400: {'description': 'Dados inválidos'},
        404: {'description': 'Profissional não encontrado'}
    }
})
def add_blocked_dates_bulk(professional_id):
    """Adicionar múltiplas datas bloqueadas"""
    try:
        professional = Professional.query.get(professional_id)
        if not professional:
            return jsonify(message='Profissional não encontrado'), 404

        data = request.get_json()

        try:
            start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return jsonify(message='Formato de data inválido. Use YYYY-MM-DD'), 400

        if start_date > end_date:
            return jsonify(message='Data inicial não pode ser maior que data final'), 400

        reason = data.get('reason')
        dates_added = []
        dates_skipped = []

        current_date = start_date
        while current_date <= end_date:
            existing = ProfessionalBlockedDate.query.filter_by(
                professional_id=professional_id,
                blocked_date=current_date
            ).first()

            if not existing:
                blocked = ProfessionalBlockedDate(
                    professional_id=professional_id,
                    blocked_date=current_date,
                    reason=reason
                )
                db.session.add(blocked)
                dates_added.append(current_date.isoformat())
            else:
                dates_skipped.append(current_date.isoformat())

            current_date += timedelta(days=1)

        db.session.commit()

        return jsonify({
            'message': f'{len(dates_added)} data(s) bloqueada(s) com sucesso',
            'dates_added': dates_added,
            'dates_skipped': dates_skipped
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao bloquear datas: {str(e)}'), 500


@professionals_bp.route('/<int:professional_id>/blocked-dates/<int:blocked_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Remover data bloqueada',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'blocked_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Data desbloqueada'},
        404: {'description': 'Data bloqueada não encontrada'}
    }
})
def remove_blocked_date(professional_id, blocked_id):
    """Remover data bloqueada"""
    try:
        blocked = ProfessionalBlockedDate.query.filter_by(
            id=blocked_id,
            professional_id=professional_id
        ).first()

        if not blocked:
            return jsonify(message='Data bloqueada não encontrada'), 404

        date_removed = blocked.blocked_date.isoformat()
        db.session.delete(blocked)
        db.session.commit()

        return jsonify({
            'message': 'Data desbloqueada com sucesso',
            'date_removed': date_removed
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao desbloquear data: {str(e)}'), 500



# ============================================
# ROTA DE CONVITE PARA PORTAL DO PROFISSIONAL
# ============================================

@professionals_bp.route('/<int:professional_id>/invite', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Profissionais'],
    'summary': 'Enviar convite para profissional acessar o portal',
    'parameters': [
        {'name': 'professional_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['email'],
                'properties': {
                    'email': {'type': 'string', 'format': 'email'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Convite enviado com sucesso'},
        400: {'description': 'Dados invalidos ou conta ja existe'},
        404: {'description': 'Profissional nao encontrado'}
    }
})
def invite_professional_to_portal(professional_id):
    """Envia convite para profissional criar conta no portal"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'message': 'Email e obrigatorio'}), 400

        # Verificar se profissional existe e pertence ao usuario
        professional = Professional.query.filter_by(
            id=professional_id,
            user_id=user_id
        ).first()

        if not professional:
            return jsonify({'message': 'Profissional nao encontrado'}), 404

        # Verificar se ja existe conta com este email
        existing_email = ProfessionalUser.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({'message': 'Ja existe uma conta com este email'}), 400

        # Verificar se profissional ja tem conta
        existing_professional = ProfessionalUser.query.filter_by(professional_id=professional_id).first()
        if existing_professional:
            return jsonify({'message': 'Profissional ja possui uma conta'}), 400

        # Criar usuario com token de convite
        invite_token = secrets.token_urlsafe(32)
        professional_user = ProfessionalUser(
            professional_id=professional_id,
            email=email,
            invite_token=invite_token,
            invite_expires_at=datetime.utcnow() + timedelta(hours=48)
        )

        db.session.add(professional_user)
        db.session.commit()

        # Enviar email com link de ativacao
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        activation_url = f"{frontend_url}/#/profissional/ativar/{invite_token}"

        email_sent, email_message = send_professional_invite_email(
            email=email,
            professional_name=professional.name,
            activation_url=activation_url
        )

        return jsonify({
            'message': 'Convite enviado com sucesso',
            'email_sent': email_sent,
            'invite_link': f'/profissional/ativar/{invite_token}'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao enviar convite: {str(e)}'}), 500
