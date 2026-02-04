"""
Rotas REST do Chat de Suporte para o sistema AgendaMais
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from src.config.database import db
from src.models.user import User
from src.models.chat_conversation import ChatConversation
from src.models.chat_message import ChatMessage
from datetime import datetime

chat_bp = Blueprint('chat', __name__)


def get_current_user_id():
    """Obtem o ID do usuario logado"""
    return int(get_jwt_identity())


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Chat Suporte'],
    'summary': 'Listar conversas',
    'description': 'Admin: todas as conversas (paginadas). User: apenas a sua.',
    'parameters': [
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 20},
        {'name': 'status', 'in': 'query', 'type': 'string', 'description': 'Filtrar por status (active/closed)'}
    ],
    'responses': {
        200: {'description': 'Lista de conversas'}
    }
})
def get_conversations():
    """Lista conversas de suporte"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'Usuario nao encontrado'}), 404

        if user.role == 'superadmin':
            # Admin ve todas as conversas
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status_filter = request.args.get('status')

            query = ChatConversation.query
            if status_filter:
                query = query.filter_by(status=status_filter)

            query = query.order_by(ChatConversation.last_message_at.desc().nullslast())
            conversations = query.paginate(page=page, per_page=per_page, error_out=False)

            return jsonify({
                'conversations': [c.to_dict() for c in conversations.items],
                'pagination': {
                    'page': conversations.page,
                    'pages': conversations.pages,
                    'per_page': conversations.per_page,
                    'total': conversations.total
                }
            }), 200
        else:
            # Usuario ve apenas sua conversa
            conversation = ChatConversation.query.filter_by(user_id=user_id).first()
            conversations = [conversation.to_dict()] if conversation else []

            return jsonify({
                'conversations': conversations,
                'pagination': {
                    'page': 1,
                    'pages': 1,
                    'per_page': 1,
                    'total': len(conversations)
                }
            }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao listar conversas: {str(e)}'}), 500


@chat_bp.route('/conversations', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Chat Suporte'],
    'summary': 'Criar ou obter conversa',
    'description': 'Cria uma nova conversa ou retorna a existente. Admin envia user_id no body.',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'integer', 'description': 'ID do usuario (obrigatorio para admin)'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Conversa existente retornada'},
        201: {'description': 'Nova conversa criada'}
    }
})
def create_conversation():
    """Cria ou retorna conversa existente"""
    try:
        current_user_id = get_current_user_id()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'message': 'Usuario nao encontrado'}), 404

        if current_user.role == 'superadmin':
            # Admin precisa informar o user_id
            data = request.get_json() or {}
            target_user_id = data.get('user_id')
            if not target_user_id:
                return jsonify({'message': 'user_id e obrigatorio para admin'}), 400

            target_user = User.query.get(target_user_id)
            if not target_user:
                return jsonify({'message': 'Usuario alvo nao encontrado'}), 404
        else:
            target_user_id = current_user_id

        # Verificar se ja existe conversa para este usuario
        conversation = ChatConversation.query.filter_by(user_id=target_user_id).first()
        if conversation:
            return jsonify({
                'message': 'Conversa existente',
                'conversation': conversation.to_dict()
            }), 200

        # Criar nova conversa
        conversation = ChatConversation(
            user_id=target_user_id,
            status='active'
        )
        db.session.add(conversation)
        db.session.commit()

        return jsonify({
            'message': 'Conversa criada com sucesso',
            'conversation': conversation.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao criar conversa: {str(e)}'}), 500


@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Chat Suporte'],
    'summary': 'Historico de mensagens',
    'description': 'Retorna mensagens paginadas de uma conversa.',
    'parameters': [
        {'name': 'conversation_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 50}
    ],
    'responses': {
        200: {'description': 'Lista de mensagens'},
        403: {'description': 'Acesso negado'},
        404: {'description': 'Conversa nao encontrada'}
    }
})
def get_messages(conversation_id):
    """Retorna historico de mensagens paginado"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'Usuario nao encontrado'}), 404

        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'message': 'Conversa nao encontrada'}), 404

        # Validar acesso
        if user.role != 'superadmin' and conversation.user_id != user_id:
            return jsonify({'message': 'Acesso negado'}), 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        messages = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(
            ChatMessage.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'messages': [m.to_dict() for m in messages.items],
            'pagination': {
                'page': messages.page,
                'pages': messages.pages,
                'per_page': messages.per_page,
                'total': messages.total
            }
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao listar mensagens: {str(e)}'}), 500


@chat_bp.route('/conversations/<int:conversation_id>/read', methods=['PATCH'])
@jwt_required()
@swag_from({
    'tags': ['Chat Suporte'],
    'summary': 'Marcar mensagens como lidas',
    'description': 'Marca mensagens do outro participante como lidas.',
    'parameters': [
        {'name': 'conversation_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Mensagens marcadas como lidas'},
        403: {'description': 'Acesso negado'},
        404: {'description': 'Conversa nao encontrada'}
    }
})
def mark_messages_read(conversation_id):
    """Marca mensagens do outro participante como lidas"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'Usuario nao encontrado'}), 404

        conversation = ChatConversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'message': 'Conversa nao encontrada'}), 404

        # Validar acesso
        if user.role != 'superadmin' and conversation.user_id != user_id:
            return jsonify({'message': 'Acesso negado'}), 403

        now = datetime.utcnow()

        if user.role == 'superadmin':
            # Admin lendo -> marca mensagens do user como lidas
            updated = ChatMessage.query.filter_by(
                conversation_id=conversation_id,
                sender_role='user',
                read=False
            ).update({'read': True, 'read_at': now})
            conversation.admin_unread_count = 0
        else:
            # User lendo -> marca mensagens do admin como lidas
            updated = ChatMessage.query.filter_by(
                conversation_id=conversation_id,
                sender_role='superadmin',
                read=False
            ).update({'read': True, 'read_at': now})
            conversation.user_unread_count = 0

        db.session.commit()

        return jsonify({
            'message': f'{updated} mensagens marcadas como lidas',
            'conversation': conversation.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao marcar como lido: {str(e)}'}), 500


@chat_bp.route('/conversations/unread-count', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Chat Suporte'],
    'summary': 'Total de mensagens nao lidas',
    'description': 'Admin: soma de todas conversas. User: da sua conversa.',
    'responses': {
        200: {'description': 'Contagem de nao lidas'}
    }
})
def get_unread_count():
    """Retorna total de mensagens nao lidas"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'Usuario nao encontrado'}), 404

        if user.role == 'superadmin':
            # Admin: soma admin_unread_count de todas as conversas
            total = db.session.query(
                db.func.coalesce(db.func.sum(ChatConversation.admin_unread_count), 0)
            ).scalar()
        else:
            # User: user_unread_count da sua conversa
            conversation = ChatConversation.query.filter_by(user_id=user_id).first()
            total = conversation.user_unread_count if conversation else 0

        return jsonify({
            'unread_count': total
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao contar nao lidas: {str(e)}'}), 500
