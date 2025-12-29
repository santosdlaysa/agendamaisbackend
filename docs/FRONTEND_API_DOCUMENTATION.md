# Documentação da API de Assinaturas - Frontend

## Base URL
```
http://localhost:5000/api/subscriptions
```

## Autenticação
Todas as rotas (exceto `/plans` e `/webhook`) requerem token JWT no header:
```
Authorization: Bearer {token}
```

---

## 📋 Endpoints

### 1. Listar Planos Disponíveis
Exibe os planos de assinatura para o usuário escolher.

```http
GET /api/subscriptions/plans
```

**Headers:** Nenhum (rota pública)

**Resposta de Sucesso (200):**
```json
{
  "plans": [
    {
      "id": "basic",
      "name": "Básico",
      "price": 29,
      "features": [
        "Até 100 agendamentos/mês",
        "Até 3 profissionais",
        "Lembretes básicos",
        "Suporte por email"
      ]
    },
    {
      "id": "pro",
      "name": "Pro",
      "price": 59,
      "features": [
        "Agendamentos ilimitados",
        "Até 10 profissionais",
        "Lembretes WhatsApp/SMS",
        "Relatórios avançados",
        "Suporte prioritário"
      ]
    },
    {
      "id": "enterprise",
      "name": "Enterprise",
      "price": 99,
      "features": [
        "Tudo do Pro",
        "Profissionais ilimitados",
        "API personalizada",
        "Gestor de conta dedicado",
        "Suporte 24/7"
      ]
    }
  ]
}
```

**Uso no Frontend:**
- Exibir cards de planos
- Mostrar preço em destaque
- Listar features como bullets
- Botão "Assinar" para cada plano

---

### 2. Criar Nova Assinatura
Inicia o processo de assinatura com Stripe.

```http
POST /api/subscriptions/subscribe
```

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:**
```json
{
  "plan": "pro"
}
```

**Campos:**
- `plan` (string, obrigatório): ID do plano escolhido (`"basic"`, `"pro"`, ou `"enterprise"`)

**Resposta de Sucesso (201):**
```json
{
  "subscription_id": 1,
  "stripe_subscription_id": "sub_1aBcD3FgHiJkLmNo",
  "client_secret": "pi_1aBcD3FgHiJkLmNo_secret_XyZ123AbC456",
  "status": "trialing",
  "trial_end": "2025-11-13T10:30:00"
}
```

**Campos da Resposta:**
- `subscription_id`: ID da assinatura no banco de dados
- `stripe_subscription_id`: ID da assinatura no Stripe
- `client_secret`: **IMPORTANTE** - Use este valor para confirmar o pagamento com Stripe Elements
- `status`: Estado inicial da assinatura (`"trialing"` = período de teste gratuito)
- `trial_end`: Data/hora de término do trial (formato ISO 8601)

**Erros Possíveis:**
```json
// 400 - Plano inválido
{
  "error": "Plano inválido"
}

// 400 - Já tem assinatura ativa
{
  "error": "Já existe uma assinatura ativa"
}

// 404 - Cliente não encontrado
{
  "error": "Cliente não encontrado"
}

// 400/500 - Erro do Stripe
{
  "error": "Erro no Stripe: [mensagem do erro]"
}
```

**Próximo Passo no Frontend:**
Após receber o `client_secret`, usar **Stripe Elements** para coletar dados do cartão e confirmar o pagamento:

```javascript
// Exemplo com Stripe.js
const stripe = Stripe('pk_test_...');
const { error, paymentIntent } = await stripe.confirmCardPayment(
  client_secret,
  {
    payment_method: {
      card: cardElement,
      billing_details: {
        name: 'Nome do Cliente',
        email: 'email@exemplo.com'
      }
    }
  }
);

if (error) {
  // Mostrar erro ao usuário
  console.error(error.message);
} else if (paymentIntent.status === 'succeeded') {
  // Pagamento confirmado!
  // Redirecionar para dashboard ou página de sucesso
}
```

---

### 3. Verificar Status da Assinatura
Consulta o estado atual da assinatura do usuário.

```http
GET /api/subscriptions/status
```

**Headers:**
```
Authorization: Bearer {token}
```

**Resposta de Sucesso (200) - Com Assinatura:**
```json
{
  "has_subscription": true,
  "subscription": {
    "id": 1,
    "client_id": 1,
    "plan": "pro",
    "stripe_customer_id": "cus_1aBcD3FgHiJkLmNo",
    "stripe_subscription_id": "sub_1aBcD3FgHiJkLmNo",
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

**Resposta de Sucesso (200) - Sem Assinatura:**
```json
{
  "has_subscription": false
}
```

**Campos Importantes:**
- `has_subscription`: Booleano indicando se o usuário tem assinatura
- `subscription.status`: Estado atual (`"trialing"`, `"active"`, `"past_due"`, `"canceled"`)
- `subscription.plan`: Plano contratado
- `subscription.trial_end`: Fim do período gratuito (se aplicável)
- `subscription.cancel_at_period_end`: `true` se o usuário cancelou mas ainda está ativo

**Estados da Assinatura:**
- `trialing`: Período de teste gratuito (7 dias)
- `active`: Assinatura ativa e paga
- `past_due`: Pagamento em atraso (ainda tem acesso limitado)
- `canceled`: Assinatura cancelada (sem acesso)

**Uso no Frontend:**
- Mostrar badge de status
- Exibir data de vencimento/renovação
- Mostrar alerta se `cancel_at_period_end` for `true`
- Desabilitar features se status não for `active` ou `trialing`

---

### 4. Cancelar Assinatura
Cancela a assinatura ao final do período pago (não imediato).

```http
POST /api/subscriptions/cancel
```

**Headers:**
```
Authorization: Bearer {token}
```

**Body:** Nenhum

**Resposta de Sucesso (200):**
```json
{
  "message": "Assinatura será cancelada ao fim do período",
  "subscription": {
    "id": 1,
    "client_id": 1,
    "plan": "pro",
    "stripe_customer_id": "cus_1aBcD3FgHiJkLmNo",
    "stripe_subscription_id": "sub_1aBcD3FgHiJkLmNo",
    "status": "active",
    "start_date": "2025-10-30T10:30:00",
    "end_date": null,
    "trial_end": null,
    "cancel_at_period_end": true,
    "created_at": "2025-10-30T10:30:00",
    "updated_at": "2025-11-06T11:00:00"
  }
}
```

**IMPORTANTE:** A assinatura continua ativa até o fim do período pago (`cancel_at_period_end: true`). O usuário mantém acesso até lá.

**Erros Possíveis:**
```json
// 404 - Sem assinatura
{
  "error": "Assinatura não encontrada"
}

// 400 - Assinatura já cancelada
{
  "error": "Assinatura não está ativa"
}
```

**Uso no Frontend:**
- Exibir modal de confirmação antes de cancelar
- Após cancelamento, mostrar mensagem: "Sua assinatura continua ativa até [data]"
- Oferecer botão "Reativar" se `cancel_at_period_end` for `true`

---

### 5. Reativar Assinatura
Reverte o cancelamento de uma assinatura.

```http
POST /api/subscriptions/reactivate
```

**Headers:**
```
Authorization: Bearer {token}
```

**Body:** Nenhum

**Resposta de Sucesso (200):**
```json
{
  "message": "Assinatura reativada com sucesso",
  "subscription": {
    "id": 1,
    "client_id": 1,
    "plan": "pro",
    "stripe_customer_id": "cus_1aBcD3FgHiJkLmNo",
    "stripe_subscription_id": "sub_1aBcD3FgHiJkLmNo",
    "status": "active",
    "start_date": "2025-10-30T10:30:00",
    "end_date": null,
    "trial_end": null,
    "cancel_at_period_end": false,
    "created_at": "2025-10-30T10:30:00",
    "updated_at": "2025-11-06T11:15:00"
  }
}
```

**Erros Possíveis:**
```json
// 404 - Sem assinatura
{
  "error": "Assinatura não encontrada"
}

// 400 - Não está cancelada
{
  "error": "Assinatura não está marcada para cancelamento"
}
```

**Uso no Frontend:**
- Mostrar apenas se `cancel_at_period_end` for `true`
- Exibir confirmação de reativação com sucesso

---

## 🎨 Fluxos de Interface (UX)

### Fluxo 1: Usuário Sem Assinatura

```
1. Usuário acessa dashboard/settings
   ↓
2. Frontend chama GET /status
   ↓
3. Recebe has_subscription: false
   ↓
4. Mostra página de planos (GET /plans)
   ↓
5. Usuário escolhe um plano e clica "Assinar"
   ↓
6. Frontend chama POST /subscribe com plan_id
   ↓
7. Recebe client_secret
   ↓
8. Mostra formulário Stripe Elements (cartão de crédito)
   ↓
9. Usuário preenche dados do cartão
   ↓
10. Frontend confirma pagamento com Stripe
   ↓
11. Stripe processa (trial de 7 dias gratuitos)
   ↓
12. Mostra mensagem de sucesso: "Você tem 7 dias grátis!"
   ↓
13. Redireciona para dashboard
```

### Fluxo 2: Usuário Com Assinatura Ativa

```
1. Usuário acessa configurações de assinatura
   ↓
2. Frontend chama GET /status
   ↓
3. Recebe has_subscription: true, status: "active"
   ↓
4. Mostra card com:
   - Plano atual (ex: "Pro - R$ 59/mês")
   - Status (badge verde "Ativo")
   - Data de renovação
   - Botão "Cancelar Assinatura"
```

### Fluxo 3: Cancelamento e Reativação

```
1. Usuário clica "Cancelar Assinatura"
   ↓
2. Frontend mostra modal de confirmação:
   "Tem certeza? Você manterá acesso até [data]"
   ↓
3. Usuário confirma
   ↓
4. Frontend chama POST /cancel
   ↓
5. Mostra alerta amarelo:
   "Assinatura cancelada. Acesso até 30/11/2025"
   Botão "Reativar"
   ↓
6. Se usuário clica "Reativar":
   ↓
7. Frontend chama POST /reactivate
   ↓
8. Mostra sucesso: "Assinatura reativada!"
```

### Fluxo 4: Trial Expirando

```
1. Frontend verifica trial_end periodicamente
   ↓
2. Se faltam < 3 dias para expirar:
   ↓
3. Mostra banner:
   "Seu trial expira em 2 dias. Adicione um cartão!"
   ↓
4. Se trial expirou sem cartão:
   ↓
5. Stripe tenta cobrar e falha
   ↓
6. Webhook atualiza status para "past_due"
   ↓
7. Frontend mostra alerta:
   "Pagamento pendente. Atualize seu cartão."
```

---

## 🚨 Tratamento de Erros

### Códigos HTTP
- `200` - Sucesso
- `201` - Assinatura criada
- `400` - Dados inválidos ou erro de negócio
- `401` - Token JWT inválido/expirado
- `403` - Sem permissão (via decorator)
- `404` - Recurso não encontrado
- `500` - Erro interno do servidor

### Erros Específicos de Assinatura

Quando proteger rotas com assinatura, o backend pode retornar:

```json
// 403 - Sem assinatura
{
  "error": "Assinatura necessária para acessar este recurso",
  "code": "SUBSCRIPTION_REQUIRED"
}

// 403 - Assinatura inativa
{
  "error": "Assinatura inativa",
  "code": "SUBSCRIPTION_INACTIVE",
  "status": "past_due"
}

// 403 - Plano insuficiente
{
  "error": "Plano insuficiente",
  "code": "PLAN_UPGRADE_REQUIRED",
  "current_plan": "basic",
  "required_plans": ["pro", "enterprise"]
}
```

**Como tratar no Frontend:**
```javascript
if (error.code === 'SUBSCRIPTION_REQUIRED') {
  // Redirecionar para página de planos
  router.push('/subscription/plans');
}

if (error.code === 'SUBSCRIPTION_INACTIVE') {
  // Mostrar alerta de pagamento pendente
  showAlert('Seu pagamento está pendente. Atualize seu cartão.');
}

if (error.code === 'PLAN_UPGRADE_REQUIRED') {
  // Mostrar modal de upgrade
  showUpgradeModal({
    current: error.current_plan,
    required: error.required_plans
  });
}
```

---

## 💳 Integração com Stripe

### 1. Incluir Stripe.js

```html
<script src="https://js.stripe.com/v3/"></script>
```

### 2. Inicializar Stripe

```javascript
const stripe = Stripe('pk_test_...'); // Chave pública do Stripe
const elements = stripe.elements();
const cardElement = elements.create('card');
cardElement.mount('#card-element');
```

### 3. Confirmar Pagamento

```javascript
async function subscribe(planId) {
  // 1. Criar assinatura no backend
  const response = await fetch('/api/subscriptions/subscribe', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ plan: planId })
  });

  const data = await response.json();

  if (!response.ok) {
    alert(data.error);
    return;
  }

  // 2. Confirmar pagamento com Stripe
  const { error, paymentIntent } = await stripe.confirmCardPayment(
    data.client_secret,
    {
      payment_method: {
        card: cardElement,
        billing_details: {
          name: userName,
          email: userEmail
        }
      }
    }
  );

  if (error) {
    alert('Erro no pagamento: ' + error.message);
  } else {
    // Sucesso! Trial iniciado
    alert('Assinatura criada! Você tem 7 dias grátis.');
    window.location.href = '/dashboard';
  }
}
```

### 4. Cartões de Teste

Para desenvolvimento, use estes números de cartão:

| Cenário | Número | CVV | Data | CEP |
|---------|--------|-----|------|-----|
| Sucesso | 4242 4242 4242 4242 | 123 | 12/34 | Qualquer |
| Falha | 4000 0000 0000 0002 | 123 | 12/34 | Qualquer |
| 3D Secure | 4000 0027 6000 3184 | 123 | 12/34 | Qualquer |

---

## 🎯 Componentes Sugeridos para o Frontend

### 1. SubscriptionPlans (Página de Planos)
- Lista cards de planos lado a lado
- Destaca plano recomendado (Pro)
- Botão "Escolher Plano" que abre modal de pagamento

### 2. PaymentModal (Modal de Pagamento)
- Stripe Elements para captura de cartão
- Resumo do plano escolhido
- Informação do trial: "7 dias grátis, depois R$ X/mês"
- Loading state durante processamento

### 3. SubscriptionStatus (Card de Status)
- Badge colorido por status (verde=active, amarelo=trialing, vermelho=past_due)
- Info do plano atual
- Data de renovação ou trial
- Botões "Cancelar" ou "Reativar"

### 4. UpgradePrompt (Banner/Modal de Upgrade)
- Aparece quando usuário tenta usar feature bloqueada
- Compara plano atual vs. plano necessário
- Botão "Fazer Upgrade"

### 5. SubscriptionGuard (HOC/Middleware)
```javascript
// Exemplo React
function SubscriptionGuard({ children, requiredPlans }) {
  const { subscription } = useSubscription();

  if (!subscription?.is_active) {
    return <UpgradePrompt />;
  }

  if (requiredPlans && !requiredPlans.includes(subscription.plan)) {
    return <UpgradePrompt requiredPlans={requiredPlans} />;
  }

  return children;
}

// Uso:
<SubscriptionGuard requiredPlans={['pro', 'enterprise']}>
  <AdvancedReports />
</SubscriptionGuard>
```

---

## 📊 Estados da UI por Status

| Status | Badge | Descrição | Ações Disponíveis |
|--------|-------|-----------|-------------------|
| `trialing` | 🟡 Trial | "Trial até DD/MM" | Cancelar |
| `active` | 🟢 Ativo | "Próxima cobrança: DD/MM" | Cancelar |
| `past_due` | 🟠 Pendente | "Pagamento pendente" | Atualizar cartão |
| `canceled` | 🔴 Cancelado | "Acesso encerrado" | Renovar |

---

## 🔔 Notificações Sugeridas

### Trial vai expirar em 3 dias
```
"Seu trial expira em 3 dias! Adicione um método de pagamento para continuar."
[Adicionar Cartão]
```

### Trial vai expirar hoje
```
"Seu trial expira hoje! Adicione um cartão para não perder acesso."
[Adicionar Cartão Agora]
```

### Pagamento falhou
```
"Não conseguimos processar seu pagamento. Por favor, atualize seu cartão."
[Atualizar Cartão]
```

### Assinatura cancelada (mas ainda ativa)
```
"Sua assinatura será cancelada em DD/MM. Mudou de ideia?"
[Reativar Assinatura]
```

---

## ✅ Checklist de Implementação Frontend

### Setup Inicial
- [ ] Adicionar Stripe.js no projeto
- [ ] Configurar chave pública do Stripe (`pk_test_...`)
- [ ] Criar serviço/API client para chamadas HTTP

### Páginas/Componentes
- [ ] Página de planos (`/subscription/plans`)
- [ ] Modal de pagamento com Stripe Elements
- [ ] Página de gerenciamento de assinatura (`/subscription/manage`)
- [ ] Guard/HOC para proteger features premium

### Funcionalidades
- [ ] Listar planos disponíveis
- [ ] Processo de checkout com Stripe
- [ ] Exibir status da assinatura
- [ ] Cancelar assinatura
- [ ] Reativar assinatura
- [ ] Notificações de trial expirando
- [ ] Tratamento de erros de pagamento

### UX/UI
- [ ] Badges de status coloridos
- [ ] Loading states durante operações
- [ ] Modais de confirmação para cancelamento
- [ ] Mensagens de erro amigáveis
- [ ] Alerts/banners para ações importantes

---

## 🔗 Recursos Úteis

- [Stripe.js Documentation](https://stripe.com/docs/js)
- [Stripe Elements](https://stripe.com/docs/payments/elements)
- [Testing Stripe](https://stripe.com/docs/testing)
- [Payment Intents API](https://stripe.com/docs/payments/payment-intents)

---

## 📞 Contato Backend

Se encontrar inconsistências nos dados ou erros não documentados, contate o time de backend.

**Versão da API:** 1.0.0
**Última atualização:** 2025-11-06
