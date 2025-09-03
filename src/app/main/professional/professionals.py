from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.user import db
from src.models.professional import Professional
from src.models.service import Service

professionals_bp = Blueprint('professionals', __name__)

@professionals_bp.route('', methods=['GET'])
# @jwt_required()  # Temporariamente desabilitado
def get_professionals():
    """Listar todos os profissionais"""
    try:
        # Parâmetros de busca e filtros
        search = request.args.get('search', '')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        include_services = request.args.get('include_services', 'false').lower() == 'true'
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
        # Query base
        query = Professional.query
        
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
# @jwt_required()  # Temporariamente desabilitado
def get_professional(professional_id):
    """Obter profissional específico"""
    try:
        professional = Professional.query.get(professional_id)
        
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
# @jwt_required()  # Temporariamente desabilitado
def create_professional():
    """Criar novo profissional"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('name') or not data.get('role'):
            return jsonify(message='Nome e função são obrigatórios'), 400
        
        # Criar profissional
        professional = Professional(
            name=data['name'],
            role=data['role'],
            phone=data.get('phone'),
            email=data.get('email'),
            color=data.get('color', '#3B82F6'),
            active=data.get('active', True)
        )
        
        db.session.add(professional)
        db.session.flush()  # Para obter o ID
        
        # Associar serviços se fornecidos
        service_ids = data.get('service_ids', [])
        if service_ids:
            services = Service.query.filter(Service.id.in_(service_ids)).all()
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
# @jwt_required()  # Temporariamente desabilitado
def update_professional(professional_id):
    """Atualizar profissional"""
    try:
        professional = Professional.query.get(professional_id)
        
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
        
        # Atualizar serviços se fornecidos
        if 'service_ids' in data:
            service_ids = data['service_ids']
            services = Service.query.filter(Service.id.in_(service_ids)).all()
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
# @jwt_required()  # Temporariamente desabilitado
def delete_professional(professional_id):
    """Excluir profissional"""
    try:
        professional = Professional.query.get(professional_id)
        
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
# @jwt_required()  # Temporariamente desabilitado
def get_professional_services(professional_id):
    """Obter serviços de um profissional"""
    try:
        professional = Professional.query.get(professional_id)
        
        if not professional:
            return jsonify(message='Profissional não encontrado'), 404
        
        services_data = [service.to_dict() for service in professional.services if service.active]
        
        return jsonify(services=services_data), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao obter serviços do profissional: {str(e)}'), 500

@professionals_bp.route('/<int:professional_id>/services', methods=['POST'])
# @jwt_required()  # Temporariamente desabilitado
def update_professional_services(professional_id):
    """Atualizar serviços de um profissional"""
    try:
        professional = Professional.query.get(professional_id)
        
        if not professional:
            return jsonify(message='Profissional não encontrado'), 404
        
        data = request.get_json()
        service_ids = data.get('service_ids', [])
        
        # Buscar serviços
        services = Service.query.filter(Service.id.in_(service_ids)).all()
        
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
# @jwt_required()  # Temporariamente desabilitado
def toggle_professional_status(professional_id):
    """Ativar/desativar profissional"""
    try:
        professional = Professional.query.get(professional_id)
        
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

