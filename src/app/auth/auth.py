import re

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flasgger import swag_from
from src.models.user import db, User
from src.services.email_service import send_verification_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Registrar novo usuário',
    'description': 'Cria um novo usuário no sistema',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['email', 'password', 'name'],
                'properties': {
                    'email': {'type': 'string', 'example': 'usuario@email.com'},
                    'password': {'type': 'string', 'example': 'senha123'},
                    'name': {'type': 'string', 'example': 'João Silva'},
                    'role': {'type': 'string', 'example': 'user', 'default': 'user'}
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Usuário criado com sucesso',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'user': {'$ref': '#/definitions/User'}
                }
            }
        },
        400: {'description': 'Dados inválidos ou email já em uso'}
    }
})
def register():
    """Registrar novo usuário"""
    try:
        data = request.get_json()

        # Validar dados obrigatórios
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()

        if not email or not password or not name:
            return jsonify(message='Email, senha e nome são obrigatórios'), 400

        # Validar formato do email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify(message='Formato de email inválido'), 400

        # Validar tamanho da senha
        if len(password) < 6:
            return jsonify(message='A senha deve ter no mínimo 6 caracteres'), 400

        # Verificar se usuário já existe
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify(message='Email já está em uso'), 400

        # Criar novo usuário (role sempre 'user' - admins devem ser promovidos manualmente)
        user = User(
            email=email,
            name=name,
            role='user'
        )
        user.set_password(password)

        # Gerar token de verificação de email
        token = user.generate_email_verification_token()

        db.session.add(user)
        db.session.commit()

        # Enviar email de verificação
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/verificar-email?token={token}"

        email_sent, email_msg = send_verification_email(user, verification_url)

        return jsonify(
            message='Usuário criado com sucesso. Verifique seu email para confirmar o cadastro.',
            user=user.to_dict(),
            email_sent=email_sent,
            email_message=email_msg if not email_sent else None
        ), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao criar usuário: {str(e)}'), 500

@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Login do usuário',
    'description': 'Autentica o usuário e retorna um token JWT',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['email', 'password'],
                'properties': {
                    'email': {'type': 'string', 'example': 'usuario@email.com'},
                    'password': {'type': 'string', 'example': 'senha123'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Login realizado com sucesso',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'access_token': {'type': 'string'},
                    'user': {'$ref': '#/definitions/User'}
                }
            }
        },
        400: {'description': 'Email e senha são obrigatórios'},
        401: {'description': 'Email ou senha inválidos'}
    }
})
def login():
    """Login do usuário"""
    try:
        data = request.get_json()

        # Validar dados obrigatórios
        if not data.get('email') or not data.get('password'):
            return jsonify(message='Email e senha são obrigatórios'), 400

        # Buscar usuário
        user = User.query.filter_by(email=data['email']).first()

        # DEBUG
        print(f"DEBUG - Email recebido: '{data['email']}'")
        print(f"DEBUG - Usuário encontrado: {user is not None}")
        if user:
            print(f"DEBUG - Email no banco: '{user.email}'")
            print(f"DEBUG - Password hash: {user.password_hash}")
            senha_valida = user.check_password(data['password'])
            print(f"DEBUG - Senha válida: {senha_valida}")

        # Verificar usuário e senha
        if not user or not user.check_password(data['password']):
            return jsonify(message='Email ou senha inválidos'), 401
        
        # Criar token de acesso (identity deve ser string)
        access_token = create_access_token(identity=str(user.id))

        # Preparar resposta
        response_data = {
            'message': 'Login realizado com sucesso',
            'access_token': access_token,
            'user': user.to_dict()
        }

        # Adicionar aviso se email não verificado
        if not user.email_verified:
            response_data['warning'] = 'Seu email ainda não foi verificado. Verifique sua caixa de entrada.'
            response_data['email_verified'] = False
        else:
            response_data['email_verified'] = True

        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify(message=f'Erro ao fazer login: {str(e)}'), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Obter dados do usuário atual',
    'description': 'Retorna os dados do usuário autenticado',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Dados do usuário',
            'schema': {
                'type': 'object',
                'properties': {
                    'user': {'$ref': '#/definitions/User'}
                }
            }
        },
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Usuário não encontrado'}
    }
})
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
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Alterar senha do usuário',
    'description': 'Altera a senha do usuário autenticado',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['current_password', 'new_password'],
                'properties': {
                    'current_password': {'type': 'string', 'example': 'senhaAtual123'},
                    'new_password': {'type': 'string', 'example': 'novaSenha456'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Senha alterada com sucesso'},
        400: {'description': 'Dados inválidos ou senha atual incorreta'},
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Usuário não encontrado'}
    }
})
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


@auth_bp.route('/verify-email/<token>', methods=['GET'])
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Verificar email',
    'description': 'Verifica o email do usuário usando o token enviado por email',
    'parameters': [
        {
            'name': 'token',
            'in': 'path',
            'required': True,
            'type': 'string',
            'description': 'Token de verificação de email'
        }
    ],
    'responses': {
        200: {'description': 'Email verificado com sucesso'},
        400: {'description': 'Token inválido ou expirado'},
        404: {'description': 'Token não encontrado'}
    }
})
def verify_email(token):
    """Verificar email do usuário"""
    try:
        user = User.find_by_verification_token(token)

        if not user:
            return jsonify(message='Token de verificação não encontrado'), 404

        success, message = user.verify_email(token)

        if success:
            db.session.commit()
            return jsonify(message=message), 200
        else:
            return jsonify(message=message), 400

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao verificar email: {str(e)}'), 500


@auth_bp.route('/resend-verification', methods=['POST'])
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Reenviar email de verificação',
    'description': 'Reenvia o email de verificação para o usuário',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['email'],
                'properties': {
                    'email': {'type': 'string', 'example': 'usuario@email.com'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Email de verificação reenviado'},
        400: {'description': 'Email já verificado'},
        404: {'description': 'Usuário não encontrado'}
    }
})
def resend_verification():
    """Reenviar email de verificação"""
    try:
        data = request.get_json()

        if not data.get('email'):
            return jsonify(message='Email é obrigatório'), 400

        user = User.query.filter_by(email=data['email']).first()

        if not user:
            return jsonify(message='Usuário não encontrado'), 404

        if user.email_verified:
            return jsonify(message='Este email já foi verificado'), 400

        # Gerar novo token
        token = user.generate_email_verification_token()
        db.session.commit()

        # Enviar email
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/verificar-email?token={token}"

        email_sent, email_msg = send_verification_email(user, verification_url)

        if email_sent:
            return jsonify(message='Email de verificação reenviado com sucesso'), 200
        else:
            return jsonify(message=f'Erro ao enviar email: {email_msg}'), 500

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao reenviar verificação: {str(e)}'), 500


@auth_bp.route('/business', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Obter dados da empresa',
    'description': 'Retorna os dados do estabelecimento do usuário autenticado',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Dados da empresa',
            'schema': {
                'type': 'object',
                'properties': {
                    'slug': {'type': 'string'},
                    'business_name': {'type': 'string'},
                    'business_phone': {'type': 'string'},
                    'business_address': {'type': 'string'},
                    'business_logo': {'type': 'string'},
                    'online_booking_enabled': {'type': 'boolean'}
                }
            }
        },
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Usuário não encontrado'}
    }
})
def get_business():
    """Obter dados da empresa"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify(message='Usuário não encontrado'), 404

        return jsonify({
            'slug': user.slug,
            'business_name': user.business_name,
            'business_phone': user.business_phone,
            'business_address': user.business_address,
            'business_logo': user.business_logo,
            'online_booking_enabled': user.online_booking_enabled
        }), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter dados da empresa: {str(e)}'), 500


@auth_bp.route('/business', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Atualizar dados da empresa',
    'description': 'Atualiza os dados do estabelecimento para agendamento online',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'slug': {'type': 'string', 'example': 'minha-barbearia'},
                    'business_name': {'type': 'string', 'example': 'Minha Barbearia'},
                    'business_phone': {'type': 'string', 'example': '(11) 99999-9999'},
                    'business_address': {'type': 'string', 'example': 'Rua das Flores, 123'},
                    'business_logo': {'type': 'string', 'example': 'https://...'},
                    'online_booking_enabled': {'type': 'boolean', 'example': True}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Dados atualizados com sucesso'},
        400: {'description': 'Slug já está em uso'},
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Usuário não encontrado'}
    }
})
def update_business():
    """Atualizar dados da empresa"""
    try:
        data = request.get_json()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify(message='Usuário não encontrado'), 404

        # Verificar se slug já está em uso por outro usuário
        if data.get('slug'):
            slug = data['slug'].lower().strip()
            # Remover caracteres especiais e espaços
            slug = ''.join(c if c.isalnum() or c == '-' else '-' for c in slug)
            slug = '-'.join(filter(None, slug.split('-')))  # Remove hífens duplicados

            existing = User.query.filter(User.slug == slug, User.id != user_id).first()
            if existing:
                return jsonify(message='Este slug já está em uso'), 400
            user.slug = slug

        if 'business_name' in data:
            user.business_name = data['business_name']

        if 'business_phone' in data:
            user.business_phone = data['business_phone']

        if 'business_address' in data:
            user.business_address = data['business_address']

        if 'business_logo' in data:
            user.business_logo = data['business_logo']

        if 'online_booking_enabled' in data:
            user.online_booking_enabled = data['online_booking_enabled']

        db.session.commit()

        return jsonify({
            'message': 'Dados da empresa atualizados com sucesso',
            'business': {
                'slug': user.slug,
                'business_name': user.business_name,
                'business_phone': user.business_phone,
                'business_address': user.business_address,
                'business_logo': user.business_logo,
                'online_booking_enabled': user.online_booking_enabled
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar dados da empresa: {str(e)}'), 500


@auth_bp.route('/settings/payment', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Obter configurações de pagamento',
    'description': 'Retorna as configurações de pagamento do estabelecimento para agendamento online',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Configurações de pagamento',
            'schema': {
                'type': 'object',
                'properties': {
                    'require_payment': {'type': 'boolean'},
                    'payment_type': {'type': 'string', 'enum': ['full', 'deposit']},
                    'deposit_percentage': {'type': 'integer'}
                }
            }
        },
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Usuário não encontrado'}
    }
})
def get_payment_settings():
    """Obter configurações de pagamento"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify(message='Usuário não encontrado'), 404

        return jsonify({
            'require_payment': user.booking_require_payment or False,
            'payment_type': user.booking_payment_type or 'full',
            'deposit_percentage': user.booking_deposit_percentage or 50
        }), 200

    except Exception as e:
        return jsonify(message=f'Erro ao obter configurações de pagamento: {str(e)}'), 500


@auth_bp.route('/settings/payment', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Atualizar configurações de pagamento',
    'description': 'Atualiza as configurações de pagamento para agendamento online',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'require_payment': {'type': 'boolean', 'example': True, 'description': 'Exigir pagamento para agendar'},
                    'payment_type': {'type': 'string', 'enum': ['full', 'deposit'], 'example': 'deposit', 'description': 'Tipo de pagamento: total ou depósito'},
                    'deposit_percentage': {'type': 'integer', 'example': 50, 'description': 'Porcentagem do depósito (se payment_type for deposit)'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Configurações atualizadas com sucesso'},
        400: {'description': 'Dados inválidos'},
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Usuário não encontrado'}
    }
})
def update_payment_settings():
    """Atualizar configurações de pagamento"""
    try:
        data = request.get_json()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify(message='Usuário não encontrado'), 404

        # Atualizar require_payment
        if 'require_payment' in data:
            user.booking_require_payment = bool(data['require_payment'])

        # Atualizar payment_type
        if 'payment_type' in data:
            payment_type = data['payment_type']
            if payment_type not in ['full', 'deposit']:
                return jsonify(message='payment_type deve ser "full" ou "deposit"'), 400
            user.booking_payment_type = payment_type

        # Atualizar deposit_percentage
        if 'deposit_percentage' in data:
            deposit_pct = data['deposit_percentage']
            if not isinstance(deposit_pct, int) or deposit_pct < 1 or deposit_pct > 100:
                return jsonify(message='deposit_percentage deve ser um inteiro entre 1 e 100'), 400
            user.booking_deposit_percentage = deposit_pct

        db.session.commit()

        return jsonify({
            'message': 'Configurações de pagamento atualizadas com sucesso',
            'payment_settings': {
                'require_payment': user.booking_require_payment,
                'payment_type': user.booking_payment_type,
                'deposit_percentage': user.booking_deposit_percentage
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao atualizar configurações de pagamento: {str(e)}'), 500


@auth_bp.route('/onboarding/status', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Onboarding'],
    'summary': 'Verificar status do onboarding',
    'description': 'Retorna o status do onboarding do usuário',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Status do onboarding',
            'schema': {
                'type': 'object',
                'properties': {
                    'onboarding_completed': {'type': 'boolean'},
                    'onboarding_completed_at': {'type': 'string', 'format': 'date-time'},
                    'missing_fields': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        },
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Usuário não encontrado'}
    }
})
def get_onboarding_status():
    """Verificar status do onboarding"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify(message='Usuário não encontrado'), 404

        # Verificar campos obrigatórios faltando
        missing_fields = []
        if not user.business_name or user.business_name.strip() == '':
            missing_fields.append('business_name')
        if not user.slug or user.slug.strip() == '':
            missing_fields.append('slug')

        return jsonify({
            'onboarding_completed': user.onboarding_completed or False,
            'onboarding_completed_at': user.onboarding_completed_at.isoformat() if user.onboarding_completed_at else None,
            'missing_fields': missing_fields
        }), 200

    except Exception as e:
        return jsonify(message=f'Erro ao verificar status do onboarding: {str(e)}'), 500


@auth_bp.route('/onboarding/complete', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Onboarding'],
    'summary': 'Completar onboarding',
    'description': 'Marca o onboarding como completo após validar campos obrigatórios (business_name e slug)',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['business_name', 'slug'],
                'properties': {
                    'business_name': {'type': 'string', 'example': 'Minha Barbearia'},
                    'slug': {'type': 'string', 'example': 'minha-barbearia'},
                    'business_phone': {'type': 'string', 'example': '(11) 99999-9999'},
                    'business_address': {'type': 'string', 'example': 'Rua das Flores, 123'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Onboarding completo',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'onboarding_completed': {'type': 'boolean'},
                    'user': {'$ref': '#/definitions/User'}
                }
            }
        },
        400: {'description': 'Campos obrigatórios não preenchidos ou slug já em uso'},
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Usuário não encontrado'}
    }
})
def complete_onboarding():
    """Completar onboarding"""
    try:
        from datetime import datetime

        data = request.get_json()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)

        if not user:
            return jsonify(message='Usuário não encontrado'), 404

        # Validar campos obrigatórios
        business_name = data.get('business_name', '').strip() if data.get('business_name') else ''
        slug = data.get('slug', '').strip() if data.get('slug') else ''

        if not business_name:
            return jsonify(message='Nome da empresa é obrigatório'), 400

        if not slug:
            return jsonify(message='Slug (URL) é obrigatório'), 400

        # Validar e formatar slug
        slug = slug.lower()
        slug = ''.join(c if c.isalnum() or c == '-' else '-' for c in slug)
        slug = '-'.join(filter(None, slug.split('-')))

        if len(slug) < 3:
            return jsonify(message='Slug deve ter no mínimo 3 caracteres'), 400

        # Verificar se slug já está em uso
        existing = User.query.filter(User.slug == slug, User.id != user_id).first()
        if existing:
            return jsonify(message='Este slug já está em uso'), 400

        # Atualizar dados do usuário
        user.business_name = business_name
        user.slug = slug

        # Atualizar campos opcionais se fornecidos
        if data.get('business_phone'):
            user.business_phone = data['business_phone']

        if data.get('business_address'):
            user.business_address = data['business_address']

        # Marcar onboarding como completo
        user.onboarding_completed = True
        user.onboarding_completed_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': 'Onboarding concluído com sucesso',
            'onboarding_completed': True,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(message=f'Erro ao completar onboarding: {str(e)}'), 500
