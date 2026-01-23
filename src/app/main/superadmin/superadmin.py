"""
Super Admin API - Endpoints para gerenciamento administrativo da plataforma SaaS.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
from flasgger import swag_from

from src.config.database import db
from src.models.user import User
from src.models.subscription import Subscription
from src.models.client import Client
from src.models.professional import Professional
from src.models.appointment import Appointment
from src.models.payment import Payment
from src.decorators.admin_required import admin_required

superadmin_bp = Blueprint('superadmin', __name__)


# ============================================================================
# COMPANIES (EMPRESAS/USUÁRIOS)
# ============================================================================

@superadmin_bp.route('/companies', methods=['GET'])
@jwt_required()
@admin_required
def get_companies():
    """
    Lista todas as empresas/usuários cadastrados na plataforma.
    ---
    tags:
      - Super Admin - Companies
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: limit
        in: query
        type: integer
        default: 20
      - name: search
        in: query
        type: string
        description: Busca por nome, email ou slug
      - name: status
        in: query
        type: string
        enum: [active, suspended, all]
        default: all
      - name: plan
        in: query
        type: string
        enum: [basic, pro, enterprise, trial, none, all]
        default: all
      - name: sort_by
        in: query
        type: string
        enum: [created_at, name, mrr, last_activity]
        default: created_at
      - name: sort_order
        in: query
        type: string
        enum: [asc, desc]
        default: desc
    responses:
      200:
        description: Lista de empresas
    """
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    plan = request.args.get('plan', 'all')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')

    # Base query - excluir admins da listagem
    query = User.query.filter(User.role != 'admin')

    # Filtro de busca
    if search:
        search_filter = or_(
            User.name.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%'),
            User.business_name.ilike(f'%{search}%'),
            User.slug.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)

    # Filtro de status (ativo/suspenso)
    if status == 'active':
        query = query.filter(User.active == True)
    elif status == 'suspended':
        query = query.filter(User.active == False)

    # Filtro de plano
    if plan and plan != 'all':
        if plan == 'none':
            query = query.outerjoin(Subscription).filter(Subscription.id == None)
        elif plan == 'trial':
            query = query.join(Subscription).filter(Subscription.status == 'trialing')
        else:
            query = query.join(Subscription).filter(Subscription.plan == plan)

    # Ordenação
    if sort_by == 'name':
        order_col = User.name
    elif sort_by == 'mrr':
        # Para ordenar por MRR, precisa join com subscription
        order_col = User.id  # Simplificado
    else:
        order_col = User.id  # created_at não existe, usar id como proxy

    if sort_order == 'desc':
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(order_col)

    # Paginação
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    companies = []
    for user in pagination.items:
        # Obter subscription
        subscription = Subscription.query.filter_by(user_id=user.id).first()

        # Contar recursos
        clients_count = Client.query.filter_by(user_id=user.id).count()
        professionals_count = Professional.query.filter_by(user_id=user.id).count()
        appointments_count = Appointment.query.filter_by(user_id=user.id).count()

        # Calcular MRR
        mrr = 0
        if subscription and subscription.is_active():
            plan_prices = {'basic': 29, 'pro': 59, 'enterprise': 99}
            mrr = plan_prices.get(subscription.plan, 0)

        companies.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'business_name': user.business_name,
            'slug': user.slug,
            'active': user.active,
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'subscription': {
                'plan': subscription.plan if subscription else None,
                'status': subscription.status if subscription else None,
                'end_date': subscription.end_date.isoformat() if subscription and subscription.end_date else None,
                'trial_end': subscription.trial_end.isoformat() if subscription and subscription.trial_end else None,
            } if subscription else None,
            'stats': {
                'clients': clients_count,
                'professionals': professionals_count,
                'appointments': appointments_count,
                'mrr': mrr
            }
        })

    return jsonify({
        'companies': companies,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@superadmin_bp.route('/companies/<int:company_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_company(company_id):
    """
    Obtém detalhes de uma empresa específica.
    ---
    tags:
      - Super Admin - Companies
    security:
      - Bearer: []
    parameters:
      - name: company_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Detalhes da empresa
      404:
        description: Empresa não encontrada
    """
    user = User.query.get(company_id)
    if not user or user.role == 'admin':
        return jsonify({'error': 'Empresa não encontrada'}), 404

    subscription = Subscription.query.filter_by(user_id=user.id).first()

    # Estatísticas detalhadas
    clients_count = Client.query.filter_by(user_id=user.id).count()
    professionals_count = Professional.query.filter_by(user_id=user.id).count()

    # Agendamentos nos últimos 30 dias
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_appointments = Appointment.query.filter(
        Appointment.user_id == user.id,
        Appointment.created_at >= thirty_days_ago
    ).count()

    total_appointments = Appointment.query.filter_by(user_id=user.id).count()

    # Calcular MRR
    mrr = 0
    if subscription and subscription.is_active():
        plan_prices = {'basic': 29, 'pro': 59, 'enterprise': 99}
        mrr = plan_prices.get(subscription.plan, 0)

    # Histórico de assinatura (simplificado - apenas atual)
    subscription_history = []
    if subscription:
        subscription_history.append({
            'plan': subscription.plan,
            'status': subscription.status,
            'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
            'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
            'stripe_subscription_id': subscription.stripe_subscription_id
        })

    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'business_name': user.business_name,
        'business_phone': user.business_phone,
        'business_address': user.business_address,
        'slug': user.slug,
        'active': user.active,
        'email_verified': user.email_verified,
        'online_booking_enabled': user.online_booking_enabled,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'subscription': subscription.to_dict() if subscription else None,
        'subscription_history': subscription_history,
        'stats': {
            'clients': clients_count,
            'professionals': professionals_count,
            'total_appointments': total_appointments,
            'recent_appointments': recent_appointments,
            'mrr': mrr
        }
    }), 200


@superadmin_bp.route('/companies/<int:company_id>/suspend', methods=['POST'])
@jwt_required()
@admin_required
def suspend_company(company_id):
    """
    Suspende uma empresa.
    ---
    tags:
      - Super Admin - Companies
    security:
      - Bearer: []
    parameters:
      - name: company_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            reason:
              type: string
              description: Motivo da suspensão
    responses:
      200:
        description: Empresa suspensa com sucesso
      404:
        description: Empresa não encontrada
    """
    user = User.query.get(company_id)
    if not user or user.role == 'admin':
        return jsonify({'error': 'Empresa não encontrada'}), 404

    data = request.get_json() or {}
    reason = data.get('reason', '')

    user.active = False
    db.session.commit()

    return jsonify({
        'message': 'Empresa suspensa com sucesso',
        'company_id': company_id,
        'reason': reason
    }), 200


@superadmin_bp.route('/companies/<int:company_id>/activate', methods=['POST'])
@jwt_required()
@admin_required
def activate_company(company_id):
    """
    Ativa uma empresa suspensa.
    ---
    tags:
      - Super Admin - Companies
    security:
      - Bearer: []
    parameters:
      - name: company_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Empresa ativada com sucesso
      404:
        description: Empresa não encontrada
    """
    user = User.query.get(company_id)
    if not user or user.role == 'admin':
        return jsonify({'error': 'Empresa não encontrada'}), 404

    user.active = True
    db.session.commit()

    return jsonify({
        'message': 'Empresa ativada com sucesso',
        'company_id': company_id
    }), 200


@superadmin_bp.route('/companies/<int:company_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_company(company_id):
    """
    Atualiza dados de uma empresa.
    ---
    tags:
      - Super Admin - Companies
    security:
      - Bearer: []
    parameters:
      - name: company_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            name:
              type: string
            email:
              type: string
            business_name:
              type: string
            role:
              type: string
              enum: [user, admin]
    responses:
      200:
        description: Empresa atualizada com sucesso
      404:
        description: Empresa não encontrada
    """
    user = User.query.get(company_id)
    if not user:
        return jsonify({'error': 'Empresa não encontrada'}), 404

    data = request.get_json()

    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    if 'business_name' in data:
        user.business_name = data['business_name']
    if 'role' in data and data['role'] in ['user', 'admin', 'superadmin']:
        user.role = data['role']

    db.session.commit()

    return jsonify({
        'message': 'Empresa atualizada com sucesso',
        'company': user.to_dict()
    }), 200


@superadmin_bp.route('/companies/<int:company_id>/reset-password', methods=['POST'])
@jwt_required()
@admin_required
def reset_company_password(company_id):
    """
    Redefine a senha de uma empresa.
    ---
    tags:
      - Super Admin - Companies
    security:
      - Bearer: []
    parameters:
      - name: company_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          required:
            - new_password
          properties:
            new_password:
              type: string
              minLength: 6
    responses:
      200:
        description: Senha redefinida com sucesso
      400:
        description: Senha invalida
      404:
        description: Empresa não encontrada
    """
    user = User.query.get(company_id)
    if not user:
        return jsonify({'error': 'Empresa não encontrada'}), 404

    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'A senha deve ter pelo menos 6 caracteres'}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({
        'message': 'Senha redefinida com sucesso',
        'company_id': company_id,
        'email': user.email
    }), 200


# ============================================================================
# SUBSCRIPTIONS (ASSINATURAS)
# ============================================================================

@superadmin_bp.route('/subscriptions', methods=['GET'])
@jwt_required()
@admin_required
def get_subscriptions():
    """
    Lista todas as assinaturas.
    ---
    tags:
      - Super Admin - Subscriptions
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: limit
        in: query
        type: integer
        default: 20
      - name: status
        in: query
        type: string
        enum: [active, trialing, canceled, past_due, all]
        default: all
      - name: plan
        in: query
        type: string
        enum: [basic, pro, enterprise, all]
        default: all
    responses:
      200:
        description: Lista de assinaturas
    """
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    status = request.args.get('status', 'all')
    plan = request.args.get('plan', 'all')

    query = Subscription.query

    if status and status != 'all':
        query = query.filter(Subscription.status == status)

    if plan and plan != 'all':
        query = query.filter(Subscription.plan == plan)

    query = query.order_by(desc(Subscription.created_at))
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    subscriptions = []
    for sub in pagination.items:
        user = User.query.get(sub.user_id)
        subscriptions.append({
            'id': sub.id,
            'user_id': sub.user_id,
            'company_name': user.business_name or user.name if user else 'N/A',
            'company_email': user.email if user else 'N/A',
            'plan': sub.plan,
            'status': sub.status,
            'start_date': sub.start_date.isoformat() if sub.start_date else None,
            'end_date': sub.end_date.isoformat() if sub.end_date else None,
            'trial_end': sub.trial_end.isoformat() if sub.trial_end else None,
            'cancel_at_period_end': sub.cancel_at_period_end,
            'stripe_subscription_id': sub.stripe_subscription_id
        })

    return jsonify({
        'subscriptions': subscriptions,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@superadmin_bp.route('/subscriptions/<int:subscription_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_subscription(subscription_id):
    """
    Obtém detalhes de uma assinatura específica.
    ---
    tags:
      - Super Admin - Subscriptions
    security:
      - Bearer: []
    parameters:
      - name: subscription_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Detalhes da assinatura
      404:
        description: Assinatura não encontrada
    """
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({'error': 'Assinatura não encontrada'}), 404

    user = User.query.get(subscription.user_id)

    return jsonify({
        'subscription': subscription.to_dict(),
        'company': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'business_name': user.business_name
        } if user else None
    }), 200


@superadmin_bp.route('/subscriptions/<int:subscription_id>/plan', methods=['PUT'])
@jwt_required()
@admin_required
def change_subscription_plan(subscription_id):
    """
    Altera o plano de uma assinatura.
    ---
    tags:
      - Super Admin - Subscriptions
    security:
      - Bearer: []
    parameters:
      - name: subscription_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - new_plan
          properties:
            new_plan:
              type: string
              enum: [basic, pro, enterprise]
    responses:
      200:
        description: Plano alterado com sucesso
      400:
        description: Dados inválidos
      404:
        description: Assinatura não encontrada
    """
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({'error': 'Assinatura não encontrada'}), 404

    data = request.get_json()
    new_plan = data.get('new_plan')

    if new_plan not in ['basic', 'pro', 'enterprise']:
        return jsonify({'error': 'Plano inválido'}), 400

    old_plan = subscription.plan
    subscription.plan = new_plan
    subscription.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Plano alterado com sucesso',
        'subscription_id': subscription_id,
        'old_plan': old_plan,
        'new_plan': new_plan
    }), 200


@superadmin_bp.route('/subscriptions/<int:subscription_id>/extend', methods=['POST'])
@jwt_required()
@admin_required
def extend_subscription(subscription_id):
    """
    Estende o período de uma assinatura.
    ---
    tags:
      - Super Admin - Subscriptions
    security:
      - Bearer: []
    parameters:
      - name: subscription_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - days
          properties:
            days:
              type: integer
              minimum: 1
              description: Número de dias para estender
    responses:
      200:
        description: Assinatura estendida com sucesso
      400:
        description: Dados inválidos
      404:
        description: Assinatura não encontrada
    """
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({'error': 'Assinatura não encontrada'}), 404

    data = request.get_json()
    days = data.get('days', 0)

    if not days or days < 1:
        return jsonify({'error': 'Número de dias inválido'}), 400

    # Estender end_date
    if subscription.end_date:
        subscription.end_date = subscription.end_date + timedelta(days=days)
    else:
        subscription.end_date = datetime.utcnow() + timedelta(days=days)

    # Se estava cancelada, reativar
    if subscription.status == 'canceled':
        subscription.status = 'active'
        subscription.cancel_at_period_end = False

    subscription.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Assinatura estendida com sucesso',
        'subscription_id': subscription_id,
        'days_added': days,
        'new_end_date': subscription.end_date.isoformat()
    }), 200


@superadmin_bp.route('/subscriptions/<int:subscription_id>/cancel', methods=['POST'])
@jwt_required()
@admin_required
def cancel_subscription(subscription_id):
    """
    Cancela uma assinatura.
    ---
    tags:
      - Super Admin - Subscriptions
    security:
      - Bearer: []
    parameters:
      - name: subscription_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            reason:
              type: string
              description: Motivo do cancelamento
    responses:
      200:
        description: Assinatura cancelada com sucesso
      404:
        description: Assinatura não encontrada
    """
    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({'error': 'Assinatura não encontrada'}), 404

    data = request.get_json() or {}
    reason = data.get('reason', '')

    subscription.status = 'canceled'
    subscription.cancel_at_period_end = True
    subscription.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Assinatura cancelada com sucesso',
        'subscription_id': subscription_id,
        'reason': reason
    }), 200


@superadmin_bp.route('/subscriptions/expiring', methods=['GET'])
@jwt_required()
@admin_required
def get_expiring_subscriptions():
    """
    Lista assinaturas que vencem em breve.
    ---
    tags:
      - Super Admin - Subscriptions
    security:
      - Bearer: []
    parameters:
      - name: days
        in: query
        type: integer
        default: 7
        description: Dias para considerar como "vencendo em breve"
    responses:
      200:
        description: Lista de assinaturas vencendo em breve
    """
    days = request.args.get('days', 7, type=int)

    cutoff_date = datetime.utcnow() + timedelta(days=days)

    subscriptions = Subscription.query.filter(
        and_(
            Subscription.status.in_(['active', 'trialing']),
            or_(
                and_(Subscription.end_date != None, Subscription.end_date <= cutoff_date),
                and_(Subscription.trial_end != None, Subscription.trial_end <= cutoff_date)
            )
        )
    ).all()

    result = []
    for sub in subscriptions:
        user = User.query.get(sub.user_id)

        # Calcular dias restantes
        if sub.status == 'trialing' and sub.trial_end:
            days_remaining = (sub.trial_end - datetime.utcnow()).days
            expiring_type = 'trial'
        elif sub.end_date:
            days_remaining = (sub.end_date - datetime.utcnow()).days
            expiring_type = 'subscription'
        else:
            days_remaining = None
            expiring_type = 'unknown'

        result.append({
            'id': sub.id,
            'user_id': sub.user_id,
            'company_name': user.business_name or user.name if user else 'N/A',
            'company_email': user.email if user else 'N/A',
            'plan': sub.plan,
            'status': sub.status,
            'expiring_type': expiring_type,
            'days_remaining': days_remaining,
            'end_date': sub.end_date.isoformat() if sub.end_date else None,
            'trial_end': sub.trial_end.isoformat() if sub.trial_end else None
        })

    # Ordenar por dias restantes
    result.sort(key=lambda x: x['days_remaining'] if x['days_remaining'] is not None else 999)

    return jsonify({
        'expiring_subscriptions': result,
        'total': len(result)
    }), 200


# ============================================================================
# ANALYTICS
# ============================================================================

@superadmin_bp.route('/analytics/overview', methods=['GET'])
@jwt_required()
@admin_required
def get_analytics_overview():
    """
    Obtém métricas gerais da plataforma.
    ---
    tags:
      - Super Admin - Analytics
    security:
      - Bearer: []
    responses:
      200:
        description: Métricas gerais
    """
    # Total de empresas (excluindo admins)
    total_companies = User.query.filter(User.role != 'admin').count()
    active_companies = User.query.filter(User.role != 'admin', User.active == True).count()

    # Empresas em trial
    trial_companies = Subscription.query.filter(Subscription.status == 'trialing').count()

    # Assinaturas ativas
    active_subscriptions = Subscription.query.filter(
        Subscription.status.in_(['active', 'trialing'])
    ).count()

    # Calcular MRR
    mrr = 0
    plan_prices = {'basic': 29, 'pro': 59, 'enterprise': 99}
    active_subs = Subscription.query.filter(Subscription.status == 'active').all()
    for sub in active_subs:
        mrr += plan_prices.get(sub.plan, 0)

    # ARR
    arr = mrr * 12

    # Crescimento do mês (novos usuários)
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = User.query.filter(
        User.role != 'admin',
        User.id > 0  # Proxy para created_at
    ).count()  # Simplificado - idealmente filtrar por created_at

    # Churn rate (simplificado)
    canceled_this_month = Subscription.query.filter(
        Subscription.status == 'canceled'
    ).count()

    churn_rate = (canceled_this_month / total_companies * 100) if total_companies > 0 else 0

    # Distribuição por plano
    plan_distribution = {
        'basic': Subscription.query.filter(Subscription.plan == 'basic', Subscription.status.in_(['active', 'trialing'])).count(),
        'pro': Subscription.query.filter(Subscription.plan == 'pro', Subscription.status.in_(['active', 'trialing'])).count(),
        'enterprise': Subscription.query.filter(Subscription.plan == 'enterprise', Subscription.status.in_(['active', 'trialing'])).count(),
    }

    return jsonify({
        'total_companies': total_companies,
        'active_companies': active_companies,
        'trial_companies': trial_companies,
        'active_subscriptions': active_subscriptions,
        'mrr': mrr,
        'arr': arr,
        'churn_rate': round(churn_rate, 2),
        'plan_distribution': plan_distribution
    }), 200


@superadmin_bp.route('/analytics/revenue', methods=['GET'])
@jwt_required()
@admin_required
def get_revenue_analytics():
    """
    Obtém dados de receita para gráficos.
    ---
    tags:
      - Super Admin - Analytics
    security:
      - Bearer: []
    parameters:
      - name: months
        in: query
        type: integer
        default: 12
        description: Número de meses para retornar
    responses:
      200:
        description: Dados de receita
    """
    months = request.args.get('months', 12, type=int)

    # Calcular receita mensal (simplificado - dados estáticos por enquanto)
    plan_prices = {'basic': 29, 'pro': 59, 'enterprise': 99}

    revenue_data = []
    current_date = datetime.utcnow()

    for i in range(months - 1, -1, -1):
        # Calcular mês
        month_date = current_date - timedelta(days=i * 30)
        month_name = month_date.strftime('%Y-%m')

        # Contar assinaturas ativas (simplificado)
        active_count = Subscription.query.filter(
            Subscription.status.in_(['active', 'trialing'])
        ).count()

        # Calcular receita estimada
        mrr = 0
        for sub in Subscription.query.filter(Subscription.status == 'active').all():
            mrr += plan_prices.get(sub.plan, 0)

        revenue_data.append({
            'month': month_name,
            'mrr': mrr,
            'subscriptions': active_count
        })

    return jsonify({
        'revenue_data': revenue_data,
        'total_months': months
    }), 200


@superadmin_bp.route('/analytics/growth', methods=['GET'])
@jwt_required()
@admin_required
def get_growth_analytics():
    """
    Obtém dados de crescimento.
    ---
    tags:
      - Super Admin - Analytics
    security:
      - Bearer: []
    parameters:
      - name: months
        in: query
        type: integer
        default: 12
    responses:
      200:
        description: Dados de crescimento
    """
    months = request.args.get('months', 12, type=int)

    # Dados de crescimento (simplificado)
    total_companies = User.query.filter(User.role != 'admin').count()
    total_subscriptions = Subscription.query.filter(
        Subscription.status.in_(['active', 'trialing'])
    ).count()

    return jsonify({
        'total_companies': total_companies,
        'total_subscriptions': total_subscriptions,
        'growth_rate': 0,  # Precisaria de dados históricos
        'months': months
    }), 200


@superadmin_bp.route('/analytics/churn', methods=['GET'])
@jwt_required()
@admin_required
def get_churn_analytics():
    """
    Obtém dados de churn.
    ---
    tags:
      - Super Admin - Analytics
    security:
      - Bearer: []
    responses:
      200:
        description: Dados de churn
    """
    total_subscriptions = Subscription.query.count()
    canceled_subscriptions = Subscription.query.filter(
        Subscription.status == 'canceled'
    ).count()

    churn_rate = (canceled_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0

    return jsonify({
        'total_subscriptions': total_subscriptions,
        'canceled_subscriptions': canceled_subscriptions,
        'churn_rate': round(churn_rate, 2)
    }), 200


@superadmin_bp.route('/analytics/plans', methods=['GET'])
@jwt_required()
@admin_required
def get_plan_distribution():
    """
    Obtém distribuição de assinaturas por plano.
    ---
    tags:
      - Super Admin - Analytics
    security:
      - Bearer: []
    responses:
      200:
        description: Distribuição por plano
    """
    distribution = []
    plan_prices = {'basic': 29, 'pro': 59, 'enterprise': 99}

    for plan in ['basic', 'pro', 'enterprise']:
        count = Subscription.query.filter(
            Subscription.plan == plan,
            Subscription.status.in_(['active', 'trialing'])
        ).count()

        distribution.append({
            'plan': plan,
            'count': count,
            'mrr': count * plan_prices.get(plan, 0)
        })

    return jsonify({
        'distribution': distribution
    }), 200


# ============================================================================
# ALERTS AND ACTIVITY
# ============================================================================

@superadmin_bp.route('/alerts', methods=['GET'])
@jwt_required()
@admin_required
def get_alerts():
    """
    Obtém alertas do sistema.
    ---
    tags:
      - Super Admin - Alerts
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de alertas
    """
    alerts = []

    # Assinaturas vencendo em 7 dias
    seven_days = datetime.utcnow() + timedelta(days=7)
    expiring_soon = Subscription.query.filter(
        Subscription.status.in_(['active', 'trialing']),
        or_(
            and_(Subscription.end_date != None, Subscription.end_date <= seven_days),
            and_(Subscription.trial_end != None, Subscription.trial_end <= seven_days)
        )
    ).count()

    if expiring_soon > 0:
        alerts.append({
            'type': 'warning',
            'title': 'Assinaturas Vencendo',
            'message': f'{expiring_soon} assinatura(s) vence(m) nos próximos 7 dias',
            'count': expiring_soon
        })

    # Trials expirando
    trials_expiring = Subscription.query.filter(
        Subscription.status == 'trialing',
        Subscription.trial_end != None,
        Subscription.trial_end <= seven_days
    ).count()

    if trials_expiring > 0:
        alerts.append({
            'type': 'info',
            'title': 'Trials Expirando',
            'message': f'{trials_expiring} período(s) de teste expira(m) em breve',
            'count': trials_expiring
        })

    # Empresas suspensas
    suspended = User.query.filter(User.role != 'admin', User.active == False).count()
    if suspended > 0:
        alerts.append({
            'type': 'error',
            'title': 'Empresas Suspensas',
            'message': f'{suspended} empresa(s) está(ão) suspensa(s)',
            'count': suspended
        })

    # Pagamentos atrasados
    past_due = Subscription.query.filter(Subscription.status == 'past_due').count()
    if past_due > 0:
        alerts.append({
            'type': 'error',
            'title': 'Pagamentos Atrasados',
            'message': f'{past_due} pagamento(s) atrasado(s)',
            'count': past_due
        })

    return jsonify({
        'alerts': alerts,
        'total': len(alerts)
    }), 200


@superadmin_bp.route('/activity/recent', methods=['GET'])
@jwt_required()
@admin_required
def get_recent_activity():
    """
    Obtém atividades recentes na plataforma.
    ---
    tags:
      - Super Admin - Activity
    security:
      - Bearer: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: Lista de atividades recentes
    """
    limit = request.args.get('limit', 10, type=int)

    activities = []

    # Últimas empresas cadastradas
    recent_users = User.query.filter(User.role != 'admin').order_by(
        desc(User.id)
    ).limit(limit).all()

    for user in recent_users:
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        activities.append({
            'type': 'new_company',
            'company_id': user.id,
            'company_name': user.business_name or user.name,
            'email': user.email,
            'plan': subscription.plan if subscription else None,
            'status': subscription.status if subscription else 'no_subscription'
        })

    return jsonify({
        'activities': activities[:limit],
        'total': len(activities)
    }), 200


# ============================================================================
# PAYMENTS (PAGAMENTOS/FATURAMENTO)
# ============================================================================

@superadmin_bp.route('/payments', methods=['GET'])
@jwt_required()
@admin_required
def get_payments():
    """
    Lista todos os pagamentos/faturamentos da plataforma.
    ---
    tags:
      - Super Admin - Payments
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: limit
        in: query
        type: integer
        default: 20
      - name: status
        in: query
        type: string
        enum: [paid, pending, failed, all]
        default: all
      - name: start_date
        in: query
        type: string
        format: date
        description: Data inicial (YYYY-MM-DD)
      - name: end_date
        in: query
        type: string
        format: date
        description: Data final (YYYY-MM-DD)
      - name: sort_by
        in: query
        type: string
        enum: [paid_at, amount, created_at]
        default: paid_at
      - name: sort_order
        in: query
        type: string
        enum: [asc, desc]
        default: desc
    responses:
      200:
        description: Lista de pagamentos
    """
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    status = request.args.get('status', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_by = request.args.get('sort_by', 'paid_at')
    sort_order = request.args.get('sort_order', 'desc')

    # Base query com joins
    query = Payment.query.join(Subscription).join(User)

    # Filtro por status
    if status != 'all':
        query = query.filter(Payment.status == status)

    # Filtro por data
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Payment.paid_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Payment.paid_at < end)
        except ValueError:
            pass

    # Ordenação
    if sort_by == 'amount':
        order_col = Payment.amount
    elif sort_by == 'created_at':
        order_col = Payment.created_at
    else:
        order_col = Payment.paid_at

    if sort_order == 'desc':
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(order_col)

    # Paginação
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    payments = []
    for payment in pagination.items:
        user = User.query.get(payment.user_id)
        subscription = Subscription.query.get(payment.subscription_id)

        payments.append({
            'id': payment.id,
            'stripe_invoice_id': payment.stripe_invoice_id,
            'stripe_payment_intent_id': payment.stripe_payment_intent_id,
            'amount': float(payment.amount) if payment.amount else 0,
            'currency': payment.currency,
            'status': payment.status,
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
            'period_start': payment.period_start.isoformat() if payment.period_start else None,
            'period_end': payment.period_end.isoformat() if payment.period_end else None,
            'created_at': payment.created_at.isoformat() if payment.created_at else None,
            'company': {
                'id': user.id if user else None,
                'name': user.name if user else None,
                'email': user.email if user else None
            },
            'subscription': {
                'id': subscription.id if subscription else None,
                'plan': subscription.plan if subscription else None,
                'status': subscription.status if subscription else None
            }
        })

    return jsonify({
        'payments': payments,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@superadmin_bp.route('/payments/<int:payment_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_payment(payment_id):
    """
    Obtém detalhes de um pagamento específico.
    ---
    tags:
      - Super Admin - Payments
    security:
      - Bearer: []
    parameters:
      - name: payment_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Detalhes do pagamento
      404:
        description: Pagamento não encontrado
    """
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'error': 'Pagamento não encontrado'}), 404

    user = User.query.get(payment.user_id)
    subscription = Subscription.query.get(payment.subscription_id)

    return jsonify({
        'id': payment.id,
        'stripe_invoice_id': payment.stripe_invoice_id,
        'stripe_payment_intent_id': payment.stripe_payment_intent_id,
        'amount': float(payment.amount) if payment.amount else 0,
        'currency': payment.currency,
        'status': payment.status,
        'paid_at': payment.paid_at.isoformat() if payment.paid_at else None,
        'period_start': payment.period_start.isoformat() if payment.period_start else None,
        'period_end': payment.period_end.isoformat() if payment.period_end else None,
        'created_at': payment.created_at.isoformat() if payment.created_at else None,
        'updated_at': payment.updated_at.isoformat() if payment.updated_at else None,
        'company': {
            'id': user.id if user else None,
            'name': user.name if user else None,
            'email': user.email if user else None,
            'company_name': user.company_name if user else None
        },
        'subscription': {
            'id': subscription.id if subscription else None,
            'plan': subscription.plan if subscription else None,
            'status': subscription.status if subscription else None,
            'stripe_subscription_id': subscription.stripe_subscription_id if subscription else None
        }
    }), 200


@superadmin_bp.route('/payments/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_payments_stats():
    """
    Obtém estatísticas de faturamento.
    ---
    tags:
      - Super Admin - Payments
    security:
      - Bearer: []
    parameters:
      - name: months
        in: query
        type: integer
        default: 12
        description: Número de meses para análise
    responses:
      200:
        description: Estatísticas de faturamento
    """
    months = request.args.get('months', 12, type=int)

    # Total faturado
    total_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'paid'
    ).scalar() or 0

    # Total de pagamentos
    total_payments = Payment.query.filter(Payment.status == 'paid').count()

    # Faturamento por mês
    monthly_data = []
    for i in range(months - 1, -1, -1):
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i * 30)
        month_end = month_start + timedelta(days=30)

        month_revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == 'paid',
            Payment.paid_at >= month_start,
            Payment.paid_at < month_end
        ).scalar() or 0

        month_count = Payment.query.filter(
            Payment.status == 'paid',
            Payment.paid_at >= month_start,
            Payment.paid_at < month_end
        ).count()

        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'revenue': float(month_revenue),
            'count': month_count
        })

    # Faturamento dos últimos 30 dias
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    last_30_days_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'paid',
        Payment.paid_at >= thirty_days_ago
    ).scalar() or 0

    last_30_days_count = Payment.query.filter(
        Payment.status == 'paid',
        Payment.paid_at >= thirty_days_ago
    ).count()

    return jsonify({
        'total_revenue': float(total_revenue),
        'total_payments': total_payments,
        'last_30_days': {
            'revenue': float(last_30_days_revenue),
            'count': last_30_days_count
        },
        'monthly': monthly_data
    }), 200
