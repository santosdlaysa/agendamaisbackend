"""
Rotas de Notificacoes In-App para o sistema AgendaMais
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from src.config.database import db
from src.models.notification import Notification

notifications_bp = Blueprint('notifications', __name__)


def get_current_user_id():
    """Obtem o ID do usuario logado"""
    return int(get_jwt_identity())


@notifications_bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Notificacoes'],
    'summary': 'Listar notificacoes',
    'description': 'Retorna lista paginada de notificacoes do usuario',
    'parameters': [
        {'name': 'page', 'in': 'query', 'type': 'integer', 'default': 1},
        {'name': 'per_page', 'in': 'query', 'type': 'integer', 'default': 20},
        {'name': 'unread_only', 'in': 'query', 'type': 'boolean', 'default': False}
    ],
    'responses': {
        200: {'description': 'Lista de notificacoes'}
    }
})
def get_notifications():
    """Listar notificacoes do usuario"""
    try:
        user_id = get_current_user_id()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'

        notifications = Notification.get_notifications(
            user_id=user_id,
            page=page,
            per_page=per_page,
            unread_only=unread_only
        )

        return jsonify({
            'notifications': [n.to_dict() for n in notifications.items],
            'pagination': {
                'page': notifications.page,
                'pages': notifications.pages,
                'per_page': notifications.per_page,
                'total': notifications.total
            },
            'unread_count': Notification.get_unread_count(user_id)
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao listar notificacoes: {str(e)}'}), 500


@notifications_bp.route('/count', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Notificacoes'],
    'summary': 'Contar notificacoes nao lidas',
    'description': 'Retorna contagem de notificacoes nao lidas',
    'responses': {
        200: {'description': 'Contagem de notificacoes'}
    }
})
def get_unread_count():
    """Retorna contagem de notificacoes nao lidas"""
    try:
        user_id = get_current_user_id()
        count = Notification.get_unread_count(user_id)

        return jsonify({
            'unread_count': count
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao contar notificacoes: {str(e)}'}), 500


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Notificacoes'],
    'summary': 'Marcar notificacao como lida',
    'parameters': [
        {'name': 'notification_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Notificacao marcada como lida'},
        404: {'description': 'Notificacao nao encontrada'}
    }
})
def mark_as_read(notification_id):
    """Marca uma notificacao como lida"""
    try:
        user_id = get_current_user_id()

        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return jsonify({'message': 'Notificacao nao encontrada'}), 404

        notification.mark_as_read()
        db.session.commit()

        return jsonify({
            'message': 'Notificacao marcada como lida',
            'notification': notification.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao marcar notificacao: {str(e)}'}), 500


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Notificacoes'],
    'summary': 'Marcar todas como lidas',
    'description': 'Marca todas as notificacoes do usuario como lidas',
    'responses': {
        200: {'description': 'Todas notificacoes marcadas como lidas'}
    }
})
def mark_all_as_read():
    """Marca todas as notificacoes como lidas"""
    try:
        user_id = get_current_user_id()

        Notification.mark_all_as_read(user_id)

        return jsonify({
            'message': 'Todas as notificacoes foram marcadas como lidas',
            'unread_count': 0
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao marcar notificacoes: {str(e)}'}), 500


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
@swag_from({
    'tags': ['Notificacoes'],
    'summary': 'Excluir notificacao',
    'parameters': [
        {'name': 'notification_id', 'in': 'path', 'type': 'integer', 'required': True}
    ],
    'responses': {
        200: {'description': 'Notificacao excluida'},
        404: {'description': 'Notificacao nao encontrada'}
    }
})
def delete_notification(notification_id):
    """Exclui uma notificacao"""
    try:
        user_id = get_current_user_id()

        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return jsonify({'message': 'Notificacao nao encontrada'}), 404

        db.session.delete(notification)
        db.session.commit()

        return jsonify({
            'message': 'Notificacao excluida com sucesso'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao excluir notificacao: {str(e)}'}), 500


@notifications_bp.route('/clear', methods=['DELETE'])
@jwt_required()
@swag_from({
    'tags': ['Notificacoes'],
    'summary': 'Limpar notificacoes',
    'description': 'Remove todas as notificacoes lidas do usuario',
    'responses': {
        200: {'description': 'Notificacoes limpas'}
    }
})
def clear_read_notifications():
    """Remove todas as notificacoes lidas"""
    try:
        user_id = get_current_user_id()

        deleted = Notification.query.filter_by(
            user_id=user_id,
            read=True
        ).delete()

        db.session.commit()

        return jsonify({
            'message': f'{deleted} notificacoes removidas',
            'deleted_count': deleted
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao limpar notificacoes: {str(e)}'}), 500
