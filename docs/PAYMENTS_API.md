# API de Pagamentos/Faturamento

Esta documentação descreve a funcionalidade de rastreamento de pagamentos integrada com o Stripe.

## Visão Geral

O sistema registra automaticamente todos os pagamentos processados pelo Stripe através de webhooks. Os dados ficam disponíveis no dashboard do super admin para consulta e análise.

---

## Modelo de Dados

### Tabela `payments`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único do pagamento |
| `subscription_id` | Integer | FK para tabela subscriptions |
| `user_id` | Integer | FK para tabela users |
| `stripe_invoice_id` | String(100) | ID da invoice no Stripe (único) |
| `stripe_payment_intent_id` | String(100) | ID do payment intent no Stripe |
| `amount` | Decimal(10,2) | Valor do pagamento em reais |
| `currency` | String(3) | Moeda (padrão: 'brl') |
| `status` | String(50) | Status do pagamento ('paid', 'pending', 'failed') |
| `paid_at` | DateTime | Data/hora do pagamento |
| `period_start` | DateTime | Início do período de cobrança |
| `period_end` | DateTime | Fim do período de cobrança |
| `created_at` | DateTime | Data de criação do registro |
| `updated_at` | DateTime | Data de atualização do registro |

---

## Endpoints da API

### Listar Pagamentos

```
GET /api/superadmin/payments
```

**Autenticação:** Bearer Token (admin/superadmin)

**Parâmetros de Query:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `page` | integer | 1 | Número da página |
| `limit` | integer | 20 | Itens por página |
| `status` | string | 'all' | Filtrar por status: 'paid', 'pending', 'failed', 'all' |
| `start_date` | string | - | Data inicial (YYYY-MM-DD) |
| `end_date` | string | - | Data final (YYYY-MM-DD) |
| `sort_by` | string | 'paid_at' | Ordenar por: 'paid_at', 'amount', 'created_at' |
| `sort_order` | string | 'desc' | Ordem: 'asc', 'desc' |

**Resposta:**

```json
{
  "payments": [
    {
      "id": 1,
      "stripe_invoice_id": "in_1234567890",
      "stripe_payment_intent_id": "pi_1234567890",
      "amount": 59.00,
      "currency": "brl",
      "status": "paid",
      "paid_at": "2024-01-15T10:30:00",
      "period_start": "2024-01-15T00:00:00",
      "period_end": "2024-02-15T00:00:00",
      "created_at": "2024-01-15T10:30:00",
      "company": {
        "id": 1,
        "name": "Empresa XYZ",
        "email": "contato@empresa.com"
      },
      "subscription": {
        "id": 1,
        "plan": "pro",
        "status": "active"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### Detalhes do Pagamento

```
GET /api/superadmin/payments/{payment_id}
```

**Autenticação:** Bearer Token (admin/superadmin)

**Resposta:**

```json
{
  "id": 1,
  "stripe_invoice_id": "in_1234567890",
  "stripe_payment_intent_id": "pi_1234567890",
  "amount": 59.00,
  "currency": "brl",
  "status": "paid",
  "paid_at": "2024-01-15T10:30:00",
  "period_start": "2024-01-15T00:00:00",
  "period_end": "2024-02-15T00:00:00",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "company": {
    "id": 1,
    "name": "Empresa XYZ",
    "email": "contato@empresa.com",
    "company_name": "Empresa XYZ LTDA"
  },
  "subscription": {
    "id": 1,
    "plan": "pro",
    "status": "active",
    "stripe_subscription_id": "sub_1234567890"
  }
}
```

---

### Estatísticas de Faturamento

```
GET /api/superadmin/payments/stats
```

**Autenticação:** Bearer Token (admin/superadmin)

**Parâmetros de Query:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `months` | integer | 12 | Número de meses para análise |

**Resposta:**

```json
{
  "total_revenue": 15000.00,
  "total_payments": 250,
  "last_30_days": {
    "revenue": 1500.00,
    "count": 25
  },
  "monthly": [
    {
      "month": "2024-01",
      "revenue": 1500.00,
      "count": 25
    },
    {
      "month": "2023-12",
      "revenue": 1400.00,
      "count": 23
    }
  ]
}
```

---

## Webhook do Stripe

O sistema processa automaticamente o evento `invoice.paid` do Stripe.

### Endpoint do Webhook

```
POST /api/subscriptions/webhook
```

### Dados Capturados

Quando o Stripe envia um evento `invoice.paid`, o sistema:

1. Localiza a subscription pelo `stripe_subscription_id`
2. Atualiza o status da subscription para `active`
3. Cria um registro na tabela `payments` com:
   - `stripe_invoice_id` - ID da invoice
   - `stripe_payment_intent_id` - ID do payment intent
   - `amount` - Valor pago (convertido de centavos para reais)
   - `currency` - Moeda
   - `paid_at` - Data do pagamento
   - `period_start` / `period_end` - Período de cobrança

### Configuração do Webhook no Stripe

1. Acesse o Dashboard do Stripe > Developers > Webhooks
2. Adicione o endpoint: `https://seu-dominio.com/api/subscriptions/webhook`
3. Selecione os eventos:
   - `invoice.paid`
   - `invoice.payment_failed`
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copie o Webhook Secret e configure em `STRIPE_WEBHOOK_SECRET`

---

## Frontend - Dashboard de Faturamento

### Acesso

- **Rota:** `/admin/payments`
- **Permissão:** Usuários com role `admin` ou `superadmin`
- **Menu:** Link "Faturamento" aparece automaticamente para admins

### Funcionalidades

1. **Cards de Estatísticas**
   - Receita total
   - Receita dos últimos 30 dias
   - Total de pagamentos
   - Pagamentos dos últimos 30 dias

2. **Filtros**
   - Status (Todos, Pago, Pendente, Falhou)
   - Data inicial
   - Data final

3. **Tabela de Pagamentos**
   - Empresa (nome e email)
   - Plano
   - Valor
   - Status
   - Data do pagamento
   - Período de cobrança

4. **Gráfico de Receita Mensal**
   - Visualização dos últimos 6 meses

---

## Arquivos Relacionados

### Backend

| Arquivo | Descrição |
|---------|-----------|
| `src/models/payment.py` | Modelo Payment |
| `src/models/__init__.py` | Export do modelo |
| `src/app/main/subscription/subscriptions.py` | Webhook handler |
| `src/app/main/superadmin/superadmin.py` | Endpoints de pagamentos |

### Frontend

| Arquivo | Descrição |
|---------|-----------|
| `src/components/AdminPayments.jsx` | Página de faturamento |
| `src/components/Layout.jsx` | Navegação com link para admins |
| `src/App.jsx` | Rota /admin/payments |
| `src/contexts/AuthContext.jsx` | Helper isAdmin() |

---

## Variáveis de Ambiente

```env
# Stripe
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_BASIC=price_xxx
STRIPE_PRICE_PRO=price_xxx
STRIPE_PRICE_ENTERPRISE=price_xxx
```

---

## Testando Localmente

### Com Stripe CLI

```bash
# Instalar Stripe CLI
# Windows: scoop install stripe

# Login
stripe login

# Encaminhar webhooks para localhost
stripe listen --forward-to localhost:5000/api/subscriptions/webhook

# Em outro terminal, simular pagamento
stripe trigger invoice.paid
```

### Verificar no Dashboard

1. Faça login como admin
2. Acesse "Faturamento" no menu
3. Verifique se o pagamento aparece na listagem
