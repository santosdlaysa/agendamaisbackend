from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from src.models.user import db, User
from src.models.client import Client
from src.models.notification import Notification
from src.services.notification_service import NotificationService

clients_bp = Blueprint('clients', __name__)


def get_current_user_id():
    """Obtém o ID do usuário logado"""
    return int(get_jwt_identity())


@clients_bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Listar todos os clientes',
    'description': 'Retorna uma lista paginada de clientes com opção de busca',
    'parameters': [
        {'name': 'search', 'in': 'query', 'type': 'string', 'description': 'Termo de busca (nome, telefone ou email)'},
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1, 'description': 'Número da página'},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 20, 'description': 'Itens por página'},
        {'name': 'include_stats', 'in': 'query', 'type': 'boolean', 'default': False, 'description': 'Incluir estatísticas do cliente'}
    ],
    'responses': {
        200: {
            'description': 'Lista de clientes',
            'schema': {
                'type': 'object',
                'properties': {
                    'clients': {'type': 'array', 'items': {'$ref': '#/definitions/Client'}},
                    'pagination': {'$ref': '#/definitions/Pagination'}
                }
            }
        }
    }
})
def get_clients():
    """Listar todos os clientes"""
    try:
        user_id = get_current_user_id()

        # Parâmetros de busca e paginação
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        include_stats = request.args.get('include_stats', 'false').lower() == 'true'

        # Query base - FILTRAR POR EMPRESA
        query = Client.query.filter_by(user_id=user_id)

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
@jwt_required()
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Obter cliente específico',
    'description': 'Retorna os dados de um cliente pelo ID',
    'parameters': [
        {'name': 'client_id', 'in': 'path', 'type': 'integer', 'required': True, 'description': 'ID do cliente'},
        {'name': 'include_stats', 'in': 'query', 'type': 'boolean', 'default': False, 'description': 'Incluir estatísticas do cliente'}
    ],
    'responses': {
        200: {
            'description': 'Dados do cliente',
            'schema': {
                'type': 'object',
                'properties': {
                    'client': {'$ref': '#/definitions/Client'}
                }
            }
        },
        404: {'description': 'Cliente não encontrado'}
    }
})
def get_client(client_id):
    """Obter cliente específico"""
    try:
        user_id = get_current_user_id()

        # Buscar cliente DA EMPRESA
        client = Client.query.filter_by(id=client_id, user_id=user_id).first()

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
@jwt_required()
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Criar novo cliente',
    'description': 'Cria um novo cliente no sistema',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['name'],
                'properties': {
                    'name': {'type': 'string', 'example': 'Maria Santos'},
                    'phone': {'type': 'string', 'example': '(11) 99999-9999'},
                    'email': {'type': 'string', 'example': 'maria@email.com'},
                    'notes': {'type': 'string', 'example': 'Cliente VIP'}
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Cliente criado com sucesso',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'client': {'$ref': '#/definitions/Client'}
                }
            }
        },
        400: {'description': 'Nome obrigatório ou email já em uso'}
    }
})
def create_client():
    """Criar novo cliente"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Validar dados obrigatórios
        if not data.get('name'):
            return jsonify(message='Nome é obrigatório'), 400

        # Verificar se email já existe NA EMPRESA (se fornecido)
        if data.get('email'):
            existing_client = Client.query.filter_by(
                email=data['email'],
                user_id=user_id
            ).first()
            if existing_client:
                return jsonify(message='Email já está em uso por outro cliente'), 400

        # Criar cliente ASSOCIADO À EMPRESA
        client = Client(
            user_id=user_id,
            name=data['name'],
            phone=data.get('phone'),
            email=data.get('email'),
            notes=data.get('notes')
        )

        db.session.add(client)

        # Criar notificacao in-app para o dashboard
        try:
            Notification.notify_new_client(user_id=user_id, client=client)
        except Exception as e:
            print(f"Erro ao criar notificacao in-app: {str(e)}")

        db.session.commit()

        # Enviar notificacao de boas-vindas para novo cliente (email/whatsapp)
        notification_results = {}
        send_notification = data.get('send_notification', True)

        if send_notification and (client.email or client.phone):
            try:
                # Buscar dados da empresa
                user = User.query.get(user_id)
                business_name = user.business_name or user.name if user else 'Agenda+'

                # Gerar URL de agendamento online se disponivel
                booking_url = None
                if user and user.slug and user.online_booking_enabled:
                    frontend_url = 'https://agendamais.site'
                    booking_url = f"{frontend_url}/agendar/{user.slug}"

                # Definir canais de notificacao
                channels = data.get('notification_channels', ['email', 'whatsapp'])

                # Enviar notificacao
                notification_results = NotificationService.send_new_client_notification(
                    client=client,
                    business_name=business_name,
                    booking_url=booking_url,
                    channels=channels
                )
            except Exception as e:
                # Erro de notificacao nao deve impedir criacao do cliente
                notification_results = {'error': str(e)}

        return jsonify(
            message='Cliente criado com sucesso',
            client=client.to_dict(),
            notifications={k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in notification_results.items()} if notification_results else None
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao criar cliente: {str(e)}'), 500


@clients_bp.route('/<int:client_id>', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Atualizar cliente',
    'description': 'Atualiza os dados de um cliente existente',
    'parameters': [
        {'name': 'client_id', 'in': 'path', 'type': 'integer', 'required': True, 'description': 'ID do cliente'},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['name'],
                'properties': {
                    'name': {'type': 'string', 'example': 'Maria Santos'},
                    'phone': {'type': 'string', 'example': '(11) 99999-9999'},
                    'email': {'type': 'string', 'example': 'maria@email.com'},
                    'notes': {'type': 'string', 'example': 'Cliente VIP'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Cliente atualizado com sucesso',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'client': {'$ref': '#/definitions/Client'}
                }
            }
        },
        400: {'description': 'Nome obrigatório ou email já em uso'},
        404: {'description': 'Cliente não encontrado'}
    }
})
def update_client(client_id):
    """Atualizar cliente"""
    try:
        user_id = get_current_user_id()

        # Buscar cliente DA EMPRESA
        client = Client.query.filter_by(id=client_id, user_id=user_id).first()

        if not client:
            return jsonify(message='Cliente não encontrado'), 404

        data = request.get_json()

        # Validar dados obrigatórios
        if not data.get('name'):
            return jsonify(message='Nome é obrigatório'), 400

        # Verificar se email já existe NA EMPRESA (se fornecido e diferente do atual)
        if data.get('email') and data['email'] != client.email:
            existing_client = Client.query.filter_by(
                email=data['email'],
                user_id=user_id
            ).first()
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
@jwt_required()
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Excluir cliente',
    'description': 'Remove um cliente do sistema. Não é possível excluir clientes com agendamentos.',
    'parameters': [
        {'name': 'client_id', 'in': 'path', 'type': 'integer', 'required': True, 'description': 'ID do cliente'}
    ],
    'responses': {
        200: {'description': 'Cliente excluído com sucesso'},
        400: {'description': 'Cliente possui agendamentos'},
        404: {'description': 'Cliente não encontrado'}
    }
})
def delete_client(client_id):
    """Excluir cliente"""
    try:
        user_id = get_current_user_id()

        # Buscar cliente DA EMPRESA
        client = Client.query.filter_by(id=client_id, user_id=user_id).first()

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
@jwt_required()
@swag_from({
    'tags': ['Clientes'],
    'summary': 'Buscar clientes (autocomplete)',
    'description': 'Busca rápida de clientes por nome ou telefone para autocomplete',
    'parameters': [
        {'name': 'q', 'in': 'query', 'type': 'string', 'required': True, 'description': 'Termo de busca'},
        {'name': 'limit', 'in': 'query', 'type': 'integer', 'default': 10, 'description': 'Limite de resultados'}
    ],
    'responses': {
        200: {
            'description': 'Lista de clientes encontrados',
            'schema': {
                'type': 'object',
                'properties': {
                    'clients': {'type': 'array', 'items': {'$ref': '#/definitions/Client'}}
                }
            }
        }
    }
})
def search_clients():
    """Buscar clientes por nome ou telefone (para autocomplete)"""
    try:
        user_id = get_current_user_id()
        query_param = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))

        if not query_param:
            return jsonify(clients=[]), 200

        # Buscar clientes DA EMPRESA
        clients = Client.query.filter(
            Client.user_id == user_id,
            db.or_(
                Client.name.ilike(f'%{query_param}%'),
                Client.phone.ilike(f'%{query_param}%')
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
