from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.user import db
from src.models.client import Client

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('', methods=['GET'])
# @jwt_required()  # Temporariamente desabilitado
def get_clients():
    """Listar todos os clientes"""
    try:
        # Parâmetros de busca e paginação
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
        # Query base
        query = Client.query
        
        # Aplicar filtro de busca
        if search:
            query = query.filter(
                db.or_(
                    Client.name.ilike(f'%{search}%'),
                    Client.phone.ilike(f'%{search}%'),
                    Client.email.ilike(f'%{search}%')
                )
            )
        
        # Ordenar por nome
        query = query.order_by(Client.name)
        
        # Paginação
        clients = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Serializar dados
        if include_stats:
            clients_data = [client.to_dict_with_stats() for client in clients.items]
        else:
            clients_data = [client.to_dict() for client in clients.items]
        
        return jsonify(
            clients=clients_data,
            pagination={
                'page': clients.page,
                'pages': clients.pages,
                'per_page': clients.per_page,
                'total': clients.total
            }
        ), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao listar clientes: {str(e)}'), 500

@clients_bp.route('/<int:client_id>', methods=['GET'])
# @jwt_required()  # Temporariamente desabilitado
def get_client(client_id):
    """Obter cliente específico"""
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify(message='Cliente não encontrado'), 404
        
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'
        
        if include_stats:
            return jsonify(client=client.to_dict_with_stats()), 200
        else:
            return jsonify(client=client.to_dict()), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao obter cliente: {str(e)}'), 500

@clients_bp.route('', methods=['POST'])
# @jwt_required()  # Temporariamente desabilitado
def create_client():
    """Criar novo cliente"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('name'):
            return jsonify(message='Nome é obrigatório'), 400
        
        # Verificar se email já existe (se fornecido)
        if data.get('email'):
            existing_client = Client.query.filter_by(email=data['email']).first()
            if existing_client:
                return jsonify(message='Email já está em uso por outro cliente'), 400
        
        # Criar cliente
        client = Client(
            name=data['name'],
            phone=data.get('phone'),
            email=data.get('email'),
            notes=data.get('notes')
        )
        
        db.session.add(client)
        db.session.commit()
        
        return jsonify(
            message='Cliente criado com sucesso',
            client=client.to_dict()
        ), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao criar cliente: {str(e)}'), 500

@clients_bp.route('/<int:client_id>', methods=['PUT'])
# @jwt_required()  # Temporariamente desabilitado
def update_client(client_id):
    """Atualizar cliente"""
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify(message='Cliente não encontrado'), 404
        
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('name'):
            return jsonify(message='Nome é obrigatório'), 400
        
        # Verificar se email já existe (se fornecido e diferente do atual)
        if data.get('email') and data['email'] != client.email:
            existing_client = Client.query.filter_by(email=data['email']).first()
            if existing_client:
                return jsonify(message='Email já está em uso por outro cliente'), 400
        
        # Atualizar dados
        client.name = data['name']
        client.phone = data.get('phone')
        client.email = data.get('email')
        client.notes = data.get('notes')
        
        db.session.commit()
        
        return jsonify(
            message='Cliente atualizado com sucesso',
            client=client.to_dict()
        ), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar cliente: {str(e)}'), 500

@clients_bp.route('/<int:client_id>', methods=['DELETE'])
# @jwt_required()  # Temporariamente desabilitado
def delete_client(client_id):
    """Excluir cliente"""
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify(message='Cliente não encontrado'), 404
        
        # Verificar se cliente tem agendamentos
        if client.appointments:
            return jsonify(
                message='Não é possível excluir cliente com agendamentos. Cancele os agendamentos primeiro.'
            ), 400
        
        db.session.delete(client)
        db.session.commit()
        
        return jsonify(message='Cliente excluído com sucesso'), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao excluir cliente: {str(e)}'), 500

@clients_bp.route('/search', methods=['GET'])
# @jwt_required()  # Temporariamente desabilitado
def search_clients():
    """Buscar clientes por nome ou telefone (para autocomplete)"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify(clients=[]), 200
        
        clients = Client.query.filter(
            db.or_(
                Client.name.ilike(f'%{query}%'),
                Client.phone.ilike(f'%{query}%')
            )
        ).limit(limit).all()
        
        clients_data = [{
            'id': client.id,
            'name': client.name,
            'phone': client.phone,
            'email': client.email
        } for client in clients]
        
        return jsonify(clients=clients_data), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao buscar clientes: {str(e)}'), 500

