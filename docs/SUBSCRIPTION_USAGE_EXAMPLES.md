# Exemplos de Uso - Sistema de Assinaturas

## 1. Proteger Rotas com Assinatura

### Exemplo Básico - Qualquer Plano Ativo

```python
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.decorators import subscription_required

features_bp = Blueprint('features', __name__)

@features_bp.route('/api/basic-feature', methods=['GET'])
@jwt_required()
@subscription_required()
def basic_feature():
    """Feature disponível para qualquer plano ativo"""
    return jsonify({
        'message': 'Esta feature está disponível para todos os assinantes'
    }), 200
```

### Exemplo Intermediário - Planos Específicos

```python
@features_bp.route('/api/advanced-reports', methods=['GET'])
@jwt_required()
@subscription_required(['pro', 'enterprise'])
def advanced_reports():
    """Feature disponível apenas para planos Pro e Enterprise"""
    from src.models.appointment import Appointment
    from flask_jwt_extended import get_jwt_identity

    client_id = get_jwt_identity()

    # Sua lógica aqui
    appointments = Appointment.query.filter_by(client_id=client_id).all()

    return jsonify({
        'report': 'dados avançados',
        'total': len(appointments)
    }), 200
```

### Exemplo Avançado - Feature Enterprise Only

```python
@features_bp.route('/api/api-access', methods=['POST'])
@jwt_required()
@subscription_required(['enterprise'])
def api_access():
    """Feature exclusiva do plano Enterprise"""
    return jsonify({
        'api_key': 'generated_api_key',
        'message': 'API access granted'
    }), 200
```

## 2. Verificar Plano Programaticamente

### Dentro de uma Rota

```python
@features_bp.route('/api/dynamic-feature', methods=['GET'])
@jwt_required()
def dynamic_feature():
    """Comportamento diferente por plano"""
    from flask_jwt_extended import get_jwt_identity
    from src.models.subscription import Subscription

    client_id = get_jwt_identity()
    subscription = Subscription.query.filter_by(client_id=client_id).first()

    if not subscription or not subscription.is_active():
        return jsonify({'error': 'Assinatura necessária'}), 403

    # Comportamento baseado no plano
    if subscription.plan == 'basic':
        limit = 100
    elif subscription.plan == 'pro':
        limit = 1000
    else:  # enterprise
        limit = None  # ilimitado

    return jsonify({
        'limit': limit,
        'plan': subscription.plan
    }), 200
```

### Usando o Método can_access_feature

```python
@features_bp.route('/api/check-feature', methods=['GET'])
@jwt_required()
def check_feature():
    from flask_jwt_extended import get_jwt_identity
    from src.models.subscription import Subscription

    client_id = get_jwt_identity()
    subscription = Subscription.query.filter_by(client_id=client_id).first()

    if not subscription:
        return jsonify({'access': False}), 200

    # Verificar se pode acessar feature específica
    can_access = subscription.can_access_feature(['pro', 'enterprise'])

    return jsonify({
        'access': can_access,
        'plan': subscription.plan,
        'status': subscription.status
    }), 200
```

## 3. Usar o Check de Features Específicas

```python
from src.decorators import check_feature_access

@features_bp.route('/api/whatsapp-reminders', methods=['POST'])
@jwt_required()
@check_feature_access('whatsapp_reminders')
def send_whatsapp_reminder():
    """Feature de lembretes via WhatsApp - Pro e Enterprise"""
    return jsonify({'message': 'Lembrete enviado via WhatsApp'}), 200

@features_bp.route('/api/unlimited-professionals', methods=['GET'])
@jwt_required()
@check_feature_access('unlimited_professionals')
def unlimited_professionals():
    """Feature de profissionais ilimitados - Enterprise only"""
    return jsonify({'message': 'Sem limite de profissionais'}), 200
```

## 4. Tratamento de Erros

### Tratando Respostas de Erro do Decorator

```javascript
// Frontend - Exemplo em JavaScript
async function callProtectedApi() {
  try {
    const response = await fetch('/api/premium-feature', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const error = await response.json();

      if (error.code === 'SUBSCRIPTION_REQUIRED') {
        // Redirecionar para página de planos
        window.location.href = '/subscription/plans';
      } else if (error.code === 'SUBSCRIPTION_INACTIVE') {
        // Mostrar aviso de pagamento pendente
        alert('Sua assinatura está inativa. Verifique seu pagamento.');
      } else if (error.code === 'PLAN_UPGRADE_REQUIRED') {
        // Oferecer upgrade
        alert(`Upgrade necessário para: ${error.required_plans.join(' ou ')}`);
      }
    }

    return await response.json();
  } catch (error) {
    console.error('Erro:', error);
  }
}
```

## 5. Limitar Funcionalidades por Plano

### Exemplo: Limitar Número de Profissionais

```python
@professionals_bp.route('/api/professionals', methods=['POST'])
@jwt_required()
@subscription_required()
def create_professional():
    from flask_jwt_extended import get_jwt_identity
    from src.models.subscription import Subscription
    from src.models.professional import Professional

    client_id = get_jwt_identity()
    subscription = Subscription.query.filter_by(client_id=client_id).first()

    # Contar profissionais existentes
    current_count = Professional.query.filter_by(client_id=client_id).count()

    # Verificar limites por plano
    limits = {
        'basic': 3,
        'pro': 10,
        'enterprise': None  # ilimitado
    }

    limit = limits.get(subscription.plan)

    if limit is not None and current_count >= limit:
        return jsonify({
            'error': 'Limite de profissionais atingido',
            'current': current_count,
            'limit': limit,
            'plan': subscription.plan,
            'upgrade_message': 'Faça upgrade para adicionar mais profissionais'
        }), 403

    # Criar profissional...
    return jsonify({'message': 'Profissional criado'}), 201
```

### Exemplo: Limitar Agendamentos Mensais

```python
@appointments_bp.route('/api/appointments', methods=['POST'])
@jwt_required()
@subscription_required()
def create_appointment():
    from flask_jwt_extended import get_jwt_identity
    from src.models.subscription import Subscription
    from src.models.appointment import Appointment
    from datetime import datetime, timedelta
    from sqlalchemy import func

    client_id = get_jwt_identity()
    subscription = Subscription.query.filter_by(client_id=client_id).first()

    # Apenas plano básico tem limite
    if subscription.plan == 'basic':
        # Contar agendamentos do mês atual
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        count = Appointment.query.filter(
            Appointment.client_id == client_id,
            Appointment.created_at >= start_of_month
        ).count()

        if count >= 100:
            return jsonify({
                'error': 'Limite de agendamentos mensais atingido',
                'limit': 100,
                'current': count,
                'plan': 'basic',
                'upgrade_message': 'Faça upgrade para Pro para agendamentos ilimitados'
            }), 403

    # Criar agendamento...
    return jsonify({'message': 'Agendamento criado'}), 201
```

## 6. Adicionar Informações de Assinatura em Respostas

### Incluir Info de Plano na Resposta

```python
@clients_bp.route('/api/clients/me', methods=['GET'])
@jwt_required()
def get_my_info():
    from flask_jwt_extended import get_jwt_identity
    from src.models.client import Client
    from src.models.subscription import Subscription

    client_id = get_jwt_identity()
    client = Client.query.get(client_id)
    subscription = Subscription.query.filter_by(client_id=client_id).first()

    response = client.to_dict()

    # Adicionar informações de assinatura
    if subscription:
        response['subscription'] = {
            'plan': subscription.plan,
            'status': subscription.status,
            'is_active': subscription.is_active()
        }
    else:
        response['subscription'] = None

    return jsonify(response), 200
```

## 7. Webhooks - Ações Personalizadas

### Customizar Comportamento nos Webhooks

```python
# Adicione em subscriptions.py

@subscriptions_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    # ... código existente ...

    if event_type == 'customer.subscription.deleted':
        subscription_id = data_object['id']
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()

        if subscription:
            subscription.status = 'canceled'
            subscription.end_date = datetime.utcnow()

            # AÇÕES PERSONALIZADAS:

            # 1. Notificar cliente por email
            # send_cancellation_email(subscription.client)

            # 2. Arquivar dados do cliente
            # archive_client_data(subscription.client_id)

            # 3. Desativar features premium
            # deactivate_premium_features(subscription.client_id)

            db.session.commit()

    return jsonify({'success': True}), 200
```

## 8. Testes Unitários

### Exemplo de Teste

```python
# tests/test_subscriptions.py
import pytest
from flask_jwt_extended import create_access_token

def test_subscription_required_without_subscription(client, app):
    """Testar acesso sem assinatura"""
    with app.app_context():
        token = create_access_token(identity=1)

    response = client.get(
        '/api/premium-feature',
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 403
    assert response.json['code'] == 'SUBSCRIPTION_REQUIRED'

def test_subscription_required_with_active_subscription(client, app, db):
    """Testar acesso com assinatura ativa"""
    from src.models.subscription import Subscription

    with app.app_context():
        # Criar assinatura de teste
        subscription = Subscription(
            client_id=1,
            plan='pro',
            status='active'
        )
        db.session.add(subscription)
        db.session.commit()

        token = create_access_token(identity=1)

    response = client.get(
        '/api/premium-feature',
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200
```

## Resumo

O sistema de assinaturas oferece:

1. **Decorators simples** para proteger rotas
2. **Verificação flexível** de planos e features
3. **Limites configuráveis** por plano
4. **Webhooks automáticos** para sincronização
5. **Mensagens de erro claras** para o frontend
6. **Fácil customização** e extensão

Para mais detalhes, consulte:
- `SUBSCRIPTION_API.md` - Documentação completa da API
- `SUBSCRIPTION_SETUP.md` - Guia de configuração
- `SUBSCRIPTION_IMPLEMENTATION_GUIDE.md` - Guia de implementação completo

---

**Última atualização:** 2025-10-30
