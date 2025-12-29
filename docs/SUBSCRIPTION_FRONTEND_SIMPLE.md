# Documentação de Assinaturas - Frontend

## 🗄️ Model Subscription

```javascript
{
  id: number,
  client_id: number,
  plan: string,                      // "basic", "pro", "enterprise"
  stripe_customer_id: string,
  stripe_subscription_id: string,
  status: string,                    // "trialing", "active", "past_due", "canceled"
  start_date: string,                // ISO 8601: "2025-11-06T10:30:00"
  end_date: string | null,
  trial_end: string | null,          // ISO 8601: "2025-11-13T10:30:00"
  cancel_at_period_end: boolean,
  created_at: string,                // ISO 8601
  updated_at: string                 // ISO 8601
}
```

## 📍 Rotas da API

Base URL: `http://localhost:5000/api/subscriptions`

---

### 1. GET `/plans`
**Descrição:** Lista os planos disponíveis

**Autenticação:** Não requer

**Enviar:** Nada

**Retorno:**
```json
{
  "plans": [
    {
      "id": "basic",
      "name": "Básico",
      "price": 29,
      "features": ["Até 100 agendamentos/mês", "Até 3 profissionais", ...]
    },
    {
      "id": "pro",
      "name": "Pro",
      "price": 59,
      "features": [...]
    },
    {
      "id": "enterprise",
      "name": "Enterprise",
      "price": 99,
      "features": [...]
    }
  ]
}
```

---

### 2. POST `/subscribe`
**Descrição:** Cria uma nova assinatura

**Autenticação:** JWT Bearer Token

**Enviar:**
```json
{
  "plan": "pro"
}
```

**Campos obrigatórios:**
- `plan` (string): "basic", "pro" ou "enterprise"

**Retorno (201):**
```json
{
  "subscription_id": 1,
  "stripe_subscription_id": "sub_1aBcD3FgHiJkLmNo",
  "client_secret": "pi_1aBcD3FgHiJkLmNo_secret_XyZ123AbC456",
  "status": "trialing",
  "trial_end": "2025-11-13T10:30:00"
}
```

**⚠️ IMPORTANTE:** Use o `client_secret` retornado para confirmar o pagamento com Stripe Elements:
```javascript
stripe.confirmCardPayment(client_secret, { payment_method: {...} })
```

**Erros possíveis:**
- `400` - "Plano inválido"
- `400` - "Já existe uma assinatura ativa"
- `404` - "Cliente não encontrado"

---

### 3. GET `/status`
**Descrição:** Retorna o status da assinatura do cliente logado

**Autenticação:** JWT Bearer Token

**Enviar:** Nada

**Retorno com assinatura (200):**
```json
{
  "has_subscription": true,
  "subscription": {
    "id": 1,
    "client_id": 1,
    "plan": "pro",
    "stripe_customer_id": "cus_...",
    "stripe_subscription_id": "sub_...",
    "status": "active",
    "start_date": "2025-10-30T10:30:00",
    "end_date": null,
    "trial_end": "2025-11-06T10:30:00",
    "cancel_at_period_end": false,
    "created_at": "2025-10-30T10:30:00",
    "updated_at": "2025-10-30T10:30:00"
  }
}
```

**Retorno sem assinatura (200):**
```json
{
  "has_subscription": false
}
```

---

### 4. POST `/cancel`
**Descrição:** Cancela a assinatura ao final do período (não é imediato)

**Autenticação:** JWT Bearer Token

**Enviar:** Nada

**Retorno (200):**
```json
{
  "message": "Assinatura será cancelada ao fim do período",
  "subscription": {
    "id": 1,
    "status": "active",
    "cancel_at_period_end": true,
    ...
  }
}
```

**⚠️ IMPORTANTE:** O usuário mantém acesso até o fim do período pago. Apenas `cancel_at_period_end` muda para `true`.

**Erros possíveis:**
- `404` - "Assinatura não encontrada"
- `400` - "Assinatura não está ativa"

---

### 5. POST `/reactivate`
**Descrição:** Reativa uma assinatura que foi cancelada (mas ainda está ativa)

**Autenticação:** JWT Bearer Token

**Enviar:** Nada

**Retorno (200):**
```json
{
  "message": "Assinatura reativada com sucesso",
  "subscription": {
    "id": 1,
    "status": "active",
    "cancel_at_period_end": false,
    ...
  }
}
```

**Erros possíveis:**
- `404` - "Assinatura não encontrada"
- `400` - "Assinatura não está marcada para cancelamento"

---

## 🔐 Autenticação

Adicione o token JWT no header de todas as requisições (exceto `/plans`):

```
Authorization: Bearer {seu_token_jwt}
```

---

## 📊 Status da Assinatura

| Status | Descrição | Usuário tem acesso? |
|--------|-----------|---------------------|
| `trialing` | Período de teste (7 dias gratuitos) | ✅ Sim |
| `active` | Assinatura ativa e paga | ✅ Sim |
| `past_due` | Pagamento em atraso | ⚠️ Limitado |
| `canceled` | Assinatura cancelada | ❌ Não |

---

## 🎯 Fluxo Básico de Implementação

### 1. Exibir Planos
```
GET /api/subscriptions/plans
→ Mostrar cards com os 3 planos
```

### 2. Criar Assinatura
```
POST /api/subscriptions/subscribe
Body: { "plan": "pro" }
→ Recebe client_secret
→ Usar Stripe.js para confirmar pagamento
```

### 3. Verificar Status
```
GET /api/subscriptions/status
→ Verificar se has_subscription = true
→ Mostrar status e plano atual
```

### 4. Cancelar
```
POST /api/subscriptions/cancel
→ Assinatura continua ativa até fim do período
→ cancel_at_period_end = true
```

### 5. Reativar
```
POST /api/subscriptions/reactivate
→ Remove flag de cancelamento
→ cancel_at_period_end = false
```

---

## 💳 Integração Stripe (Frontend)

### 1. Instalar biblioteca
```bash
npm install @stripe/stripe-js
```

### 2. Inicializar
```javascript
import { loadStripe } from '@stripe/stripe-js';
const stripe = await loadStripe('pk_test_...');
```

### 3. Confirmar Pagamento
```javascript
// Após criar assinatura no backend
const { client_secret } = await fetch('/api/subscriptions/subscribe', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ plan: 'pro' })
}).then(r => r.json());

// Confirmar com Stripe
const result = await stripe.confirmCardPayment(client_secret, {
  payment_method: {
    card: cardElement, // Stripe Elements
    billing_details: { name: 'Cliente' }
  }
});

if (result.error) {
  // Erro no pagamento
  console.error(result.error.message);
} else {
  // Sucesso! Assinatura criada
  console.log('Trial de 7 dias iniciado!');
}
```

### 4. Cartões de Teste
- **Sucesso:** `4242 4242 4242 4242`
- **Falha:** `4000 0000 0000 0002`
- CVV: qualquer 3 dígitos
- Data: qualquer data futura

---

## 📝 Resumo

**O que o frontend precisa fazer:**

1. **Listar planos:** `GET /plans` (sem autenticação)
2. **Criar assinatura:** `POST /subscribe` com `{ "plan": "pro" }` → recebe `client_secret`
3. **Confirmar pagamento:** Usar Stripe.js com o `client_secret`
4. **Verificar status:** `GET /status` para saber se tem assinatura ativa
5. **Cancelar:** `POST /cancel` (mantém acesso até fim do período)
6. **Reativar:** `POST /reactivate` (se cancelou antes)

**Variáveis de ambiente necessárias:**
- `STRIPE_PUBLIC_KEY`: pk_test_... (chave pública do Stripe)
- `API_URL`: http://localhost:5000

**Período de trial:**
- Toda nova assinatura ganha 7 dias gratuitos
- Após 7 dias, Stripe cobra automaticamente
- Webhooks atualizam o status no backend

---

**Documentação completa em:** `SUBSCRIPTION_API.md`
