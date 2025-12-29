# Sistema de Assinaturas SaaS - AgendaMais
## Guia Completo de Implementação

---

## Índice
1. [Configuração Inicial](#1-configuração-inicial)
2. [Backend (Flask)](#2-backend-flask)
3. [Frontend (React)](#3-frontend-react)
4. [Integração Stripe](#4-integração-stripe)
5. [Testes](#5-testes)
6. [Deploy](#6-deploy)

---

## 1. Configuração Inicial

### 1.1 Criar Conta Stripe
1. Acesse https://stripe.com e crie uma conta
2. Ative o modo de teste
3. Anote as chaves:
   - Publishable key (pk_test_...)
   - Secret key (sk_test_...)

### 1.2 Criar Produtos e Preços no Stripe
```bash
# Via Stripe Dashboard ou API
Plano Básico: $29/mês
Plano Pro: $59/mês
Plano Enterprise: $99/mês
```

### 1.3 Variáveis de Ambiente
```bash
# Backend (.env)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=postgresql://...

# Frontend (.env)
VITE_STRIPE_PUBLIC_KEY=pk_test_...
VITE_API_URL=http://localhost:5000
```

---

## 2. Backend (Flask)

### 2.1 Instalação de Dependências
```bash
cd backend
pip install stripe flask-sqlalchemy python-dotenv
```

### 2.2 Criar Tabela Subscriptions

**Arquivo: `backend/migrations/create_subscriptions.sql`**
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    client_id INT REFERENCES clients(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL, -- basic, pro, enterprise
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100) UNIQUE,
    status VARCHAR(20) NOT NULL, -- active, past_due, canceled, trialing
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    trial_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_client_id ON subscriptions(client_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

### 2.3 Model Subscription

**Arquivo: `backend/models/subscription.py`**
```python
from datetime import datetime
from app import db

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    plan = db.Column(db.String(50), nullable=False)
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), nullable=False, default='trialing')
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento
    client = db.relationship('Client', backref=db.backref('subscription', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'plan': self.plan,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'cancel_at_period_end': self.cancel_at_period_end
        }
```

### 2.4 Rotas de Assinatura

**Arquivo: `backend/routes/subscriptions.py`**
```python
import stripe
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.subscription import Subscription
from models.client import Client
from app import db
import os
from datetime import datetime, timedelta

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
subscription_bp = Blueprint('subscriptions', __name__)

# Mapeamento de planos
PLANS = {
    'basic': {'price_id': 'price_...', 'name': 'Básico', 'price': 29},
    'pro': {'price_id': 'price_...', 'name': 'Pro', 'price': 59},
    'enterprise': {'price_id': 'price_...', 'name': 'Enterprise', 'price': 99}
}

@subscription_bp.route('/api/subscribe', methods=['POST'])
@jwt_required()
def create_subscription():
    """Criar nova assinatura"""
    try:
        data = request.json
        client_id = get_jwt_identity()
        plan = data.get('plan')

        if plan not in PLANS:
            return jsonify({'error': 'Plano inválido'}), 400

        client = Client.query.get(client_id)
        if not client:
            return jsonify({'error': 'Cliente não encontrado'}), 404

        # Verificar se já tem assinatura ativa
        existing = Subscription.query.filter_by(
            client_id=client_id,
            status='active'
        ).first()

        if existing:
            return jsonify({'error': 'Já existe uma assinatura ativa'}), 400

        # Criar customer no Stripe
        customer = stripe.Customer.create(
            email=client.email,
            name=client.name,
            metadata={'client_id': client_id}
        )

        # Criar assinatura no Stripe com trial de 7 dias
        stripe_subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': PLANS[plan]['price_id']}],
            trial_period_days=7,
            payment_behavior='default_incomplete',
            payment_settings={
                'save_default_payment_method': 'on_subscription'
            },
            expand=['latest_invoice.payment_intent']
        )

        # Salvar no banco
        trial_end = datetime.utcnow() + timedelta(days=7)
        subscription = Subscription(
            client_id=client_id,
            plan=plan,
            stripe_customer_id=customer.id,
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
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/api/subscribe/status', methods=['GET'])
@jwt_required()
def get_subscription_status():
    """Obter status da assinatura"""
    client_id = get_jwt_identity()

    subscription = Subscription.query.filter_by(client_id=client_id).first()

    if not subscription:
        return jsonify({'has_subscription': False}), 200

    # Atualizar status do Stripe
    if subscription.stripe_subscription_id:
        try:
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            subscription.status = stripe_sub.status
            db.session.commit()
        except stripe.error.StripeError:
            pass

    return jsonify({
        'has_subscription': True,
        'subscription': subscription.to_dict()
    }), 200

@subscription_bp.route('/api/subscribe/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancelar assinatura"""
    try:
        client_id = get_jwt_identity()

        subscription = Subscription.query.filter_by(
            client_id=client_id,
            status='active'
        ).first()

        if not subscription:
            return jsonify({'error': 'Assinatura não encontrada'}), 404

        # Cancelar no Stripe (ao fim do período)
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )

        subscription.cancel_at_period_end = True
        db.session.commit()

        return jsonify({
            'message': 'Assinatura cancelada ao fim do período',
            'subscription': subscription.to_dict()
        }), 200

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@subscription_bp.route('/api/webhook', methods=['POST'])
def stripe_webhook():
    """Webhook do Stripe"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400

    # Processar eventos
    if event['type'] == 'invoice.paid':
        # Pagamento bem-sucedido
        subscription_id = event['data']['object']['subscription']
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()

        if subscription:
            subscription.status = 'active'
            db.session.commit()

    elif event['type'] == 'invoice.payment_failed':
        # Falha no pagamento
        subscription_id = event['data']['object']['subscription']
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()

        if subscription:
            subscription.status = 'past_due'
            db.session.commit()

    elif event['type'] == 'customer.subscription.deleted':
        # Assinatura cancelada
        subscription_id = event['data']['object']['id']
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()

        if subscription:
            subscription.status = 'canceled'
            subscription.end_date = datetime.utcnow()
            db.session.commit()

    elif event['type'] == 'customer.subscription.updated':
        # Assinatura atualizada
        stripe_sub = event['data']['object']
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=stripe_sub['id']
        ).first()

        if subscription:
            subscription.status = stripe_sub['status']
            subscription.cancel_at_period_end = stripe_sub['cancel_at_period_end']
            db.session.commit()

    return jsonify({'success': True}), 200
```

### 2.5 Middleware de Controle de Acesso

**Arquivo: `backend/decorators/subscription_required.py`**
```python
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from models.subscription import Subscription

def subscription_required(plans=None):
    """
    Decorator para verificar assinatura ativa
    Usage:
        @subscription_required()  # Qualquer plano ativo
        @subscription_required(['pro', 'enterprise'])  # Planos específicos
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            client_id = get_jwt_identity()

            subscription = Subscription.query.filter_by(
                client_id=client_id
            ).first()

            # Verificar se tem assinatura
            if not subscription:
                return jsonify({
                    'error': 'Assinatura necessária',
                    'code': 'SUBSCRIPTION_REQUIRED'
                }), 403

            # Verificar status
            if subscription.status not in ['active', 'trialing']:
                return jsonify({
                    'error': 'Assinatura inativa',
                    'code': 'SUBSCRIPTION_INACTIVE',
                    'status': subscription.status
                }), 403

            # Verificar plano específico
            if plans and subscription.plan not in plans:
                return jsonify({
                    'error': 'Plano insuficiente',
                    'code': 'PLAN_UPGRADE_REQUIRED',
                    'current_plan': subscription.plan,
                    'required_plans': plans
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Exemplo de uso:
# @app.route('/api/premium-feature')
# @jwt_required()
# @subscription_required(['pro', 'enterprise'])
# def premium_feature():
#     return jsonify({'message': 'Feature premium'})
```

---

## 3. Frontend (React)

### 3.1 Instalação
```bash
cd frontend
npm install @stripe/stripe-js
```

### 3.2 Context de Assinatura

**Arquivo: `frontend/src/contexts/SubscriptionContext.jsx`**
```javascript
import { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';

const SubscriptionContext = createContext();

export const useSubscription = () => {
  const context = useContext(SubscriptionContext);
  if (!context) {
    throw new Error('useSubscription must be used within SubscriptionProvider');
  }
  return context;
};

export const SubscriptionProvider = ({ children }) => {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSubscription = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/subscribe/status');
      if (response.data.has_subscription) {
        setSubscription(response.data.subscription);
      }
    } catch (error) {
      console.error('Error fetching subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscription();
  }, []);

  const hasActiveSubscription = () => {
    return subscription && ['active', 'trialing'].includes(subscription.status);
  };

  const canAccessFeature = (requiredPlans = []) => {
    if (!hasActiveSubscription()) return false;
    if (requiredPlans.length === 0) return true;
    return requiredPlans.includes(subscription?.plan);
  };

  return (
    <SubscriptionContext.Provider
      value={{
        subscription,
        loading,
        hasActiveSubscription,
        canAccessFeature,
        refreshSubscription: fetchSubscription
      }}
    >
      {children}
    </SubscriptionContext.Provider>
  );
};
```

### 3.3 Componente de Planos

**Arquivo: `frontend/src/components/SubscriptionPlans.jsx`**
```javascript
import { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Check } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../utils/api';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY);

const PLANS = [
  {
    id: 'basic',
    name: 'Básico',
    price: 29,
    features: [
      'Até 100 agendamentos/mês',
      'Até 3 profissionais',
      'Lembretes básicos',
      'Suporte por email'
    ]
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 59,
    popular: true,
    features: [
      'Agendamentos ilimitados',
      'Até 10 profissionais',
      'Lembretes WhatsApp/SMS',
      'Relatórios avançados',
      'Suporte prioritário'
    ]
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 99,
    features: [
      'Tudo do Pro',
      'Profissionais ilimitados',
      'API personalizada',
      'Gestor de conta dedicado',
      'Suporte 24/7'
    ]
  }
];

export default function SubscriptionPlans() {
  const [loading, setLoading] = useState(null);

  const handleSubscribe = async (planId) => {
    try {
      setLoading(planId);

      // Criar assinatura no backend
      const response = await api.post('/api/subscribe', { plan: planId });

      // Redirecionar para Stripe Checkout
      const stripe = await stripePromise;
      const { error } = await stripe.redirectToCheckout({
        sessionId: response.data.session_id
      });

      if (error) {
        toast.error(error.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Erro ao criar assinatura');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-16">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">Escolha seu Plano</h1>
        <p className="text-gray-600">Teste gratuito de 7 dias em todos os planos</p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        {PLANS.map((plan) => (
          <div
            key={plan.id}
            className={`relative bg-white rounded-lg shadow-lg p-8 ${
              plan.popular ? 'ring-2 ring-blue-500' : ''
            }`}
          >
            {plan.popular && (
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                Mais Popular
              </div>
            )}

            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
              <div className="flex items-baseline justify-center gap-2">
                <span className="text-4xl font-bold">R$ {plan.price}</span>
                <span className="text-gray-600">/mês</span>
              </div>
            </div>

            <ul className="space-y-3 mb-8">
              {plan.features.map((feature, index) => (
                <li key={index} className="flex items-start gap-2">
                  <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleSubscribe(plan.id)}
              disabled={loading === plan.id}
              className={`w-full py-3 rounded-lg font-medium transition-colors ${
                plan.popular
                  ? 'bg-blue-500 hover:bg-blue-600 text-white'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {loading === plan.id ? 'Processando...' : 'Começar Teste Gratuito'}
            </button>

            <p className="text-center text-xs text-gray-500 mt-4">
              Cancele a qualquer momento
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 3.4 Componente de Status

**Arquivo: `frontend/src/components/SubscriptionStatus.jsx`**
```javascript
import { useSubscription } from '../contexts/SubscriptionContext';
import { CreditCard, Calendar, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const PLAN_NAMES = {
  basic: 'Básico',
  pro: 'Pro',
  enterprise: 'Enterprise'
};

const STATUS_CONFIG = {
  active: { label: 'Ativa', color: 'green' },
  trialing: { label: 'Teste Gratuito', color: 'blue' },
  past_due: { label: 'Pagamento Pendente', color: 'red' },
  canceled: { label: 'Cancelada', color: 'gray' }
};

export default function SubscriptionStatus() {
  const { subscription, loading } = useSubscription();

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p>Carregando...</p>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-yellow-900 mb-1">
              Nenhuma assinatura ativa
            </h3>
            <p className="text-yellow-800 mb-3">
              Assine um plano para acessar todos os recursos do AgendaMais
            </p>
            <a
              href="/subscription/plans"
              className="inline-block bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Ver Planos
            </a>
          </div>
        </div>
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[subscription.status] || STATUS_CONFIG.active;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Minha Assinatura</h2>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium bg-${statusConfig.color}-100 text-${statusConfig.color}-800`}
        >
          {statusConfig.label}
        </span>
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <CreditCard className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-sm text-gray-600">Plano Atual</p>
            <p className="font-semibold">{PLAN_NAMES[subscription.plan]}</p>
          </div>
        </div>

        {subscription.trial_end && subscription.status === 'trialing' && (
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-600">Término do Teste</p>
              <p className="font-semibold">
                {format(new Date(subscription.trial_end), "dd 'de' MMMM 'às' HH:mm", {
                  locale: ptBR
                })}
              </p>
            </div>
          </div>
        )}

        {subscription.cancel_at_period_end && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 text-sm">
              Sua assinatura será cancelada ao fim do período atual
            </p>
          </div>
        )}

        <div className="flex gap-3 pt-4 border-t">
          <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-lg transition-colors">
            Alterar Plano
          </button>
          <button className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-800 py-2 rounded-lg transition-colors">
            Cancelar Assinatura
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## 4. Integração Stripe

### 4.1 Configurar Webhooks
1. Acesse Stripe Dashboard > Developers > Webhooks
2. Adicione endpoint: `https://seu-dominio.com/api/webhook`
3. Selecione eventos:
   - `invoice.paid`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
4. Copie o webhook secret (whsec_...)

### 4.2 Testar Localmente
```bash
# Instalar Stripe CLI
stripe listen --forward-to localhost:5000/api/webhook

# Em outro terminal
stripe trigger invoice.paid
```

---

## 5. Testes

### 5.1 Backend (pytest)
```python
# tests/test_subscriptions.py
def test_create_subscription(client, auth_headers):
    response = client.post(
        '/api/subscribe',
        json={'plan': 'basic'},
        headers=auth_headers
    )
    assert response.status_code == 201
    assert 'subscription_id' in response.json

def test_get_subscription_status(client, auth_headers):
    response = client.get('/api/subscribe/status', headers=auth_headers)
    assert response.status_code == 200
```

### 5.2 Frontend (Jest)
```javascript
// tests/SubscriptionPlans.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import SubscriptionPlans from '../components/SubscriptionPlans';

test('renders all plans', () => {
  render(<SubscriptionPlans />);
  expect(screen.getByText('Básico')).toBeInTheDocument();
  expect(screen.getByText('Pro')).toBeInTheDocument();
  expect(screen.getByText('Enterprise')).toBeInTheDocument();
});
```

---

## 6. Deploy

### 6.1 Produção
```bash
# Variáveis de ambiente de produção
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 6.2 Checklist Final
- [ ] Webhook configurado e testado
- [ ] Variáveis de ambiente em produção
- [ ] Planos criados no Stripe (modo live)
- [ ] SSL/HTTPS configurado
- [ ] Testes end-to-end realizados
- [ ] Documentação atualizada
- [ ] Monitoramento configurado

---

## Fluxo Completo

```
1. Cliente acessa /subscription/plans
2. Cliente escolhe plano → handleSubscribe()
3. Backend cria customer + subscription no Stripe
4. Backend salva subscription no banco (status: trialing)
5. Cliente usa sistema por 7 dias (trial)
6. Stripe tenta cobrar após trial
7. Se sucesso → webhook invoice.paid → status: active
8. Se falha → webhook invoice.payment_failed → status: past_due
9. Cliente pode cancelar a qualquer momento
10. Webhook customer.subscription.deleted → status: canceled
```

---

## Recursos Adicionais

### Documentação Oficial
- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Webhooks Guide](https://stripe.com/docs/webhooks)

### Cartões de Teste
```
Sucesso: 4242 4242 4242 4242
Falha: 4000 0000 0000 0002
3D Secure: 4000 0027 6000 3184
```

---

**Desenvolvido para AgendaMais**
*Data: 2025-10-30*
