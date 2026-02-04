"""
Handlers WebSocket para o chat de suporte em tempo real.
Namespace: /chat
"""
from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token
from src.sockets import socketio
from src.config.database import db
from src.models.user import User
from src.models.chat_conversation import ChatConversation
from src.models.chat_message import ChatMessage
from datetime import datetime

# Mapeamento sid -> {user_id, role}
# manage_session=False desabilita flask.session no socketio,
# entao usamos este dict indexado por sid (unico por conexao)
_sid_to_user = {}


def get_user_from_token(token):
    """Decodifica JWT e retorna user_id e role"""
    try:
        decoded = decode_token(token)
        user_id = int(decoded['sub'])
        user = db.session.get(User, user_id)
        if user:
            return user_id, user.role
    except Exception as e:
        print(f"[Chat WS] Token decode error: {e}")
    return None, None


def get_current_ws_user():
    """Retorna (user_id, role) do socket atual via sid"""
    info = _sid_to_user.get(request.sid)
    if info:
        return info['user_id'], info['role']
    return None, None


@socketio.on('connect', namespace='/chat')
def handle_connect(auth=None):
    """Autenticacao via JWT no parametro auth.token"""
    token = None
    if auth and isinstance(auth, dict):
        token = auth.get('token')

    if not token:
        print(f"[Chat WS] Connection rejected: no token")
        return False

    user_id, role = get_user_from_token(token)
    if not user_id:
        print(f"[Chat WS] Connection rejected: invalid token")
        return False

    # Registrar sid -> usuario
    _sid_to_user[request.sid] = {'user_id': user_id, 'role': role}

    # Entrar na room pessoal
    join_room(f'user_{user_id}')

    # Super admins entram na admin_room
    if role == 'superadmin':
        join_room('admin_room')

    print(f"[Chat WS] User {user_id} ({role}) connected, sid={request.sid}")

    emit('connected', {
        'user_id': user_id,
        'role': role,
        'message': 'Conectado ao chat de suporte'
    })


@socketio.on('disconnect', namespace='/chat')
def handle_disconnect():
    """Remove usuario e loga desconexao"""
    info = _sid_to_user.pop(request.sid, None)
    user_id = info['user_id'] if info else '?'
    print(f"[Chat WS] User {user_id} disconnected, sid={request.sid}")


@socketio.on('join_conversation', namespace='/chat')
def handle_join_conversation(data):
    """Entra na room de uma conversa especifica"""
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        emit('error', {'message': 'conversation_id e obrigatorio'})
        return

    user_id, user_role = get_current_ws_user()
    if not user_id:
        emit('error', {'message': 'Usuario nao autenticado'})
        return

    # Validar acesso
    conversation = db.session.get(ChatConversation, conversation_id)
    if not conversation:
        emit('error', {'message': 'Conversa nao encontrada'})
        return

    if user_role != 'superadmin' and conversation.user_id != user_id:
        emit('error', {'message': 'Acesso negado'})
        return

    join_room(f'conversation_{conversation_id}')
    print(f"[Chat WS] User {user_id} joined conversation_{conversation_id}")
    emit('joined_conversation', {'conversation_id': conversation_id})


@socketio.on('send_message', namespace='/chat')
def handle_send_message(data):
    """Cria mensagem, atualiza conversa, emite para a room"""
    conversation_id = data.get('conversation_id')
    message_text = data.get('message', '').strip()

    if not conversation_id or not message_text:
        emit('error', {'message': 'conversation_id e message sao obrigatorios'})
        return

    user_id, user_role = get_current_ws_user()
    if not user_id:
        emit('error', {'message': 'Usuario nao autenticado'})
        return

    conversation = db.session.get(ChatConversation, conversation_id)
    if not conversation:
        emit('error', {'message': 'Conversa nao encontrada'})
        return

    if user_role != 'superadmin' and conversation.user_id != user_id:
        emit('error', {'message': 'Acesso negado'})
        return

    try:
        sender_role = 'superadmin' if user_role == 'superadmin' else 'user'

        chat_message = ChatMessage(
            conversation_id=conversation_id,
            sender_id=user_id,
            sender_role=sender_role,
            message=message_text
        )
        db.session.add(chat_message)

        now = datetime.utcnow()
        conversation.last_message_text = message_text[:200]
        conversation.last_message_at = now
        conversation.last_message_sender_role = sender_role
        conversation.updated_at = now

        if sender_role == 'user':
            conversation.admin_unread_count += 1
        else:
            conversation.user_unread_count += 1

        if conversation.status == 'closed':
            conversation.status = 'active'

        db.session.commit()

        message_data = chat_message.to_dict()

        print(f"[Chat WS] Message sent by user {user_id} in conversation {conversation_id}")

        # Emitir nova mensagem para a room da conversa
        emit('new_message', message_data, room=f'conversation_{conversation_id}')

        # Notificar admin_room sobre atualizacao da conversa
        emit('conversation_updated', conversation.to_dict(),
             room='admin_room', namespace='/chat')

        # Enviar atualizacao de nao lidas para o usuario da conversa
        emit('unread_update', {
            'conversation_id': conversation_id,
            'user_unread_count': conversation.user_unread_count,
            'admin_unread_count': conversation.admin_unread_count
        }, room=f'user_{conversation.user_id}', namespace='/chat')

    except Exception as e:
        db.session.rollback()
        print(f"[Chat WS] Error sending message: {e}")
        emit('error', {'message': f'Erro ao enviar mensagem: {str(e)}'})


@socketio.on('typing', namespace='/chat')
def handle_typing(data):
    """Emite indicador de digitacao para a room (excluindo o sender)"""
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return

    user_id, user_role = get_current_ws_user()
    if not user_id:
        return

    sender_role = 'superadmin' if user_role == 'superadmin' else 'user'

    emit('typing_indicator', {
        'conversation_id': conversation_id,
        'user_id': user_id,
        'sender_role': sender_role,
        'is_typing': data.get('is_typing', True)
    }, room=f'conversation_{conversation_id}', include_self=False)


@socketio.on('mark_read', namespace='/chat')
def handle_mark_read(data):
    """Marca mensagens do outro como lidas"""
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return

    user_id, user_role = get_current_ws_user()
    if not user_id:
        return

    conversation = db.session.get(ChatConversation, conversation_id)
    if not conversation:
        return

    if user_role != 'superadmin' and conversation.user_id != user_id:
        return

    try:
        now = datetime.utcnow()

        if user_role == 'superadmin':
            ChatMessage.query.filter_by(
                conversation_id=conversation_id,
                sender_role='user',
                read=False
            ).update({'read': True, 'read_at': now})
            conversation.admin_unread_count = 0
        else:
            ChatMessage.query.filter_by(
                conversation_id=conversation_id,
                sender_role='superadmin',
                read=False
            ).update({'read': True, 'read_at': now})
            conversation.user_unread_count = 0

        db.session.commit()

        emit('messages_read', {
            'conversation_id': conversation_id,
            'read_by': user_id,
            'read_by_role': 'superadmin' if user_role == 'superadmin' else 'user',
            'read_at': now.isoformat()
        }, room=f'conversation_{conversation_id}')

        emit('conversation_updated', conversation.to_dict(),
             room='admin_room', namespace='/chat')

    except Exception as e:
        db.session.rollback()
        print(f"[Chat WS] Error marking read: {e}")
        emit('error', {'message': f'Erro ao marcar como lido: {str(e)}'})
