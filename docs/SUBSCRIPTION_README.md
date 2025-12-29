# Sistema de Assinaturas SaaS - AgendaMais

## 📋 Visão Geral

Sistema completo de assinaturas SaaS integrado com Stripe para gerenciar planos de pagamento recorrente do AgendaMais.

### ✨ Funcionalidades

- ✅ 3 Planos de assinatura (Básico, Pro, Enterprise)
- ✅ Trial gratuito de 7 dias
- ✅ Integração completa com Stripe
- ✅ Webhooks automáticos para sincronização
- ✅ Controle de acesso por plano
- ✅ Sistema de features por plano
- ✅ 64 testes unitários (>80% cobertura)
- ✅ Documentação completa

## 🚀 Quick Start

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas credenciais
# Ver SUBSCRIPTION_ENV_SETUP.md para detalhes
```

### 3. Executar Migração

```bash
# PostgreSQL
psql -U postgres -d agendamais < migrations/create_subscriptions.sql

# Ou deixe o Flask criar automaticamente
python app.py
```

### 4. Testar

```bash
# Executar testes
pytest

# Com cobertura
pytest --cov=src
```

## 📦 Planos Disponíveis

| Plano | Preço | Agendamentos | Profissionais | Features |
|-------|-------|--------------|---------------|----------|
| **Básico** | R$ 29/mês | 100/mês | 3 | Lembretes básicos, Email |
| **Pro** | R$ 59/mês | Ilimitado | 10 | + WhatsApp/SMS, Relatórios |
| **Enterprise** | R$ 99/mês | Ilimitado | Ilimitado | + API, Suporte 24/7 |

*Todos os planos incluem 7 dias de trial gratuito*

## 📚 Documentação

### Guias Principais

1. **[SUBSCRIPTION_ENV_SETUP.md](SUBSCRIPTION_ENV_SETUP.md)** ⭐ COMECE AQUI
   - Como obter STRIPE_SECRET_KEY
   - Como obter STRIPE_WEBHOOK_SECRET
   - Como obter DATABASE_URL
   - Passo a passo completo

2. **[SUBSCRIPTION_SETUP.md](SUBSCRIPTION_SETUP.md)**
   - Guia rápido de configuração
   - Checklist de implementação
   - Troubleshooting

3. **[SUBSCRIPTION_API.md](SUBSCRIPTION_API.md)**
   - Documentação completa da API
   - Endpoints disponíveis
   - Exemplos de requisições

4. **[SUBSCRIPTION_TESTING_GUIDE.md](SUBSCRIPTION_TESTING_GUIDE.md)**
   - Como executar testes
   - Como criar novos testes
   - Fixtures disponíveis

5. **[SUBSCRIPTION_USAGE_EXAMPLES.md](SUBSCRIPTION_USAGE_EXAMPLES.md)**
   - Exemplos práticos de uso
   - Como proteger rotas
   - Como verificar planos

6. **[SUBSCRIPTION_IMPLEMENTATION_GUIDE.md](SUBSCRIPTION_IMPLEMENTATION_GUIDE.md)**
   - Guia completo de implementação
   - Frontend React
   - Deploy

## 🏗️ Arquitetura

```
Backend/
├── src/
│   ├── models/
│   │   └── subscription.py           # Model de assinatura
│   ├── app/main/subscription/
│   │   └── subscriptions.py          # Rotas de API
│   └── decorators/
│       └── subscription_required.py  # Controle de acesso
├── migrations/
│   └── create_subscriptions.sql      # Script SQL
└── tests/
    ├── conftest.py                   # Fixtures
    ├── test_subscription_model.py    # 24 testes
    ├── test_subscription_routes.py   # 23 testes
    └── test_subscription_decorator.py # 17 testes
```

## 🔌 API Endpoints

```
GET    /api/subscriptions/plans          # Listar planos
POST   /api/subscriptions/subscribe      # Criar assinatura
GET    /api/subscriptions/status         # Status da assinatura
POST   /api/subscriptions/cancel         # Cancelar assinatura
POST   /api/subscriptions/reactivate     # Reativar assinatura
POST   /api/subscriptions/webhook        # Webhook do Stripe
```

## 🛡️ Usando o Decorator

### Qualquer Plano Ativo

```python
from flask_jwt_extended import jwt_required
from src.decorators import subscription_required

@app.route('/api/feature')
@jwt_required()
@subscription_required()
def feature():
    return jsonify({'message': 'Acesso permitido'})
```

### Planos Específicos

```python
@app.route('/api/premium-feature')
@jwt_required()
@subscription_required(['pro', 'enterprise'])
def premium_feature():
    return jsonify({'message': 'Feature premium'})
```

### Features Específicas

```python
from src.decorators import check_feature_access

@app.route('/api/advanced-reports')
@jwt_required()
@check_feature_access('advanced_reports')
def advanced_reports():
    return jsonify({'report': 'data'})
```

## 🧪 Testes

### Executar Todos os Testes

```bash
pytest
```

### Cobertura

```bash
pytest --cov=src --cov-report=html
# Abra htmlcov/index.html
```

### Testes Específicos

```bash
pytest tests/test_subscription_model.py
pytest tests/test_subscription_routes.py
pytest tests/test_subscription_decorator.py
```

**Cobertura Total: 64 testes, >80%**

## 🔧 Configuração do Stripe

### 1. Criar Conta

https://stripe.com → Criar conta → Ativar modo de teste

### 2. Obter Chaves

Dashboard > Developers > API keys
- Copie **Secret key** (sk_test_...)

### 3. Criar Produtos

Dashboard > Products > Create product
- Crie: Básico (R$ 29), Pro (R$ 59), Enterprise (R$ 99)
- Copie os **Price IDs** (price_...)

### 4. Configurar Webhook (Desenvolvimento)

```bash
# Instalar Stripe CLI
stripe login
stripe listen --forward-to localhost:5000/api/subscriptions/webhook
# Copie o webhook secret (whsec_...)
```

**Ver [SUBSCRIPTION_ENV_SETUP.md](SUBSCRIPTION_ENV_SETUP.md) para detalhes completos**

## 💳 Testando com Cartões

Use estes números em modo de teste:

| Resultado | Número |
|-----------|--------|
| Sucesso | `4242 4242 4242 4242` |
| Falha | `4000 0000 0000 0002` |
| 3D Secure | `4000 0027 6000 3184` |

**CVV:** Qualquer 3 dígitos
**Data:** Qualquer data futura

## 📊 Status de Assinatura

| Status | Descrição |
|--------|-----------|
| `trialing` | Período de teste gratuito (7 dias) |
| `active` | Assinatura ativa e paga |
| `past_due` | Pagamento atrasado |
| `canceled` | Assinatura cancelada |

## 🚨 Troubleshooting

### Erro: "Invalid API key"
✅ Verifique STRIPE_SECRET_KEY no .env

### Erro: "Webhook signature verification failed"
✅ Reinicie `stripe listen` e copie novo secret

### Erro: "Price not found"
✅ Verifique IDs dos preços no Stripe Dashboard

### Erro: "Database not found"
✅ Execute a migração SQL

**Ver mais em [SUBSCRIPTION_SETUP.md](SUBSCRIPTION_SETUP.md#troubleshooting)**

## 📈 Roadmap

### ✅ Concluído
- [x] Backend completo
- [x] Integração Stripe
- [x] Webhooks
- [x] Controle de acesso
- [x] Testes unitários
- [x] Documentação

### 📋 Próximo
- [ ] Frontend React
- [ ] Painel de administração
- [ ] Relatórios de receita
- [ ] Múltiplas moedas
- [ ] Cupons de desconto

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto é parte do AgendaMais.

## 🔗 Links Úteis

### Documentação Interna
- [Configuração de Variáveis](SUBSCRIPTION_ENV_SETUP.md)
- [Guia de Setup](SUBSCRIPTION_SETUP.md)
- [API](SUBSCRIPTION_API.md)
- [Testes](SUBSCRIPTION_TESTING_GUIDE.md)
- [Exemplos](SUBSCRIPTION_USAGE_EXAMPLES.md)

### Documentação Externa
- [Stripe Docs](https://stripe.com/docs)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Webhooks](https://stripe.com/docs/webhooks)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)

## 💬 Suporte

Encontrou um bug ou tem uma sugestão?

1. Verifique a [documentação](SUBSCRIPTION_SETUP.md)
2. Consulte o [troubleshooting](SUBSCRIPTION_SETUP.md#troubleshooting)
3. Abra uma issue no GitHub

---

**Desenvolvido para AgendaMais**
**Versão:** 1.0.0
**Data:** 2025-10-30

⭐ Se este projeto foi útil, considere dar uma estrela!
