from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flasgger import swag_from
from datetime import datetime, timedelta
import secrets
from src.config.database import db
from src.models.professional_user import ProfessionalUser
from src.models.professional import Professional
from src.services.email_service import send_professional_invite_email, send_professional_reset_email

professional_auth_bp = Blueprint('professional_auth', __name__)


@professional_auth_bp.route('/invite', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Portal do Profissional - Auth'],
    'summary': 'Enviar convite para profissional',
    'description': 'Admin envia convite para profissional criar conta no portal',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['professional_id', 'email'],
                'properties': {
                    'professional_id': {'type': 'integer'},
                    'email': {'type': 'string', 'format': 'email'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Convite enviado com sucesso'},
        400: {'description': 'Dados invalidos ou conta ja existe'},
        404: {'description': 'Profissional nao encontrado'}
    }
})
def invite_professional():
    """Envia convite para profissional criar conta"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        professional_id = data.get('professional_id')
        email = data.get('email')

        if not professional_id or not email:
            return jsonify({'message': 'professional_id e email sao obrigatorios'}), 400

        # Verificar se profissional existe e pertence ao usuario
        professional = Professional.query.filter_by(
            id=professional_id,
            user_id=user_id
        ).first()

        if not professional:
            return jsonify({'message': 'Profissional nao encontrado'}), 404

        # Verificar se ja existe conta com este email
        existing_email = ProfessionalUser.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({'message': 'Ja existe uma conta com este email'}), 400

        # Verificar se profissional ja tem conta
        existing_professional = ProfessionalUser.query.filter_by(professional_id=professional_id).first()
        if existing_professional:
            return jsonify({'message': 'Profissional ja possui uma conta'}), 400

        # Criar usuario com token de convite
        invite_token = secrets.token_urlsafe(32)
        professional_user = ProfessionalUser(
            professional_id=professional_id,
            email=email,
            invite_token=invite_token,
            invite_expires_at=datetime.utcnow() + timedelta(hours=48)
        )

        db.session.add(professional_user)
        db.session.commit()

        # Enviar email com link de ativacao
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        activation_url = f"{frontend_url.rstrip('/')}/#/profissional/ativar/{invite_token}"

        email_sent, email_message = send_professional_invite_email(
            email=email,
            professional_name=professional.name,
            activation_url=activation_url
        )

        return jsonify({
            'message': 'Convite enviado com sucesso',
            'email_sent': email_sent,
            'invite_link': f'/profissional/ativar/{invite_token}'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao enviar convite: {str(e)}'}), 500


@professional_auth_bp.route('/activate', methods=['POST'])
@swag_from({
    'tags': ['Portal do Profissional - Auth'],
    'summary': 'Ativar conta do profissional',
    'description': 'Profissional ativa sua conta definindo senha',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['token', 'password'],
                'properties': {
                    'token': {'type': 'string'},
                    'password': {'type': 'string', 'minLength': 6}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Conta ativada com sucesso'},
        400: {'description': 'Token invalido, expirado ou senha muito curta'}
    }
})
def activate_account():
    """Profissional ativa sua conta definindo senha"""
    try:
        data = request.get_json()
        token = data.get('token')
        password = data.get('password')

        if not token or not password:
            return jsonify({'message': 'Token e senha sao obrigatorios'}), 400

        if len(password) < 6:
            return jsonify({'message': 'Senha deve ter pelo menos 6 caracteres'}), 400

        professional_user = ProfessionalUser.query.filter_by(invite_token=token).first()

        if not professional_user:
            return jsonify({'message': 'Token invalido'}), 400

        if professional_user.invite_expires_at < datetime.utcnow():
            return jsonify({'message': 'Token expirado. Solicite um novo convite.'}), 400

        if professional_user.is_active:
            return jsonify({'message': 'Conta ja foi ativada'}), 400

        # Ativar conta
        professional_user.set_password(password)
        professional_user.is_active = True
        professional_user.invite_token = None
        professional_user.invite_expires_at = None

        db.session.commit()

        return jsonify({'message': 'Conta ativada com sucesso! Voce ja pode fazer login.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao ativar conta: {str(e)}'}), 500


@professional_auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Portal do Profissional - Auth'],
    'summary': 'Login do profissional',
    'description': 'Autentica profissional e retorna token JWT',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['email', 'password'],
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                    'password': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Login bem sucedido'},
        401: {'description': 'Credenciais invalidas ou conta inativa'}
    }
})
def login():
    """Login do profissional"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Email e senha sao obrigatorios'}), 400

        professional_user = ProfessionalUser.query.filter_by(email=email).first()

        if not professional_user or not professional_user.check_password(password):
            return jsonify({'message': 'Email ou senha incorretos'}), 401

        if not professional_user.is_active:
            return jsonify({'message': 'Conta ainda nao foi ativada'}), 401

        # Atualizar ultimo login
        professional_user.last_login = datetime.utcnow()
        db.session.commit()

        # Criar token JWT com claims especiais para profissional
        access_token = create_access_token(
            identity=str(professional_user.id),
            additional_claims={
                'type': 'professional',
                'professional_id': professional_user.professional_id,
                'user_id': professional_user.professional.user_id  # ID da empresa
            }
        )

        return jsonify({
            'access_token': access_token,
            'token_type': 'Bearer',
            'professional': {
                'id': professional_user.professional.id,
                'name': professional_user.professional.name,
                'role': professional_user.professional.role,
                'color': professional_user.professional.color,
                'email': professional_user.email
            }
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao fazer login: {str(e)}'}), 500


@professional_auth_bp.route('/forgot-password', methods=['POST'])
@swag_from({
    'tags': ['Portal do Profissional - Auth'],
    'summary': 'Solicitar recuperacao de senha',
    'description': 'Envia email com link para redefinir senha',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['email'],
                'properties': {
                    'email': {'type': 'string', 'format': 'email'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Email enviado (se existir)'}
    }
})
def forgot_password():
    """Solicita reset de senha"""
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'message': 'Email e obrigatorio'}), 400

        professional_user = ProfessionalUser.query.filter_by(email=email).first()

        # Sempre retorna sucesso para nao revelar se email existe
        if professional_user and professional_user.is_active:
            reset_token = secrets.token_urlsafe(32)
            professional_user.reset_token = reset_token
            professional_user.reset_expires_at = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            # Enviar email de recuperacao
            frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
            reset_url = f"{frontend_url}/#/profissional/resetar-senha/{reset_token}"

            send_professional_reset_email(
                email=email,
                professional_name=professional_user.professional.name,
                reset_url=reset_url
            )

        return jsonify({'message': 'Se o email existir, um link de recuperacao sera enviado'}), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao processar solicitacao: {str(e)}'}), 500


@professional_auth_bp.route('/reset-password', methods=['POST'])
@swag_from({
    'tags': ['Portal do Profissional - Auth'],
    'summary': 'Redefinir senha',
    'description': 'Redefine senha usando token de recuperacao',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['token', 'password'],
                'properties': {
                    'token': {'type': 'string'},
                    'password': {'type': 'string', 'minLength': 6}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Senha alterada com sucesso'},
        400: {'description': 'Token invalido ou expirado'}
    }
})
def reset_password():
    """Reseta senha com token"""
    try:
        data = request.get_json()
        token = data.get('token')
        password = data.get('password')

        if not token or not password:
            return jsonify({'message': 'Token e senha sao obrigatorios'}), 400

        if len(password) < 6:
            return jsonify({'message': 'Senha deve ter pelo menos 6 caracteres'}), 400

        professional_user = ProfessionalUser.query.filter_by(reset_token=token).first()

        if not professional_user:
            return jsonify({'message': 'Token invalido'}), 400

        if professional_user.reset_expires_at < datetime.utcnow():
            return jsonify({'message': 'Token expirado. Solicite novo reset.'}), 400

        professional_user.set_password(password)
        professional_user.reset_token = None
        professional_user.reset_expires_at = None
        db.session.commit()

        return jsonify({'message': 'Senha alterada com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao alterar senha: {str(e)}'}), 500


@professional_auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Portal do Profissional - Auth'],
    'summary': 'Alterar senha',
    'description': 'Altera senha do profissional logado',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['current_password', 'new_password'],
                'properties': {
                    'current_password': {'type': 'string'},
                    'new_password': {'type': 'string', 'minLength': 6}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Senha alterada com sucesso'},
        400: {'description': 'Senha atual incorreta ou nova senha invalida'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def change_password():
    """Altera senha (usuario logado)"""
    try:
        claims = get_jwt()
        if claims.get('type') != 'professional':
            return jsonify({'message': 'Acesso restrito a profissionais'}), 403

        professional_user_id = int(get_jwt_identity())
        professional_user = ProfessionalUser.query.get(professional_user_id)

        if not professional_user:
            return jsonify({'message': 'Usuario nao encontrado'}), 404

        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({'message': 'Senhas sao obrigatorias'}), 400

        if len(new_password) < 6:
            return jsonify({'message': 'Nova senha deve ter pelo menos 6 caracteres'}), 400

        if not professional_user.check_password(current_password):
            return jsonify({'message': 'Senha atual incorreta'}), 400

        professional_user.set_password(new_password)
        db.session.commit()

        return jsonify({'message': 'Senha alterada com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao alterar senha: {str(e)}'}), 500


@professional_auth_bp.route('/me', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Portal do Profissional - Auth'],
    'summary': 'Obter dados do profissional logado',
    'responses': {
        200: {'description': 'Dados do profissional'},
        403: {'description': 'Acesso nao autorizado'}
    }
})
def get_me():
    """Retorna dados do profissional logado"""
    try:
        claims = get_jwt()
        if claims.get('type') != 'professional':
            return jsonify({'message': 'Acesso restrito a profissionais'}), 403

        professional_user_id = int(get_jwt_identity())
        professional_user = ProfessionalUser.query.get(professional_user_id)

        if not professional_user:
            return jsonify({'message': 'Usuario nao encontrado'}), 404

        return jsonify({
            'professional': {
                'id': professional_user.professional.id,
                'name': professional_user.professional.name,
                'role': professional_user.professional.role,
                'color': professional_user.professional.color,
                'phone': professional_user.professional.phone,
                'email': professional_user.email,
                'last_login': professional_user.last_login.isoformat() if professional_user.last_login else None
            }
        }), 200

    except Exception as e:
        return jsonify({'message': f'Erro ao obter dados: {str(e)}'}), 500


@professional_auth_bp.route('/validate-token/<token>', methods=['GET'])
@swag_from({
    'tags': ['Portal do Profissional - Auth'],
    'summary': 'Validar token de convite',
    'description': 'Verifica se token de convite e valido',
    'parameters': [
        {'name': 'token', 'in': 'path', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Token valido'},
        400: {'description': 'Token invalido ou expirado'}
    }
})
def validate_invite_token(token):
    """Valida token de convite"""
    try:
        professional_user = ProfessionalUser.query.filter_by(invite_token=token).first()

        if not professional_user:
            return jsonify({'valid': False, 'message': 'Token invalido'}), 400

        if professional_user.invite_expires_at < datetime.utcnow():
            return jsonify({'valid': False, 'message': 'Token expirado'}), 400

        if professional_user.is_active:
            return jsonify({'valid': False, 'message': 'Conta ja foi ativada'}), 400

        return jsonify({
            'valid': True,
            'professional_name': professional_user.professional.name,
            'email': professional_user.email
        }), 200

    except Exception as e:
        return jsonify({'valid': False, 'message': f'Erro: {str(e)}'}), 500
