from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from src.models.subscription import Subscription
from src.models.user import User


def subscription_required(plans=None):
    """
    Decorator para verificar se o usuário tem uma assinatura ativa.
    Admins são isentos de verificação de assinatura.

    Args:
        plans: Lista de planos que têm permissão para acessar o recurso.
               Se None, qualquer plano ativo é aceito.

    Usage:
        @subscription_required()  # Qualquer plano ativo
        @subscription_required(['pro', 'enterprise'])  # Apenas planos específicos

    Examples:
        @app.route('/api/premium-feature')
        @jwt_required()
        @subscription_required(['pro', 'enterprise'])
        def premium_feature():
            return jsonify({'message': 'Feature premium'})
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                user_id = get_jwt_identity()

                # Verificar se é admin - admins não precisam de assinatura
                user = User.query.get(user_id)
                if user and user.role == 'admin':
                    return fn(*args, **kwargs)

                # Buscar assinatura do usuário
                subscription = Subscription.query.filter_by(user_id=user_id).first()

                # Verificar se tem assinatura
                if not subscription:
                    return jsonify({
                        'error': 'Assinatura necessária para acessar este recurso',
                        'code': 'SUBSCRIPTION_REQUIRED',
                        'message': 'Você precisa ter uma assinatura ativa para acessar este recurso'
                    }), 403

                # Verificar se a assinatura está ativa
                if not subscription.is_active():
                    return jsonify({
                        'error': 'Assinatura inativa',
                        'code': 'SUBSCRIPTION_INACTIVE',
                        'status': subscription.status,
                        'message': 'Sua assinatura não está ativa. Por favor, verifique seu pagamento.'
                    }), 403

                # Verificar plano específico (se necessário)
                if plans and subscription.plan not in plans:
                    return jsonify({
                        'error': 'Plano insuficiente',
                        'code': 'PLAN_UPGRADE_REQUIRED',
                        'current_plan': subscription.plan,
                        'required_plans': plans,
                        'message': f'Este recurso requer um dos seguintes planos: {", ".join(plans)}'
                    }), 403

                # Tudo OK, executar a função
                return fn(*args, **kwargs)

            except Exception as e:
                return jsonify({
                    'error': 'Erro ao verificar assinatura',
                    'message': str(e)
                }), 500

        return wrapper
    return decorator


def check_feature_access(feature_name):
    """
    Decorator para verificar acesso a features específicas.
    Útil para features que só estão disponíveis em certos planos.

    Args:
        feature_name: Nome da feature a ser verificada

    Usage:
        @check_feature_access('advanced_reports')
    """
    # Mapeamento de features para planos
    FEATURE_PLANS = {
        'advanced_reports': ['pro', 'enterprise'],
        'whatsapp_reminders': ['pro', 'enterprise'],
        'api_access': ['enterprise'],
        'unlimited_professionals': ['enterprise'],
        'dedicated_support': ['enterprise']
    }

    required_plans = FEATURE_PLANS.get(feature_name, [])

    def decorator(fn):
        @wraps(fn)
        @subscription_required(required_plans if required_plans else None)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        return wrapper
    return decorator
