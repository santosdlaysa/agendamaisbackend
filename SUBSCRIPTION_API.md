# API de Assinaturas - AgendaMais

## Visão Geral

Sistema de assinaturas SaaS integrado com Stripe para gerenciar planos de assinatura do AgendaMais.

## Planos Disponíveis

### Básico - R$ 29/mês
- Até 100 agendamentos/mês
- Até 3 profissionais
- Lembretes básicos
- Suporte por email

### Pro - R$ 59/mês
- Agendamentos ilimitados
- Até 10 profissionais
- Lembretes WhatsApp/SMS
- Relatórios avançados
- Suporte prioritário

### Enterprise - R$ 99/mês
- Tudo do Pro
- Profissionais ilimitados
- API personalizada
- Gestor de conta dedicado
- Suporte 24/7

## Endpoints da API

### 1. Listar Planos

```http
GET /api/subscriptions/plans
```

**Resposta:**
```json
{
  "plans": [
    {
      "id": "basic",
      "name": "Básico",
      "price": 29,
      "features": [...]
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

### 2. Criar Assinatura

```http
POST /api/subscriptions/subscribe
Authorization: Bearer {token}
Content-Type: application/json

{
  "plan": "pro"
}
```

**Resposta:**
```json
{
  "subscription_id": 1,
  "stripe_subscription_id": "sub_xxxxx",
  "client_secret": "pi_xxxxx_secret_xxxxx",
  "status": "trialing",
  "trial_end": "2025-11-06T10:30:00"
}
```

### 3. Status da Assinatura

```http
GET /api/subscriptions/status
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "has_subscription": true,
  "subscription": {
    "id": 1,
    "client_id": 1,
    "plan": "pro",
    "status": "active",
    "start_date": "2025-10-30T10:30:00",
    "trial_end": "2025-11-06T10:30:00",
    "cancel_at_period_end": false
  }
}
```

### 4. Cancelar Assinatura

```http
POST /api/subscriptions/cancel
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "message": "Assinatura será cancelada ao fim do período",
  "subscription": {
    "id": 1,
    "status": "active",
    "cancel_at_period_end": true
  }
}
```

### 5. Reativar Assinatura

```http
POST /api/subscriptions/reactivate
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "message": "Assinatura reativada com sucesso",
  "subscription": {
    "id": 1,
    "status": "active",
    "cancel_at_period_end": false
  }
}
```

### 6. Webhook do Stripe

```http
POST /api/subscriptions/webhook
Stripe-Signature: {signature}
```

**Eventos Suportados:**
- `invoice.paid` - Pagamento bem-sucedido
- `invoice.payment_failed` - Falha no pagamento
- `customer.subscription.deleted` - Assinatura cancelada
- `customer.subscription.updated` - Assinatura atualizada
- `customer.subscription.trial_will_end` - Trial terminando

## Controle de Acesso

### Usando o Decorator

```python
from flask_jwt_extended import jwt_required
from src.decorators import subscription_required

# Qualquer plano ativo
@app.route('/api/feature')
@jwt_required()
@subscription_required()
def feature():
    return jsonify({'message': 'Feature disponível'})

# Apenas planos específicos
@app.route('/api/premium-feature')
@jwt_required()
@subscription_required(['pro', 'enterprise'])
def premium_feature():
    return jsonify({'message': 'Feature premium'})
```

### Usando o Check de Features

```python
from src.decorators import check_feature_access

@app.route('/api/advanced-reports')
@jwt_required()
@check_feature_access('advanced_reports')
def advanced_reports():
    return jsonify({'report': 'data'})
```

## Status de Assinatura

- `trialing` - Período de teste gratuito (7 dias)
- `active` - Assinatura ativa e paga
- `past_due` - Pagamento atrasado
- `canceled` - Assinatura cancelada

## Códigos de Erro

### 403 - Forbidden

**SUBSCRIPTION_REQUIRED**
```json
{
  "error": "Assinatura necessária para acessar este recurso",
  "code": "SUBSCRIPTION_REQUIRED"
}
```

**SUBSCRIPTION_INACTIVE**
```json
{
  "error": "Assinatura inativa",
  "code": "SUBSCRIPTION_INACTIVE",
  "status": "past_due"
}
```

**PLAN_UPGRADE_REQUIRED**
```json
{
  "error": "Plano insuficiente",
  "code": "PLAN_UPGRADE_REQUIRED",
  "current_plan": "basic",
  "required_plans": ["pro", "enterprise"]
}
```

## Fluxo de Assinatura

1. Cliente escolhe um plano em `/api/subscriptions/plans`
2. Cliente cria assinatura em `/api/subscriptions/subscribe`
3. Sistema cria customer e subscription no Stripe
4. Cliente recebe 7 dias de trial gratuito
5. Após trial, Stripe tenta cobrar automaticamente
6. Webhooks atualizam o status da assinatura no banco

## Configuração

### Variáveis de Ambiente

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

### Migração do Banco de Dados

Execute o script SQL:
```bash
psql -U postgres -d agendamais < migrations/create_subscriptions.sql
```

Ou use a aplicação para criar as tabelas automaticamente:
```python
from app import create_app
app = create_app()
with app.app_context():
    db.create_all()
```

## Testes

### Cartões de Teste do Stripe

- Sucesso: `4242 4242 4242 4242`
- Falha: `4000 0000 0000 0002`
- 3D Secure: `4000 0027 6000 3184`

### Testar Webhooks Localmente

```bash
# Instalar Stripe CLI
stripe listen --forward-to localhost:5000/api/subscriptions/webhook

# Simular eventos
stripe trigger invoice.paid
stripe trigger customer.subscription.deleted
```

## Monitoramento

Logs importantes são impressos no console:
- Webhooks recebidos
- Status de assinaturas atualizadas
- Erros de sincronização com Stripe

## Segurança

- Todas as rotas (exceto webhook) requerem JWT
- Webhook valida assinatura do Stripe
- Dados sensíveis do Stripe não são expostos
- IDs de clientes são validados antes de criar assinaturas

## Próximos Passos

1. Configurar conta no Stripe
2. Criar produtos e preços no Stripe Dashboard
3. Adicionar variáveis de ambiente
4. Configurar webhook no Stripe
5. Testar fluxo completo com cartões de teste
6. Implementar frontend (ver SUBSCRIPTION_IMPLEMENTATION_GUIDE.md)

---

**Última atualização:** 2025-10-30
