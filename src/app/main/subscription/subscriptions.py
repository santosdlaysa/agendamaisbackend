import stripe
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify

# Carregar .env do diretório raiz do projeto
env_path = Path(__file__).resolve().parents[4] / '.env'
load_dotenv(env_path)
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from datetime import datetime, timedelta
from src.config.database import db
from src.models.subscription import Subscription
from src.models.user import User

# Configurar Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

subscriptions_bp = Blueprint('subscriptions', __name__)

# Mapeamento de planos com IDs do Stripe
# IMPORTANTE: Substitua os price_id pelos IDs reais criados no Stripe Dashboard
PLANS = {
    'basic': {
        'price_id': os.getenv('STRIPE_PRICE_BASIC', 'price_basic_placeholder'),
        'name': 'Básico',
        'price': 29,
        'features': [
            'Até 100 agendamentos/mês',
            'Até 3 profissionais',
            'Lembretes básicos',
            'Suporte por email'
        ]
    },
    'pro': {
        'price_id': os.getenv('STRIPE_PRICE_PRO', 'price_pro_placeholder'),
        'name': 'Pro',
        'price': 59,
        'features': [
            'Agendamentos ilimitados',
            'Até 10 profissionais',
            'Lembretes WhatsApp/SMS',
            'Relatórios avançados',
            'Suporte prioritário'
        ]
    },
    'enterprise': {
        'price_id': os.getenv('STRIPE_PRICE_ENTERPRISE', 'price_enterprise_placeholder'),
        'name': 'Enterprise',
        'price': 99,
        'features': [
            'Tudo do Pro',
            'Profissionais ilimitados',
            'API personalizada',
            'Gestor de conta dedicado',
            'Suporte 24/7'
        ]
    }
}


@subscriptions_bp.route('/plans', methods=['GET'])
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Listar planos disponíveis',
    'description': 'Retorna todos os planos de assinatura disponíveis',
    'responses': {
        200: {
            'description': 'Lista de planos',
            'schema': {
                'type': 'object',
                'properties': {
                    'plans': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'string', 'example': 'basic'},
                                'name': {'type': 'string', 'example': 'Básico'},
                                'price': {'type': 'number', 'example': 29},
                                'features': {'type': 'array', 'items': {'type': 'string'}}
                            }
                        }
                    }
                }
            }
        }
    }
})
def get_plans():
    """Retorna os planos disponíveis"""
    return jsonify({
        'plans': [
            {
                'id': plan_id,
                'name': plan_data['name'],
                'price': plan_data['price'],
                'features': plan_data['features']
            }
            for plan_id, plan_data in PLANS.items()
        ]
    }), 200


@subscriptions_bp.route('/subscribe', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Criar checkout para assinatura',
    'description': 'Cria uma sessão de checkout do Stripe. O usuário deve cadastrar o cartão antes de iniciar o trial de 7 dias. Após o trial, a cobrança é automática.',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['plan'],
                'properties': {
                    'plan': {'type': 'string', 'enum': ['basic', 'pro', 'enterprise'], 'example': 'basic'},
                    'success_url': {'type': 'string', 'example': 'https://seusite.com/sucesso'},
                    'cancel_url': {'type': 'string', 'example': 'https://seusite.com/cancelado'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Checkout criado - redirecionar usuário para checkout_url',
            'schema': {
                'type': 'object',
                'properties': {
                    'checkout_url': {'type': 'string', 'description': 'URL para redirecionar o usuário'},
                    'session_id': {'type': 'string', 'description': 'ID da sessão do Stripe'}
                }
            }
        },
        400: {'description': 'Plano inválido ou já possui assinatura ativa'},
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Usuário não encontrado'}
    }
})
def create_subscription():
    """Criar nova assinatura via Stripe Checkout"""
    try:
        data = request.json
        user_id = int(get_jwt_identity())
        plan = data.get('plan') if data else None
        success_url = data.get('success_url', 'http://localhost:3000/subscription/success')
        cancel_url = data.get('cancel_url', 'http://localhost:3000/subscription/cancel')

        # Buscar usuário
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        # Admins não precisam de assinatura
        if user.role == 'admin':
            return jsonify({'error': 'Administradores não precisam de assinatura'}), 400

        # Validar plano
        if not plan or plan not in PLANS:
            return jsonify({'error': f'Plano inválido. Recebido: {plan}. Válidos: {list(PLANS.keys())}'}), 400

        # Verificar se já tem assinatura ativa
        existing = Subscription.query.filter_by(user_id=user_id).first()
        if existing and existing.status in ['active', 'trialing']:
            return jsonify({'error': 'Já existe uma assinatura ativa'}), 400

        # Criar ou recuperar customer no Stripe
        stripe_customer_id = None
        if existing and existing.stripe_customer_id:
            stripe_customer_id = existing.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={'user_id': str(user_id)}
            )
            stripe_customer_id = customer.id

        # Criar Checkout Session - coleta cartão antes do trial
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': PLANS[plan]['price_id'],
                'quantity': 1
            }],
            subscription_data={
                'trial_period_days': 7,
                'metadata': {
                    'user_id': str(user_id),
                    'plan': plan
                }
            },
            success_url=success_url if '{CHECKOUT_SESSION_ID}' in success_url else success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user_id),
                'plan': plan
            }
        )

        # Salvar registro pendente no banco
        if existing:
            existing.plan = plan
            existing.stripe_customer_id = stripe_customer_id
            existing.status = 'pending'
            existing.cancel_at_period_end = False
            existing.end_date = None
            subscription = existing
        else:
            subscription = Subscription(
                user_id=user_id,
                plan=plan,
                stripe_customer_id=stripe_customer_id,
                status='pending'
            )
            db.session.add(subscription)

        db.session.commit()

        return jsonify({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        }), 200

    except stripe.StripeError as e:
        db.session.rollback()
        return jsonify({'error': f'Erro no Stripe: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar assinatura: {str(e)}'}), 500


@subscriptions_bp.route('/status', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Obter status da assinatura',
    'description': 'Retorna o status atual da assinatura do cliente autenticado',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Status da assinatura',
            'schema': {
                'type': 'object',
                'properties': {
                    'has_subscription': {'type': 'boolean'},
                    'subscription': {'$ref': '#/definitions/Subscription'}
                }
            }
        },
        401: {'description': 'Token não fornecido ou inválido'}
    }
})
def get_subscription_status():
    """Obter status da assinatura do usuário"""
    try:
        user_id = int(get_jwt_identity())

        # Verificar se é admin - admins não precisam de assinatura
        user = User.query.get(user_id)
        if user and user.role == 'admin':
            return jsonify({
                'has_subscription': True,
                'is_admin': True,
                'subscription': {
                    'plan': 'admin',
                    'status': 'active',
                    'is_admin_access': True,
                    'message': 'Acesso administrativo - sem necessidade de assinatura'
                }
            }), 200

        subscription = Subscription.query.filter_by(user_id=user_id).first()

        if not subscription:
            return jsonify({'has_subscription': False}), 200

        has_payment_method = False

        # Tentar sincronizar com Stripe
        if subscription.stripe_subscription_id:
            try:
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                subscription.status = stripe_sub.status
                subscription.cancel_at_period_end = stripe_sub.cancel_at_period_end
                db.session.commit()
            except stripe.StripeError as e:
                print(f"Erro ao sincronizar com Stripe: {e}")

        # Verificar se tem método de pagamento cadastrado
        if subscription.stripe_customer_id:
            try:
                payment_methods = stripe.PaymentMethod.list(
                    customer=subscription.stripe_customer_id,
                    type='card'
                )
                has_payment_method = len(payment_methods.data) > 0
            except stripe.StripeError as e:
                print(f"Erro ao verificar payment methods: {e}")

        subscription_data = subscription.to_dict()
        subscription_data['has_payment_method'] = has_payment_method

        return jsonify({
            'has_subscription': True,
            'subscription': subscription_data
        }), 200

    except Exception as e:
        return jsonify({'error': f'Erro ao buscar assinatura: {str(e)}'}), 500


@subscriptions_bp.route('/change-plan', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Alterar plano',
    'description': 'Altera o plano da assinatura atual. A mudança é aplicada imediatamente com proration.',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['plan'],
                'properties': {
                    'plan': {'type': 'string', 'enum': ['basic', 'pro', 'enterprise'], 'example': 'pro'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Plano alterado com sucesso'},
        400: {'description': 'Plano inválido ou igual ao atual'},
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Assinatura não encontrada'}
    }
})
def change_plan():
    """Alterar plano da assinatura"""
    try:
        user_id = int(get_jwt_identity())
        data = request.json
        new_plan = data.get('plan') if data else None

        # Validar plano
        if not new_plan or new_plan not in PLANS:
            return jsonify({'error': f'Plano inválido. Válidos: {list(PLANS.keys())}'}), 400

        # Buscar assinatura
        subscription = Subscription.query.filter_by(user_id=user_id).first()

        if not subscription:
            return jsonify({'error': 'Assinatura não encontrada'}), 404

        if subscription.status not in ['active', 'trialing']:
            return jsonify({'error': 'Assinatura não está ativa'}), 400

        if subscription.plan == new_plan:
            return jsonify({'error': 'Você já está neste plano'}), 400

        # Buscar assinatura no Stripe
        stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)

        # Atualizar para o novo plano (com proration)
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            items=[{
                'id': stripe_sub['items']['data'][0]['id'],
                'price': PLANS[new_plan]['price_id']
            }],
            proration_behavior='create_prorations'
        )

        # Atualizar no banco
        old_plan = subscription.plan
        subscription.plan = new_plan
        db.session.commit()

        return jsonify({
            'message': f'Plano alterado de {old_plan} para {new_plan}',
            'subscription': subscription.to_dict()
        }), 200

    except stripe.StripeError as e:
        return jsonify({'error': f'Erro no Stripe: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Erro ao alterar plano: {str(e)}'}), 500


@subscriptions_bp.route('/cancel', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Cancelar assinatura',
    'description': 'Cancela a assinatura ao fim do período atual',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Assinatura será cancelada ao fim do período'},
        400: {'description': 'Assinatura não está ativa'},
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Assinatura não encontrada'}
    }
})
def cancel_subscription():
    """Cancelar assinatura ao fim do período"""
    try:
        user_id = int(get_jwt_identity())

        subscription = Subscription.query.filter_by(user_id=user_id).first()

        if not subscription:
            return jsonify({'error': 'Assinatura não encontrada'}), 404

        if subscription.status not in ['active', 'trialing']:
            return jsonify({'error': 'Assinatura não está ativa'}), 400

        # Cancelar no Stripe ao fim do período
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )

        subscription.cancel_at_period_end = True
        db.session.commit()

        return jsonify({
            'message': 'Assinatura será cancelada ao fim do período',
            'subscription': subscription.to_dict()
        }), 200

    except stripe.StripeError as e:
        return jsonify({'error': f'Erro no Stripe: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Erro ao cancelar assinatura: {str(e)}'}), 500


@subscriptions_bp.route('/reactivate', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Reativar assinatura',
    'description': 'Reativa uma assinatura que foi marcada para cancelamento',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Assinatura reativada com sucesso'},
        400: {'description': 'Assinatura não está marcada para cancelamento'},
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Assinatura não encontrada'}
    }
})
def reactivate_subscription():
    """Reativar assinatura cancelada"""
    try:
        user_id = int(get_jwt_identity())

        subscription = Subscription.query.filter_by(user_id=user_id).first()

        if not subscription:
            return jsonify({'error': 'Assinatura não encontrada'}), 404

        if not subscription.cancel_at_period_end:
            return jsonify({'error': 'Assinatura não está marcada para cancelamento'}), 400

        # Remover flag de cancelamento no Stripe
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=False
        )

        subscription.cancel_at_period_end = False
        db.session.commit()

        return jsonify({
            'message': 'Assinatura reativada com sucesso',
            'subscription': subscription.to_dict()
        }), 200

    except stripe.StripeError as e:
        return jsonify({'error': f'Erro no Stripe: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Erro ao reativar assinatura: {str(e)}'}), 500


@subscriptions_bp.route('/billing-portal', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Acessar portal de billing',
    'description': 'Cria uma sessão do Stripe Billing Portal onde o usuário pode gerenciar seu cartão, ver faturas e cancelar assinatura',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['return_url'],
                'properties': {
                    'return_url': {'type': 'string', 'example': 'https://seusite.com/conta'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'URL do portal de billing',
            'schema': {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string', 'description': 'URL para redirecionar o usuário ao portal'}
                }
            }
        },
        400: {'description': 'return_url não fornecida'},
        401: {'description': 'Token não fornecido ou inválido'},
        404: {'description': 'Assinatura não encontrada'}
    }
})
def create_billing_portal():
    """Criar sessão do Stripe Billing Portal"""
    try:
        user_id = int(get_jwt_identity())
        data = request.json
        return_url = data.get('return_url') if data else None

        if not return_url:
            return jsonify({'error': 'return_url é obrigatória'}), 400

        # Buscar assinatura do usuário
        subscription = Subscription.query.filter_by(user_id=user_id).first()

        if not subscription or not subscription.stripe_customer_id:
            return jsonify({'error': 'Assinatura não encontrada'}), 404

        # Criar sessão do Billing Portal
        portal_session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=return_url
        )

        return jsonify({'url': portal_session.url}), 200

    except stripe.StripeError as e:
        return jsonify({'error': f'Erro no Stripe: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Erro ao criar portal: {str(e)}'}), 500


@subscriptions_bp.route('/verify-checkout', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Verificar checkout completado',
    'description': 'Verifica se o checkout foi completado e atualiza a assinatura. Usar após retorno do Stripe.',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['session_id'],
                'properties': {
                    'session_id': {'type': 'string', 'description': 'ID da sessão de checkout do Stripe'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Status do checkout'},
        400: {'description': 'Session ID não fornecido'},
        404: {'description': 'Sessão não encontrada'}
    }
})
def verify_checkout():
    """Verificar se checkout foi completado e atualizar assinatura"""
    try:
        user_id = int(get_jwt_identity())
        data = request.json
        session_id = data.get('session_id') if data else None

        if not session_id:
            return jsonify({'error': 'session_id é obrigatório'}), 400

        # Buscar sessão no Stripe
        try:
            checkout_session = stripe.checkout.Session.retrieve(session_id)
        except stripe.StripeError as e:
            return jsonify({'error': f'Sessão não encontrada: {str(e)}'}), 404

        # Verificar se o checkout foi completado
        if checkout_session.status != 'complete':
            return jsonify({
                'success': False,
                'status': checkout_session.status,
                'message': 'Checkout não foi completado'
            }), 200

        # Buscar assinatura do usuário
        subscription = Subscription.query.filter_by(user_id=user_id).first()

        if not subscription:
            return jsonify({'error': 'Assinatura não encontrada'}), 404

        # Se já está ativa, retornar sucesso
        if subscription.status in ['active', 'trialing']:
            return jsonify({
                'success': True,
                'status': subscription.status,
                'subscription': subscription.to_dict()
            }), 200

        # Atualizar com dados do checkout
        stripe_subscription_id = checkout_session.subscription
        stripe_customer_id = checkout_session.customer

        if stripe_subscription_id:
            # Buscar dados da assinatura no Stripe
            stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
            trial_end = datetime.fromtimestamp(stripe_sub.trial_end) if stripe_sub.trial_end else None

            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.stripe_customer_id = stripe_customer_id
            subscription.status = stripe_sub.status
            subscription.start_date = datetime.utcnow()
            subscription.trial_end = trial_end
            db.session.commit()

            return jsonify({
                'success': True,
                'status': stripe_sub.status,
                'message': 'Assinatura ativada com sucesso!',
                'subscription': subscription.to_dict()
            }), 200

        return jsonify({
            'success': False,
            'message': 'Checkout completado mas sem assinatura associada'
        }), 200

    except Exception as e:
        return jsonify({'error': f'Erro ao verificar checkout: {str(e)}'}), 500


@subscriptions_bp.route('/retry-checkout', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Retentar checkout',
    'description': 'Cria novo checkout para assinatura pendente',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'success_url': {'type': 'string'},
                    'cancel_url': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Novo checkout criado'},
        400: {'description': 'Não há assinatura pendente'},
        404: {'description': 'Assinatura não encontrada'}
    }
})
def retry_checkout():
    """Criar novo checkout para assinatura pendente"""
    try:
        user_id = int(get_jwt_identity())
        data = request.json or {}
        success_url = data.get('success_url', 'http://localhost:3000/subscription/success')
        cancel_url = data.get('cancel_url', 'http://localhost:3000/subscription/cancel')

        # Buscar assinatura pendente
        subscription = Subscription.query.filter_by(user_id=user_id).first()

        if not subscription:
            return jsonify({'error': 'Assinatura não encontrada'}), 404

        if subscription.status in ['active', 'trialing']:
            return jsonify({'error': 'Assinatura já está ativa'}), 400

        # Buscar usuário
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        plan = subscription.plan or 'basic'

        # Criar ou recuperar customer no Stripe
        stripe_customer_id = subscription.stripe_customer_id
        if not stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={'user_id': str(user_id)}
            )
            stripe_customer_id = customer.id

        # Criar nova Checkout Session
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': PLANS[plan]['price_id'],
                'quantity': 1
            }],
            subscription_data={
                'trial_period_days': 7,
                'metadata': {
                    'user_id': str(user_id),
                    'plan': plan
                }
            },
            success_url=success_url if '{CHECKOUT_SESSION_ID}' in success_url else success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user_id),
                'plan': plan
            }
        )

        # Atualizar customer_id se necessário
        subscription.stripe_customer_id = stripe_customer_id
        db.session.commit()

        return jsonify({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        }), 200

    except stripe.StripeError as e:
        return jsonify({'error': f'Erro no Stripe: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Erro ao criar checkout: {str(e)}'}), 500


@subscriptions_bp.route('/webhook', methods=['POST'])
@swag_from({
    'tags': ['Assinaturas'],
    'summary': 'Webhook do Stripe',
    'description': 'Endpoint para receber eventos do Stripe (pagamentos, cancelamentos, etc.)',
    'parameters': [
        {'name': 'Stripe-Signature', 'in': 'header', 'type': 'string', 'required': True, 'description': 'Assinatura do Stripe'}
    ],
    'responses': {
        200: {'description': 'Evento processado com sucesso'},
        400: {'description': 'Payload ou assinatura inválida'},
        500: {'description': 'Webhook secret não configurado'}
    }
})
def stripe_webhook():
    """Webhook do Stripe para eventos de assinatura"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        return jsonify({'error': 'Webhook secret não configurado'}), 500

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Payload inválido'}), 400
    except stripe.SignatureVerificationError:
        return jsonify({'error': 'Assinatura inválida'}), 400

    # Processar eventos
    event_type = event['type']
    data_object = event['data']['object']

    print(f"Webhook recebido: {event_type}")

    if event_type == 'checkout.session.completed':
        # Checkout completado - usuário cadastrou cartão e iniciou trial
        session = data_object
        stripe_subscription_id = session.get('subscription')
        stripe_customer_id = session.get('customer')
        user_id = session.get('metadata', {}).get('user_id')
        plan = session.get('metadata', {}).get('plan')

        if user_id and stripe_subscription_id:
            subscription = Subscription.query.filter_by(user_id=int(user_id)).first()

            if subscription:
                # Buscar dados da assinatura no Stripe
                stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
                trial_end = datetime.fromtimestamp(stripe_sub.trial_end) if stripe_sub.trial_end else None

                subscription.stripe_subscription_id = stripe_subscription_id
                subscription.stripe_customer_id = stripe_customer_id
                subscription.status = stripe_sub.status  # 'trialing'
                subscription.start_date = datetime.utcnow()
                subscription.trial_end = trial_end
                subscription.plan = plan or subscription.plan
                db.session.commit()
                print(f"Checkout completado - Assinatura {stripe_subscription_id} ativada em trial")

    elif event_type == 'invoice.paid':
        # Pagamento bem-sucedido
        subscription_id = data_object.get('subscription')
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()

        if subscription:
            subscription.status = 'active'
            db.session.commit()
            print(f"Assinatura {subscription_id} marcada como ativa")

    elif event_type == 'invoice.payment_failed':
        # Falha no pagamento
        subscription_id = data_object.get('subscription')
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()

        if subscription:
            subscription.status = 'past_due'
            db.session.commit()
            print(f"Assinatura {subscription_id} marcada como past_due")

    elif event_type == 'customer.subscription.deleted':
        # Assinatura cancelada
        subscription_id = data_object['id']
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()

        if subscription:
            subscription.status = 'canceled'
            subscription.end_date = datetime.utcnow()
            db.session.commit()
            print(f"Assinatura {subscription_id} cancelada")

    elif event_type == 'customer.subscription.updated':
        # Assinatura atualizada
        subscription_id = data_object['id']
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()

        if subscription:
            subscription.status = data_object['status']
            subscription.cancel_at_period_end = data_object.get('cancel_at_period_end', False)
            db.session.commit()
            print(f"Assinatura {subscription_id} atualizada: {data_object['status']}")

    elif event_type == 'customer.subscription.trial_will_end':
        # Trial vai terminar em breve
        subscription_id = data_object['id']
        print(f"Trial da assinatura {subscription_id} vai terminar em breve")
        # Aqui você pode enviar notificação ao cliente

    return jsonify({'success': True}), 200
