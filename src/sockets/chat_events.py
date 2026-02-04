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

# Usuarios conectados: {user_id: {sid, role}}
connected_users = {}


def get_user_from_token(token):
    """Decodifica JWT e retorna user_id e role"""
    try:
        decoded = decode_token(token)
        user_id = int(decoded['sub'])
        user = User.query.get(user_id)
        if user:
            return user_id, user.role
    except Exception:
        pass
    return None, None


@socketio.on('connect', namespace='/chat')
def handle_connect(auth=None):
    """Autenticacao via JWT no parametro auth.token"""
    token = None
    if auth and isinstance(auth, dict):
        token = auth.get('token')

    if not token:
        disconnect()
        return False

    user_id, role = get_user_from_token(token)
    if not user_id:
        disconnect()
        return False

    # Registrar usuario conectado
    connected_users[user_id] = {'sid': request.sid, 'role': role}

    # Entrar na room pessoal
    join_room(f'user_{user_id}')

    # Super admins entram na admin_room
    if role == 'superadmin':
        join_room('admin_room')

    emit('connected', {
        'user_id': user_id,
        'role': role,
        'message': 'Conectado ao chat de suporte'
    })


@socketio.on('disconnect', namespace='/chat')
def handle_disconnect():
    """Remove usuario dos conectados"""
    user_to_remove = None
    for uid, data in connected_users.items():
        if data['sid'] == request.sid:
            user_to_remove = uid
            break
    if user_to_remove:
        del connected_users[user_to_remove]


@socketio.on('join_conversation', namespace='/chat')
def handle_join_conversation(data):
    """Entra na room de uma conversa especifica"""
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return

    # Identificar usuario pelo sid
    user_id = None
    user_role = None
    for uid, udata in connected_users.items():
        if udata['sid'] == request.sid:
            user_id = uid
            user_role = udata['role']
            break

    if not user_id:
        return

    # Validar acesso: usuario so acessa sua propria conversa, superadmin acessa todas
    conversation = ChatConversation.query.get(conversation_id)
    if not conversation:
        emit('error', {'message': 'Conversa nao encontrada'})
        return

    if user_role != 'superadmin' and conversation.user_id != user_id:
        emit('error', {'message': 'Acesso negado'})
        return

    join_room(f'conversation_{conversation_id}')
    emit('joined_conversation', {'conversation_id': conversation_id})


@socketio.on('send_message', namespace='/chat')
def handle_send_message(data):
    """Cria mensagem, atualiza conversa, emite para a room"""
    conversation_id = data.get('conversation_id')
    message_text = data.get('message', '').strip()

    if not conversation_id or not message_text:
        emit('error', {'message': 'conversation_id e message sao obrigatorios'})
        return

    # Identificar usuario
    user_id = None
    user_role = None
    for uid, udata in connected_users.items():
        if udata['sid'] == request.sid:
            user_id = uid
            user_role = udata['role']
            break

    if not user_id:
        emit('error', {'message': 'Usuario nao autenticado'})
        return

    # Validar acesso a conversa
    conversation = ChatConversation.query.get(conversation_id)
    if not conversation:
        emit('error', {'message': 'Conversa nao encontrada'})
        return

    if user_role != 'superadmin' and conversation.user_id != user_id:
        emit('error', {'message': 'Acesso negado'})
        return

    try:
        # Determinar sender_role
        sender_role = 'superadmin' if user_role == 'superadmin' else 'user'

        # Criar mensagem
        chat_message = ChatMessage(
            conversation_id=conversation_id,
            sender_id=user_id,
            sender_role=sender_role,
            message=message_text
        )
        db.session.add(chat_message)

        # Atualizar preview da conversa
        now = datetime.utcnow()
        conversation.last_message_text = message_text[:200]
        conversation.last_message_at = now
        conversation.last_message_sender_role = sender_role
        conversation.updated_at = now

        # Incrementar contadores de nao lidas
        if sender_role == 'user':
            conversation.admin_unread_count += 1
        else:
            conversation.user_unread_count += 1

        # Reabrir conversa se estava fechada
        if conversation.status == 'closed':
            conversation.status = 'active'

        db.session.commit()

        message_data = chat_message.to_dict()

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
        emit('error', {'message': f'Erro ao enviar mensagem: {str(e)}'})


@socketio.on('typing', namespace='/chat')
def handle_typing(data):
    """Emite indicador de digitacao para a room (excluindo o sender)"""
    conversation_id = data.get('conversation_id')
    if not conversation_id:
        return

    # Identificar usuario
    user_id = None
    user_role = None
    for uid, udata in connected_users.items():
        if udata['sid'] == request.sid:
            user_id = uid
            user_role = udata['role']
            break

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

    # Identificar usuario
    user_id = None
    user_role = None
    for uid, udata in connected_users.items():
        if udata['sid'] == request.sid:
            user_id = uid
            user_role = udata['role']
            break

    if not user_id:
        return

    conversation = ChatConversation.query.get(conversation_id)
    if not conversation:
        return

    if user_role != 'superadmin' and conversation.user_id != user_id:
        return

    try:
        now = datetime.utcnow()

        if user_role == 'superadmin':
            # Admin lendo -> marca mensagens do user como lidas
            ChatMessage.query.filter_by(
                conversation_id=conversation_id,
                sender_role='user',
                read=False
            ).update({'read': True, 'read_at': now})
            conversation.admin_unread_count = 0
        else:
            # User lendo -> marca mensagens do admin como lidas
            ChatMessage.query.filter_by(
                conversation_id=conversation_id,
                sender_role='superadmin',
                read=False
            ).update({'read': True, 'read_at': now})
            conversation.user_unread_count = 0

        db.session.commit()

        # Emitir confirmacao de leitura
        emit('messages_read', {
            'conversation_id': conversation_id,
            'read_by': user_id,
            'read_by_role': 'superadmin' if user_role == 'superadmin' else 'user',
            'read_at': now.isoformat()
        }, room=f'conversation_{conversation_id}')

        # Atualizar admin_room
        emit('conversation_updated', conversation.to_dict(),
             room='admin_room', namespace='/chat')

    except Exception as e:
        db.session.rollback()
        emit('error', {'message': f'Erro ao marcar como lido: {str(e)}'})
