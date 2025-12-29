# Exemplos de Código - Frontend de Assinaturas

## 🎯 Exemplos Práticos para Implementação

Este documento contém exemplos de código prontos para uso no frontend.

---

## 1. Service/API Client

```javascript
// services/subscriptionService.js

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class SubscriptionService {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api/subscriptions`;
  }

  // Helper para adicionar token JWT
  _getHeaders(includeAuth = true) {
    const headers = {
      'Content-Type': 'application/json'
    };

    if (includeAuth) {
      const token = localStorage.getItem('token'); // ou seu método de obter token
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  // Helper para tratar erros
  async _handleResponse(response) {
    const data = await response.json();

    if (!response.ok) {
      throw {
        status: response.status,
        message: data.error || 'Erro desconhecido',
        code: data.code,
        data: data
      };
    }

    return data;
  }

  // GET /api/subscriptions/plans
  async getPlans() {
    const response = await fetch(`${this.baseURL}/plans`, {
      method: 'GET',
      headers: this._getHeaders(false) // Rota pública
    });

    return this._handleResponse(response);
  }

  // POST /api/subscriptions/subscribe
  async subscribe(planId) {
    const response = await fetch(`${this.baseURL}/subscribe`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify({ plan: planId })
    });

    return this._handleResponse(response);
  }

  // GET /api/subscriptions/status
  async getStatus() {
    const response = await fetch(`${this.baseURL}/status`, {
      method: 'GET',
      headers: this._getHeaders()
    });

    return this._handleResponse(response);
  }

  // POST /api/subscriptions/cancel
  async cancel() {
    const response = await fetch(`${this.baseURL}/cancel`, {
      method: 'POST',
      headers: this._getHeaders()
    });

    return this._handleResponse(response);
  }

  // POST /api/subscriptions/reactivate
  async reactivate() {
    const response = await fetch(`${this.baseURL}/reactivate`, {
      method: 'POST',
      headers: this._getHeaders()
    });

    return this._handleResponse(response);
  }
}

export default new SubscriptionService();
```

---

## 2. React Hook para Assinaturas

```javascript
// hooks/useSubscription.js

import { useState, useEffect, useCallback } from 'react';
import subscriptionService from '../services/subscriptionService';

export function useSubscription() {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Buscar status da assinatura
  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await subscriptionService.getStatus();

      if (data.has_subscription) {
        setSubscription(data.subscription);
      } else {
        setSubscription(null);
      }
    } catch (err) {
      setError(err.message);
      console.error('Erro ao buscar assinatura:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Carregar no mount
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Verificar se tem assinatura ativa
  const hasActiveSubscription = useCallback(() => {
    if (!subscription) return false;
    return ['active', 'trialing'].includes(subscription.status);
  }, [subscription]);

  // Verificar se pode acessar feature
  const canAccessFeature = useCallback((requiredPlans = null) => {
    if (!hasActiveSubscription()) return false;
    if (!requiredPlans) return true;
    return requiredPlans.includes(subscription.plan);
  }, [subscription, hasActiveSubscription]);

  // Verificar se está em trial
  const isInTrial = useCallback(() => {
    return subscription?.status === 'trialing';
  }, [subscription]);

  // Verificar se foi cancelado (mas ainda ativo)
  const isCanceled = useCallback(() => {
    return subscription?.cancel_at_period_end === true;
  }, [subscription]);

  // Dias restantes do trial
  const trialDaysRemaining = useCallback(() => {
    if (!subscription?.trial_end) return 0;

    const trialEnd = new Date(subscription.trial_end);
    const now = new Date();
    const diff = trialEnd - now;
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

    return Math.max(0, days);
  }, [subscription]);

  return {
    subscription,
    loading,
    error,
    hasActiveSubscription: hasActiveSubscription(),
    canAccessFeature,
    isInTrial: isInTrial(),
    isCanceled: isCanceled(),
    trialDaysRemaining: trialDaysRemaining(),
    refresh: fetchStatus
  };
}
```

---

## 3. Componente de Planos

```jsx
// components/SubscriptionPlans.jsx

import React, { useState, useEffect } from 'react';
import subscriptionService from '../services/subscriptionService';
import PaymentModal from './PaymentModal';

function SubscriptionPlans() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  useEffect(() => {
    loadPlans();
  }, []);

  async function loadPlans() {
    try {
      const data = await subscriptionService.getPlans();
      setPlans(data.plans);
    } catch (error) {
      console.error('Erro ao carregar planos:', error);
    } finally {
      setLoading(false);
    }
  }

  function handleSelectPlan(plan) {
    setSelectedPlan(plan);
    setShowPaymentModal(true);
  }

  if (loading) {
    return <div>Carregando planos...</div>;
  }

  return (
    <div className="subscription-plans">
      <h1>Escolha seu Plano</h1>

      <div className="plans-grid">
        {plans.map(plan => (
          <div
            key={plan.id}
            className={`plan-card ${plan.id === 'pro' ? 'recommended' : ''}`}
          >
            {plan.id === 'pro' && (
              <div className="badge">Recomendado</div>
            )}

            <h2>{plan.name}</h2>

            <div className="price">
              <span className="currency">R$</span>
              <span className="amount">{plan.price}</span>
              <span className="period">/mês</span>
            </div>

            <ul className="features">
              {plan.features.map((feature, index) => (
                <li key={index}>
                  <span className="check">✓</span>
                  {feature}
                </li>
              ))}
            </ul>

            <button
              className="btn-subscribe"
              onClick={() => handleSelectPlan(plan)}
            >
              Assinar {plan.name}
            </button>

            <p className="trial-info">
              7 dias grátis, depois R$ {plan.price}/mês
            </p>
          </div>
        ))}
      </div>

      {showPaymentModal && (
        <PaymentModal
          plan={selectedPlan}
          onClose={() => setShowPaymentModal(false)}
        />
      )}
    </div>
  );
}

export default SubscriptionPlans;
```

---

## 4. Modal de Pagamento com Stripe

```jsx
// components/PaymentModal.jsx

import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import subscriptionService from '../services/subscriptionService';

// Inicializar Stripe
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLIC_KEY);

// Estilos do CardElement
const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      color: '#32325d',
      fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
      fontSmoothing: 'antialiased',
      fontSize: '16px',
      '::placeholder': {
        color: '#aab7c4'
      }
    },
    invalid: {
      color: '#fa755a',
      iconColor: '#fa755a'
    }
  }
};

// Componente interno do formulário
function CheckoutForm({ plan, onSuccess, onError }) {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setProcessing(true);
    setErrorMessage('');

    try {
      // 1. Criar assinatura no backend
      const subscriptionData = await subscriptionService.subscribe(plan.id);

      // 2. Confirmar pagamento com Stripe
      const { error, paymentIntent } = await stripe.confirmCardPayment(
        subscriptionData.client_secret,
        {
          payment_method: {
            card: elements.getElement(CardElement),
            billing_details: {
              // Você pode adicionar mais dados aqui
              // name: userName,
              // email: userEmail
            }
          }
        }
      );

      if (error) {
        setErrorMessage(error.message);
        onError(error);
      } else if (paymentIntent.status === 'succeeded') {
        onSuccess(subscriptionData);
      }
    } catch (error) {
      setErrorMessage(error.message);
      onError(error);
    } finally {
      setProcessing(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="payment-form">
      <div className="plan-summary">
        <h3>{plan.name}</h3>
        <p className="price">R$ {plan.price}/mês</p>
        <p className="trial">7 dias grátis, depois cobrado mensalmente</p>
      </div>

      <div className="card-element-wrapper">
        <label>Dados do Cartão</label>
        <CardElement options={CARD_ELEMENT_OPTIONS} />
      </div>

      {errorMessage && (
        <div className="error-message">
          {errorMessage}
        </div>
      )}

      <button
        type="submit"
        disabled={!stripe || processing}
        className="btn-pay"
      >
        {processing ? 'Processando...' : 'Confirmar Assinatura'}
      </button>

      <p className="secure-info">
        🔒 Pagamento seguro processado pelo Stripe
      </p>
    </form>
  );
}

// Componente principal do modal
function PaymentModal({ plan, onClose }) {
  function handleSuccess(subscriptionData) {
    alert('Assinatura criada com sucesso! Você tem 7 dias grátis.');
    window.location.href = '/dashboard';
  }

  function handleError(error) {
    console.error('Erro no pagamento:', error);
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="btn-close" onClick={onClose}>×</button>

        <Elements stripe={stripePromise}>
          <CheckoutForm
            plan={plan}
            onSuccess={handleSuccess}
            onError={handleError}
          />
        </Elements>
      </div>
    </div>
  );
}

export default PaymentModal;
```

---

## 5. Componente de Status da Assinatura

```jsx
// components/SubscriptionStatus.jsx

import React, { useState } from 'react';
import { useSubscription } from '../hooks/useSubscription';
import subscriptionService from '../services/subscriptionService';

function SubscriptionStatus() {
  const {
    subscription,
    loading,
    hasActiveSubscription,
    isInTrial,
    isCanceled,
    trialDaysRemaining,
    refresh
  } = useSubscription();

  const [canceling, setCanceling] = useState(false);
  const [reactivating, setReactivating] = useState(false);

  if (loading) {
    return <div>Carregando...</div>;
  }

  if (!subscription) {
    return (
      <div className="no-subscription">
        <h2>Você não tem uma assinatura ativa</h2>
        <p>Escolha um plano para começar!</p>
        <a href="/subscription/plans" className="btn-primary">
          Ver Planos
        </a>
      </div>
    );
  }

  async function handleCancel() {
    if (!window.confirm('Tem certeza que deseja cancelar? Você manterá acesso até o fim do período pago.')) {
      return;
    }

    try {
      setCanceling(true);
      await subscriptionService.cancel();
      await refresh();
      alert('Assinatura cancelada. Você manterá acesso até o fim do período.');
    } catch (error) {
      alert('Erro ao cancelar: ' + error.message);
    } finally {
      setCanceling(false);
    }
  }

  async function handleReactivate() {
    try {
      setReactivating(true);
      await subscriptionService.reactivate();
      await refresh();
      alert('Assinatura reativada com sucesso!');
    } catch (error) {
      alert('Erro ao reativar: ' + error.message);
    } finally {
      setReactivating(false);
    }
  }

  function getStatusBadge() {
    const statusMap = {
      'trialing': { text: 'Trial', color: 'yellow' },
      'active': { text: 'Ativo', color: 'green' },
      'past_due': { text: 'Pendente', color: 'orange' },
      'canceled': { text: 'Cancelado', color: 'red' }
    };

    const status = statusMap[subscription.status] || { text: subscription.status, color: 'gray' };

    return (
      <span className={`badge badge-${status.color}`}>
        {status.text}
      </span>
    );
  }

  function getPlanName() {
    const planNames = {
      'basic': 'Básico',
      'pro': 'Pro',
      'enterprise': 'Enterprise'
    };
    return planNames[subscription.plan] || subscription.plan;
  }

  function getPlanPrice() {
    const prices = {
      'basic': 29,
      'pro': 59,
      'enterprise': 99
    };
    return prices[subscription.plan] || 0;
  }

  return (
    <div className="subscription-status">
      <div className="status-header">
        <h2>Minha Assinatura</h2>
        {getStatusBadge()}
      </div>

      <div className="status-details">
        <div className="detail-item">
          <label>Plano:</label>
          <span className="value">{getPlanName()} - R$ {getPlanPrice()}/mês</span>
        </div>

        {isInTrial && (
          <div className="detail-item trial-info">
            <label>Trial:</label>
            <span className="value">
              {trialDaysRemaining} dias restantes
            </span>
          </div>
        )}

        <div className="detail-item">
          <label>Status:</label>
          <span className="value">{subscription.status}</span>
        </div>

        {subscription.start_date && (
          <div className="detail-item">
            <label>Desde:</label>
            <span className="value">
              {new Date(subscription.start_date).toLocaleDateString('pt-BR')}
            </span>
          </div>
        )}
      </div>

      {/* Alerta se está cancelado */}
      {isCanceled && (
        <div className="alert alert-warning">
          <strong>Assinatura cancelada</strong>
          <p>Você manterá acesso até o fim do período pago.</p>
        </div>
      )}

      {/* Alerta se está em atraso */}
      {subscription.status === 'past_due' && (
        <div className="alert alert-danger">
          <strong>Pagamento pendente</strong>
          <p>Atualize seu método de pagamento para continuar com acesso.</p>
          <button className="btn-danger">Atualizar Cartão</button>
        </div>
      )}

      {/* Botões de ação */}
      <div className="actions">
        {hasActiveSubscription && !isCanceled && (
          <button
            className="btn-danger"
            onClick={handleCancel}
            disabled={canceling}
          >
            {canceling ? 'Cancelando...' : 'Cancelar Assinatura'}
          </button>
        )}

        {isCanceled && (
          <button
            className="btn-success"
            onClick={handleReactivate}
            disabled={reactivating}
          >
            {reactivating ? 'Reativando...' : 'Reativar Assinatura'}
          </button>
        )}
      </div>
    </div>
  );
}

export default SubscriptionStatus;
```

---

## 6. Guard para Features Premium

```jsx
// components/SubscriptionGuard.jsx

import React from 'react';
import { useSubscription } from '../hooks/useSubscription';
import { Navigate } from 'react-router-dom';

function SubscriptionGuard({
  children,
  requiredPlans = null,
  fallback = null,
  redirectTo = '/subscription/plans'
}) {
  const { subscription, loading, hasActiveSubscription, canAccessFeature } = useSubscription();

  if (loading) {
    return <div>Carregando...</div>;
  }

  // Sem assinatura
  if (!hasActiveSubscription) {
    if (fallback) {
      return fallback;
    }
    return <Navigate to={redirectTo} />;
  }

  // Assinatura existe mas plano insuficiente
  if (requiredPlans && !canAccessFeature(requiredPlans)) {
    return (
      <div className="upgrade-required">
        <h2>Upgrade Necessário</h2>
        <p>Esta funcionalidade está disponível apenas para planos:</p>
        <ul>
          {requiredPlans.map(plan => (
            <li key={plan}>{plan}</li>
          ))}
        </ul>
        <p>Seu plano atual: <strong>{subscription.plan}</strong></p>
        <a href="/subscription/plans" className="btn-primary">
          Fazer Upgrade
        </a>
      </div>
    );
  }

  return children;
}

export default SubscriptionGuard;

// Exemplo de uso:
/*
import SubscriptionGuard from './components/SubscriptionGuard';

// Proteger rota inteira
<Route path="/advanced-reports" element={
  <SubscriptionGuard requiredPlans={['pro', 'enterprise']}>
    <AdvancedReports />
  </SubscriptionGuard>
} />

// Proteger componente específico
<SubscriptionGuard requiredPlans={['pro', 'enterprise']}>
  <PremiumFeature />
</SubscriptionGuard>
*/
```

---

## 7. Banner de Trial Expirando

```jsx
// components/TrialExpiringBanner.jsx

import React from 'react';
import { useSubscription } from '../hooks/useSubscription';

function TrialExpiringBanner() {
  const { isInTrial, trialDaysRemaining } = useSubscription();

  // Não mostrar se não está em trial ou se ainda faltam mais de 3 dias
  if (!isInTrial || trialDaysRemaining > 3) {
    return null;
  }

  function getBannerClass() {
    if (trialDaysRemaining === 0) return 'banner-danger';
    if (trialDaysRemaining <= 1) return 'banner-warning';
    return 'banner-info';
  }

  function getMessage() {
    if (trialDaysRemaining === 0) {
      return 'Seu trial expira hoje! Adicione um método de pagamento agora.';
    }
    if (trialDaysRemaining === 1) {
      return 'Seu trial expira amanhã! Adicione um método de pagamento.';
    }
    return `Seu trial expira em ${trialDaysRemaining} dias. Adicione um método de pagamento.`;
  }

  return (
    <div className={`trial-banner ${getBannerClass()}`}>
      <span className="icon">⏰</span>
      <span className="message">{getMessage()}</span>
      <button className="btn-action">
        Adicionar Cartão
      </button>
    </div>
  );
}

export default TrialExpiringBanner;
```

---

## 8. Configuração do package.json

```json
{
  "dependencies": {
    "@stripe/stripe-js": "^2.1.0",
    "@stripe/react-stripe-js": "^2.3.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  }
}
```

Instalar:
```bash
npm install @stripe/stripe-js @stripe/react-stripe-js
```

---

## 9. Variáveis de Ambiente (.env)

```env
# Stripe
REACT_APP_STRIPE_PUBLIC_KEY=pk_test_...

# API
REACT_APP_API_URL=http://localhost:5000
```

---

## 10. Estilo CSS Base (Exemplo)

```css
/* styles/subscription.css */

.subscription-plans {
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  margin-top: 40px;
}

.plan-card {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 30px;
  position: relative;
  transition: transform 0.2s, box-shadow 0.2s;
}

.plan-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.plan-card.recommended {
  border-color: #4CAF50;
  box-shadow: 0 5px 20px rgba(76, 175, 80, 0.2);
}

.plan-card .badge {
  position: absolute;
  top: -15px;
  right: 20px;
  background: #4CAF50;
  color: white;
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  margin: 20px 0;
}

.price .currency {
  font-size: 20px;
  margin-right: 5px;
}

.price .amount {
  font-size: 48px;
  font-weight: bold;
}

.price .period {
  font-size: 16px;
  color: #666;
  margin-left: 5px;
}

.features {
  list-style: none;
  padding: 0;
  margin: 30px 0;
}

.features li {
  padding: 10px 0;
  display: flex;
  align-items: center;
}

.features .check {
  color: #4CAF50;
  font-weight: bold;
  margin-right: 10px;
}

.btn-subscribe {
  width: 100%;
  padding: 15px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-subscribe:hover {
  background: #45a049;
}

.trial-info {
  text-align: center;
  margin-top: 15px;
  font-size: 14px;
  color: #666;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 40px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  position: relative;
}

.btn-close {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 30px;
  cursor: pointer;
  color: #999;
}

/* Stripe Card Element */
.card-element-wrapper {
  margin: 20px 0;
}

.card-element-wrapper label {
  display: block;
  margin-bottom: 10px;
  font-weight: bold;
}

/* Status badges */
.badge {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.badge-green {
  background: #4CAF50;
  color: white;
}

.badge-yellow {
  background: #FFC107;
  color: black;
}

.badge-orange {
  background: #FF9800;
  color: white;
}

.badge-red {
  background: #f44336;
  color: white;
}

/* Alerts */
.alert {
  padding: 15px;
  border-radius: 8px;
  margin: 20px 0;
}

.alert-warning {
  background: #FFF3CD;
  border: 1px solid #FFC107;
  color: #856404;
}

.alert-danger {
  background: #F8D7DA;
  border: 1px solid #f44336;
  color: #721c24;
}

/* Trial Banner */
.trial-banner {
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.trial-banner.banner-info {
  background: #D1ECF1;
  border: 1px solid #17A2B8;
}

.trial-banner.banner-warning {
  background: #FFF3CD;
  border: 1px solid #FFC107;
}

.trial-banner.banner-danger {
  background: #F8D7DA;
  border: 1px solid #f44336;
}

.trial-banner .icon {
  font-size: 24px;
}

.trial-banner .message {
  flex: 1;
}

.trial-banner .btn-action {
  padding: 8px 20px;
  background: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}
```

---

## Pronto para Usar!

Estes exemplos cobrem todos os casos de uso principais. Ajuste conforme necessário para seu projeto específico.
