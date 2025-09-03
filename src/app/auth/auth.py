from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registrar novo usuário"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify(message='Email, senha e nome são obrigatórios'), 400
        
        # Verificar se usuário já existe
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify(message='Email já está em uso'), 400
        
        # Criar novo usuário
        user = User(
            email=data['email'],
            name=data['name'],
            role=data.get('role', 'admin')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify(
            message='Usuário criado com sucesso',
            user=user.to_dict()
        ), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao criar usuário: {str(e)}'), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login do usuário"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get('email') or not data.get('password'):
            return jsonify(message='Email e senha são obrigatórios'), 400
        
        # Buscar usuário
        user = User.query.filter_by(email=data['email']).first()
        
        # Verificar usuário e senha
        if not user or not user.check_password(data['password']):
            return jsonify(message='Email ou senha inválidos'), 401
        
        # Criar token de acesso
        access_token = create_access_token(identity=user.id)
        
        return jsonify(
            message='Login realizado com sucesso',
            access_token=access_token,
            user=user.to_dict()
        ), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao fazer login: {str(e)}'), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obter dados do usuário atual"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify(message='Usuário não encontrado'), 404
        
        return jsonify(user=user.to_dict()), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao obter usuário: {str(e)}'), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Alterar senha do usuário"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validar dados obrigatórios
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify(message='Senha atual e nova senha são obrigatórias'), 400
        
        # Buscar usuário
        user = User.query.get(user_id)
        if not user:
            return jsonify(message='Usuário não encontrado'), 404
        
        # Verificar senha atual
        if not user.check_password(data['current_password']):
            return jsonify(message='Senha atual incorreta'), 400
        
        # Definir nova senha
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify(message='Senha alterada com sucesso'), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao alterar senha: {str(e)}'), 500

