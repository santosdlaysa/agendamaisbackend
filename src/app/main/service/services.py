from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.user import db
from src.models.service import Service
from src.models.professional import Professional

services_bp = Blueprint('services', __name__)

@services_bp.route('', methods=['GET'])
# @jwt_required()  # Temporariamente desabilitado
def get_services():
    """Listar todos os serviços"""
    try:
        # Parâmetros de busca e filtros
        search = request.args.get('search', '')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        professional_id = request.args.get('professional_id')
        include_professionals = request.args.get('include_professionals', 'false').lower() == 'true'
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
        # Query base
        query = Service.query
        
        # Aplicar filtro de busca
        if search:
            query = query.filter(Service.name.ilike(f'%{search}%'))
        
        # Filtrar apenas ativos
        if active_only:
            query = query.filter(Service.active == True)
        
        # Filtrar por profissional
        if professional_id:
            query = query.join(Service.professionals).filter(Professional.id == professional_id)
        
        # Ordenar por nome
        services = query.order_by(Service.name).all()
        
        # Serializar dados
        if include_stats:
            services_data = [service.to_dict_with_stats() for service in services]
        elif include_professionals:
            services_data = [service.to_dict_with_professionals() for service in services]
        else:
            services_data = [service.to_dict() for service in services]
        
        return jsonify(services=services_data), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao listar serviços: {str(e)}'), 500

@services_bp.route('/<int:service_id>', methods=['GET'])
# @jwt_required()  # Temporariamente desabilitado
def get_service(service_id):
    """Obter serviço específico"""
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify(message='Serviço não encontrado'), 404
        
        include_professionals = request.args.get('include_professionals', 'true').lower() == 'true'
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
        if include_stats:
            return jsonify(service=service.to_dict_with_stats()), 200
        elif include_professionals:
            return jsonify(service=service.to_dict_with_professionals()), 200
        else:
            return jsonify(service=service.to_dict()), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao obter serviço: {str(e)}'), 500

@services_bp.route('', methods=['POST'])
# @jwt_required()  # Temporariamente desabilitado
def create_service():
    """Criar novo serviço"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('name') or not data.get('price') or not data.get('duration'):
            return jsonify(message='Nome, preço e duração são obrigatórios'), 400
        
        # Validar valores numéricos
        try:
            price = float(data['price'])
            duration = int(data['duration'])
            if price < 0 or duration <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify(message='Preço deve ser um número positivo e duração deve ser um número inteiro positivo'), 400
        
        # Criar serviço
        service = Service(
            name=data['name'],
            description=data.get('description'),
            price=price,
            duration=duration,
            color=data.get('color', '#10B981'),
            active=data.get('active', True)
        )
        
        db.session.add(service)
        db.session.flush()  # Para obter o ID
        
        # Associar profissionais se fornecidos
        professional_ids = data.get('professional_ids', [])
        if professional_ids:
            professionals = Professional.query.filter(Professional.id.in_(professional_ids)).all()
            service.professionals = professionals
        
        db.session.commit()
        
        return jsonify(
            message='Serviço criado com sucesso',
            service=service.to_dict_with_professionals()
        ), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao criar serviço: {str(e)}'), 500

@services_bp.route('/<int:service_id>', methods=['PUT'])
# @jwt_required()  # Temporariamente desabilitado
def update_service(service_id):
    """Atualizar serviço"""
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify(message='Serviço não encontrado'), 404
        
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('name') or not data.get('price') or not data.get('duration'):
            return jsonify(message='Nome, preço e duração são obrigatórios'), 400
        
        # Validar valores numéricos
        try:
            price = float(data['price'])
            duration = int(data['duration'])
            if price < 0 or duration <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify(message='Preço deve ser um número positivo e duração deve ser um número inteiro positivo'), 400
        
        # Atualizar dados básicos
        service.name = data['name']
        service.description = data.get('description')
        service.price = price
        service.duration = duration
        service.color = data.get('color', service.color)
        service.active = data.get('active', service.active)
        
        # Atualizar profissionais se fornecidos
        if 'professional_ids' in data:
            professional_ids = data['professional_ids']
            professionals = Professional.query.filter(Professional.id.in_(professional_ids)).all()
            service.professionals = professionals
        
        db.session.commit()
        
        return jsonify(
            message='Serviço atualizado com sucesso',
            service=service.to_dict_with_professionals()
        ), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar serviço: {str(e)}'), 500

@services_bp.route('/<int:service_id>', methods=['DELETE'])
# @jwt_required()  # Temporariamente desabilitado
def delete_service(service_id):
    """Excluir serviço"""
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify(message='Serviço não encontrado'), 404
        
        # Verificar se serviço tem agendamentos futuros
        from datetime import date
        future_appointments = [apt for apt in service.appointments 
                             if apt.appointment_date >= date.today() and apt.status == 'scheduled']
        
        if future_appointments:
            return jsonify(
                message='Não é possível excluir serviço com agendamentos futuros. Cancele os agendamentos primeiro.'
            ), 400
        
        db.session.delete(service)
        db.session.commit()
        
        return jsonify(message='Serviço excluído com sucesso'), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao excluir serviço: {str(e)}'), 500

@services_bp.route('/<int:service_id>/professionals', methods=['GET'])
# @jwt_required()  # Temporariamente desabilitado
def get_service_professionals(service_id):
    """Obter profissionais que realizam um serviço"""
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify(message='Serviço não encontrado'), 404
        
        professionals_data = [prof.to_dict() for prof in service.professionals if prof.active]
        
        return jsonify(professionals=professionals_data), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao obter profissionais do serviço: {str(e)}'), 500

@services_bp.route('/<int:service_id>/professionals', methods=['POST'])
# @jwt_required()  # Temporariamente desabilitado
def update_service_professionals(service_id):
    """Atualizar profissionais que realizam um serviço"""
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify(message='Serviço não encontrado'), 404
        
        data = request.get_json()
        professional_ids = data.get('professional_ids', [])
        
        # Buscar profissionais
        professionals = Professional.query.filter(Professional.id.in_(professional_ids)).all()
        
        # Atualizar associação
        service.professionals = professionals
        db.session.commit()
        
        return jsonify(
            message='Profissionais do serviço atualizados com sucesso',
            professionals=[prof.to_dict() for prof in professionals]
        ), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar profissionais do serviço: {str(e)}'), 500

@services_bp.route('/<int:service_id>/toggle-status', methods=['POST'])
# @jwt_required()  # Temporariamente desabilitado
def toggle_service_status(service_id):
    """Ativar/desativar serviço"""
    try:
        service = Service.query.get(service_id)
        
        if not service:
            return jsonify(message='Serviço não encontrado'), 404
        
        service.active = not service.active
        db.session.commit()
        
        status = 'ativado' if service.active else 'desativado'
        
        return jsonify(
            message=f'Serviço {status} com sucesso',
            service=service.to_dict()
        ), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao alterar status do serviço: {str(e)}'), 500

