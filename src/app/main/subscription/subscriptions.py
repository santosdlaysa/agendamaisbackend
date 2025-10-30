import stripe
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from src.config.database import db
from src.models.subscription import Subscription
from src.models.client import Client

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
def create_subscription():
    """Criar nova assinatura"""
    try:
        data = request.json
        client_id = get_jwt_identity()
        plan = data.get('plan')

        # Validar plano
        if plan not in PLANS:
            return jsonify({'error': 'Plano inválido'}), 400

        # Buscar cliente
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        # Verificar se já tem assinatura ativa
        existing = Subscription.query.filter_by(client_id=client_id).first()
        if existing and existing.status in ['active', 'trialing']:
            return jsonify({'error': 'Já existe uma assinatura ativa'}), 400

        # Criar ou recuperar customer no Stripe
        stripe_customer_id = None
        if existing and existing.stripe_customer_id:
            stripe_customer_id = existing.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=client.email,
                name=client.name,
                metadata={'client_id': str(client_id)}
            )
            stripe_customer_id = customer.id

        # Criar assinatura no Stripe com trial de 7 dias
        stripe_subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{'price': PLANS[plan]['price_id']}],
            trial_period_days=7,
            payment_behavior='default_incomplete',
            payment_settings={
                'save_default_payment_method': 'on_subscription'
            },
            expand=['latest_invoice.payment_intent']
        )

        # Calcular data de fim do trial
        trial_end = datetime.utcnow() + timedelta(days=7)

        # Criar ou atualizar assinatura no banco
        if existing:
            existing.plan = plan
            existing.stripe_customer_id = stripe_customer_id
            existing.stripe_subscription_id = stripe_subscription.id
            existing.status = 'trialing'
            existing.start_date = datetime.utcnow()
            existing.trial_end = trial_end
            existing.cancel_at_period_end = False
            existing.end_date = None
            subscription = existing
        else:
            subscription = Subscription(
                client_id=client_id,
                plan=plan,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription.id,
                status='trialing',
                trial_end=trial_end
            )
            db.session.add(subscription)

        db.session.commit()

        return jsonify({
            'subscription_id': subscription.id,
            'stripe_subscription_id': stripe_subscription.id,
            'client_secret': stripe_subscription.latest_invoice.payment_intent.client_secret,
            'status': subscription.status,
            'trial_end': trial_end.isoformat()
        }), 201

    except stripe.error.StripeError as e:
        db.session.rollback()
        return jsonify({'error': f'Erro no Stripe: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar assinatura: {str(e)}'}), 500


@subscriptions_bp.route('/status', methods=['GET'])
@jwt_required()
def get_subscription_status():
    """Obter status da assinatura do cliente"""
    try:
        client_id = get_jwt_identity()

        subscription = Subscription.query.filter_by(client_id=client_id).first()

        if not subscription:
            return jsonify({'has_subscription': False}), 200

        # Tentar sincronizar com Stripe
        if subscription.stripe_subscription_id:
            try:
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                subscription.status = stripe_sub.status
                subscription.cancel_at_period_end = stripe_sub.cancel_at_period_end
                db.session.commit()
            except stripe.error.StripeError as e:
                print(f"Erro ao sincronizar com Stripe: {e}")

        return jsonify({
            'has_subscription': True,
            'subscription': subscription.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': f'Erro ao buscar assinatura: {str(e)}'}), 500


@subscriptions_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancelar assinatura ao fim do período"""
    try:
        client_id = get_jwt_identity()

        subscription = Subscription.query.filter_by(client_id=client_id).first()

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

    except stripe.error.StripeError as e:
        return jsonify({'error': f'Erro no Stripe: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Erro ao cancelar assinatura: {str(e)}'}), 500


@subscriptions_bp.route('/reactivate', methods=['POST'])
@jwt_required()
def reactivate_subscription():
    """Reativar assinatura cancelada"""
    try:
        client_id = get_jwt_identity()

        subscription = Subscription.query.filter_by(client_id=client_id).first()

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

    except stripe.error.StripeError as e:
        return jsonify({'error': f'Erro no Stripe: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Erro ao reativar assinatura: {str(e)}'}), 500


@subscriptions_bp.route('/webhook', methods=['POST'])
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
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Assinatura inválida'}), 400

    # Processar eventos
    event_type = event['type']
    data_object = event['data']['object']

    print(f"Webhook recebido: {event_type}")

    if event_type == 'invoice.paid':
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
