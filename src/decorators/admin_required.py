"""
Decorator para verificar se o usuário é um administrador do sistema.
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User


def admin_required(fn):
    """
    Decorator que verifica se o usuário autenticado tem role 'admin' ou 'superadmin'.
    Deve ser usado após @jwt_required().

    Exemplo de uso:
        @route.route('/admin-only')
        @jwt_required()
        @admin_required
        def admin_endpoint():
            pass
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'error': 'Usuário não encontrado',
                'code': 'USER_NOT_FOUND'
            }), 404

        if user.role not in ['admin', 'superadmin']:
            return jsonify({
                'error': 'Acesso negado. Permissão de administrador necessária.',
                'code': 'ADMIN_REQUIRED'
            }), 403

        return fn(*args, **kwargs)

    return wrapper
