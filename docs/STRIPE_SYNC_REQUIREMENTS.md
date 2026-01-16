# Requisitos: Sincronização Direta com Stripe

## Problema Atual

O sistema atual depende **exclusivamente de webhooks** para registrar pagamentos. Isso causa:

- Pagamentos não registrados se webhooks falharem
- Impossibilidade de recuperar histórico anterior à implementação
- Sem forma de validar/corrigir dados inconsistentes
- Dependência total da disponibilidade do webhook

---

## Solução Proposta: Abordagem Híbrida

Manter o sistema atual de webhooks (para registro em tempo real) e adicionar:

1. **Sincronização Manual** - Endpoint para buscar e sincronizar dados do Stripe
2. **Consulta Direta** - Opção de buscar dados em tempo real quando necessário

---

## Novos Endpoints

### 1. Sincronizar Pagamentos do Stripe

```
POST /api/superadmin/payments/sync
```

**Descrição:** Busca todas as invoices pagas do Stripe e sincroniza com o banco local.

**Autenticação:** Bearer Token (superadmin)

**Parâmetros de Body (opcional):**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `start_date` | string | 30 dias atrás | Data inicial (YYYY-MM-DD) |
| `end_date` | string | hoje | Data final (YYYY-MM-DD) |
| `customer_id` | string | null | Stripe customer ID específico |
| `force_update` | boolean | false | Atualizar registros existentes |

**Resposta:**

```json
{
  "success": true,
  "synced": {
    "created": 15,
    "updated": 3,
    "skipped": 42,
    "errors": 0
  },
  "message": "Sincronização concluída: 15 novos, 3 atualizados, 42 já existiam"
}
```

**Lógica de Implementação:**

```python
import stripe

def sync_payments_from_stripe(start_date=None, end_date=None, customer_id=None, force_update=False):
    """
    Busca invoices do Stripe e sincroniza com banco local.
    """
    # Configurar filtros
    params = {
        'status': 'paid',
        'limit': 100,  # Máximo por página
    }

    if start_date:
        params['created'] = {'gte': int(start_date.timestamp())}
    if end_date:
        params['created']['lte'] = int(end_date.timestamp())
    if customer_id:
        params['customer'] = customer_id

    created = updated = skipped = errors = 0

    # Iterar sobre todas as invoices (paginação automática)
    invoices = stripe.Invoice.list(**params)

    for invoice in invoices.auto_paging_iter():
        try:
            # Verificar se já existe
            existing = Payment.query.filter_by(
                stripe_invoice_id=invoice.id
            ).first()

            if existing and not force_update:
                skipped += 1
                continue

            # Buscar subscription local pelo stripe_subscription_id
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=invoice.subscription
            ).first()

            if not subscription:
                # Log: subscription não encontrada
                errors += 1
                continue

            payment_data = {
                'subscription_id': subscription.id,
                'user_id': subscription.user_id,
                'stripe_invoice_id': invoice.id,
                'stripe_payment_intent_id': invoice.payment_intent,
                'amount': invoice.amount_paid / 100,  # Centavos para reais
                'currency': invoice.currency,
                'status': 'paid',
                'paid_at': datetime.fromtimestamp(invoice.status_transitions.paid_at),
                'period_start': datetime.fromtimestamp(invoice.period_start),
                'period_end': datetime.fromtimestamp(invoice.period_end),
            }

            if existing:
                for key, value in payment_data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                payment = Payment(**payment_data)
                db.session.add(payment)
                created += 1

        except Exception as e:
            errors += 1
            # Log error

    db.session.commit()

    return {
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'errors': errors
    }
```

---

### 2. Buscar Invoice Específica do Stripe

```
GET /api/superadmin/payments/stripe/{invoice_id}
```

**Descrição:** Busca dados de uma invoice específica diretamente do Stripe.

**Autenticação:** Bearer Token (superadmin)

**Resposta:**

```json
{
  "stripe_data": {
    "id": "in_1234567890",
    "customer": "cus_1234567890",
    "subscription": "sub_1234567890",
    "amount_paid": 5900,
    "currency": "brl",
    "status": "paid",
    "paid_at": "2024-01-15T10:30:00Z",
    "period_start": "2024-01-15T00:00:00Z",
    "period_end": "2024-02-15T00:00:00Z",
    "invoice_pdf": "https://pay.stripe.com/invoice/...",
    "hosted_invoice_url": "https://invoice.stripe.com/..."
  },
  "local_data": {
    "id": 1,
    "amount": 59.00,
    "status": "paid",
    "synced": true
  },
  "differences": []
}
```

**Lógica:**

```python
def get_stripe_invoice(invoice_id):
    """
    Busca invoice diretamente do Stripe e compara com dados locais.
    """
    # Buscar do Stripe
    stripe_invoice = stripe.Invoice.retrieve(invoice_id)

    # Buscar local
    local_payment = Payment.query.filter_by(
        stripe_invoice_id=invoice_id
    ).first()

    # Comparar e identificar diferenças
    differences = []
    if local_payment:
        stripe_amount = stripe_invoice.amount_paid / 100
        if local_payment.amount != stripe_amount:
            differences.append({
                'field': 'amount',
                'local': float(local_payment.amount),
                'stripe': stripe_amount
            })

    return {
        'stripe_data': format_stripe_invoice(stripe_invoice),
        'local_data': format_local_payment(local_payment) if local_payment else None,
        'differences': differences
    }
```

---

### 3. Listar Invoices do Stripe (Tempo Real)

```
GET /api/superadmin/payments/stripe
```

**Descrição:** Lista invoices diretamente do Stripe (não do banco local).

**Autenticação:** Bearer Token (superadmin)

**Parâmetros de Query:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `limit` | integer | 20 | Máximo de resultados |
| `starting_after` | string | null | Cursor para paginação |
| `status` | string | 'paid' | Status: 'paid', 'open', 'void', 'uncollectible' |
| `customer` | string | null | Filtrar por Stripe customer ID |

**Resposta:**

```json
{
  "invoices": [
    {
      "id": "in_1234567890",
      "customer": "cus_1234567890",
      "customer_email": "cliente@email.com",
      "amount_paid": 59.00,
      "currency": "brl",
      "status": "paid",
      "paid_at": "2024-01-15T10:30:00Z",
      "invoice_pdf": "https://pay.stripe.com/invoice/...",
      "synced_locally": true
    }
  ],
  "has_more": true,
  "next_cursor": "in_0987654321"
}
```

---

### 4. Verificar Integridade dos Dados

```
GET /api/superadmin/payments/integrity
```

**Descrição:** Compara dados locais com Stripe e identifica inconsistências.

**Autenticação:** Bearer Token (superadmin)

**Parâmetros de Query:**

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `start_date` | string | 30 dias atrás | Data inicial |
| `end_date` | string | hoje | Data final |

**Resposta:**

```json
{
  "summary": {
    "total_stripe": 100,
    "total_local": 95,
    "missing_locally": 5,
    "missing_on_stripe": 0,
    "amount_mismatch": 2
  },
  "issues": [
    {
      "type": "missing_locally",
      "stripe_invoice_id": "in_abc123",
      "customer_email": "cliente@email.com",
      "amount": 59.00,
      "paid_at": "2024-01-10T10:00:00Z"
    },
    {
      "type": "amount_mismatch",
      "stripe_invoice_id": "in_def456",
      "local_amount": 59.00,
      "stripe_amount": 69.00
    }
  ]
}
```

---

## Alterações no Modelo de Dados

### Adicionar campos à tabela `payments`:

```sql
ALTER TABLE payments ADD COLUMN stripe_invoice_url VARCHAR(500);
ALTER TABLE payments ADD COLUMN stripe_invoice_pdf VARCHAR(500);
ALTER TABLE payments ADD COLUMN synced_at TIMESTAMP;
ALTER TABLE payments ADD COLUMN sync_source VARCHAR(20) DEFAULT 'webhook';
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `stripe_invoice_url` | String(500) | URL da invoice hospedada no Stripe |
| `stripe_invoice_pdf` | String(500) | URL do PDF da invoice |
| `synced_at` | DateTime | Última sincronização com Stripe |
| `sync_source` | String(20) | Origem: 'webhook' ou 'manual_sync' |

---

## Dependências Stripe API

### Métodos utilizados:

| Método | Uso |
|--------|-----|
| `stripe.Invoice.list()` | Listar invoices com filtros |
| `stripe.Invoice.retrieve()` | Buscar invoice específica |
| `stripe.Customer.retrieve()` | Buscar dados do cliente |

### Rate Limits:

- Stripe permite **100 requests/segundo** em modo live
- Usar paginação com `limit=100` para eficiência
- Implementar retry com backoff exponencial

---

## Interface Frontend

### Novos componentes sugeridos:

1. **Botão "Sincronizar com Stripe"**
   - Localização: Página de Faturamento (`/admin/payments`)
   - Ação: Chama `POST /api/superadmin/payments/sync`
   - Feedback: Progress bar + resultado da sincronização

2. **Indicador de Status de Sync**
   - Mostrar última sincronização
   - Alertar se há inconsistências

3. **Modal de Detalhes do Pagamento**
   - Mostrar dados locais vs Stripe
   - Link para invoice no Stripe
   - Botão para baixar PDF

### Mockup do botão:

```
┌─────────────────────────────────────────────────┐
│  Faturamento                    [🔄 Sincronizar]│
│                                                 │
│  Última sync: 15/01/2024 10:30                 │
│  Status: ✓ Dados sincronizados                 │
└─────────────────────────────────────────────────┘
```

---

## Fluxo de Sincronização

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│    Stripe    │
│ Clica Sync   │     │  POST /sync  │     │ Invoice.list │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            │◀───────────────────┘
                            │   Lista de invoices
                            ▼
                     ┌──────────────┐
                     │  Para cada   │
                     │   invoice:   │
                     └──────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌─────────┐   ┌─────────┐   ┌─────────┐
        │  Novo?  │   │ Existe? │   │  Erro?  │
        │ CREATE  │   │  SKIP   │   │   LOG   │
        └─────────┘   └─────────┘   └─────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Retorna    │
                     │  Resultado   │
                     └──────────────┘
```

---

## Considerações de Segurança

1. **Apenas superadmin** pode executar sincronização
2. **Rate limiting** no endpoint de sync (1 request/minuto)
3. **Logging** de todas as operações de sync para auditoria
4. **Timeout** de 5 minutos para operações de sync longas

---

## Estimativa de Implementação

### Arquivos a modificar/criar:

| Arquivo | Ação | Descrição |
|---------|------|-----------|
| `src/models/payment.py` | Modificar | Adicionar novos campos |
| `src/app/main/superadmin/superadmin.py` | Modificar | Adicionar endpoints de sync |
| `src/services/stripe_sync.py` | Criar | Lógica de sincronização |
| `migrations/xxx_add_sync_fields.py` | Criar | Migration para novos campos |

### Ordem de implementação sugerida:

1. Migration para novos campos no modelo Payment
2. Criar serviço `stripe_sync.py` com lógica de sincronização
3. Implementar endpoint `POST /sync`
4. Implementar endpoint `GET /stripe` (listagem direta)
5. Implementar endpoint `GET /stripe/{id}` (detalhe)
6. Implementar endpoint `GET /integrity` (verificação)
7. Atualizar frontend com botão de sync

---

## Exemplos de Uso

### Sincronizar últimos 30 dias:

```bash
curl -X POST "https://api.exemplo.com/api/superadmin/payments/sync" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

### Sincronizar período específico:

```bash
curl -X POST "https://api.exemplo.com/api/superadmin/payments/sync" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "force_update": true
  }'
```

### Verificar integridade:

```bash
curl "https://api.exemplo.com/api/superadmin/payments/integrity" \
  -H "Authorization: Bearer {token}"
```
