# Guia Rápido de Setup - Sistema de Assinaturas

## Checklist de Implementação

### Backend ✅

- [x] Instalar dependência Stripe
- [x] Criar model Subscription
- [x] Criar rotas de assinatura
- [x] Implementar webhook do Stripe
- [x] Criar decorator subscription_required
- [x] Atualizar variáveis de ambiente
- [x] Registrar blueprint no app.py
- [x] Criar script de migração SQL
- [x] Criar testes unitários (64 testes)
- [x] Criar fixtures de teste
- [x] Documentar testes

### Próximos Passos

1. **Configurar Stripe** 🔧
   - [ ] Criar conta no Stripe (https://stripe.com)
   - [ ] Ativar modo de teste
   - [ ] Copiar chaves de API (pk_test_... e sk_test_...)

2. **Criar Produtos no Stripe** 💳
   - [ ] Acessar Dashboard > Produtos
   - [ ] Criar produto "Básico" - R$ 29/mês
   - [ ] Criar produto "Pro" - R$ 59/mês
   - [ ] Criar produto "Enterprise" - R$ 99/mês
   - [ ] Copiar IDs dos preços (price_...)

3. **Configurar Variáveis de Ambiente** ⚙️
   ```bash
   # Copie .env.example para .env
   cp .env.example .env

   # Edite .env e adicione suas chaves:
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_PRICE_BASIC=price_...
   STRIPE_PRICE_PRO=price_...
   STRIPE_PRICE_ENTERPRISE=price_...
   ```

4. **Executar Migração** 🗄️
   ```bash
   # PostgreSQL
   psql -U postgres -d agendamais < migrations/create_subscriptions.sql

   # Ou deixe o Flask criar automaticamente
   python app.py  # As tabelas serão criadas no startup
   ```

5. **Configurar Webhook do Stripe** 🔗
   ```bash
   # Desenvolvimento local - Instalar Stripe CLI
   # Windows: scoop install stripe
   # Mac: brew install stripe/stripe-cli/stripe
   # Linux: https://stripe.com/docs/stripe-cli

   # Login no Stripe
   stripe login

   # Iniciar listener
   stripe listen --forward-to localhost:5000/api/subscriptions/webhook

   # Copie o webhook secret (whsec_...) para .env
   ```

6. **Testar API** 🧪
   ```bash
   # Iniciar servidor
   python app.py

   # Testar endpoints
   curl http://localhost:5000/api/subscriptions/plans
   ```

## Estrutura de Arquivos Criados

```
agendamaisbackend/
├── src/
│   ├── models/
│   │   └── subscription.py          ✅ Model de assinatura
│   ├── app/
│   │   └── main/
│   │       └── subscription/
│   │           ├── __init__.py
│   │           └── subscriptions.py ✅ Rotas de subscription
│   └── decorators/
│       ├── __init__.py
│       └── subscription_required.py ✅ Decorator de controle
├── migrations/
│   └── create_subscriptions.sql     ✅ Script SQL
├── app.py                           ✅ Atualizado
├── requirements.txt                 ✅ Atualizado
├── .env.example                     ✅ Atualizado
├── tests/
│   ├── conftest.py                  ✅ Configuração de testes
│   ├── test_subscription_model.py   ✅ Testes do model
│   ├── test_subscription_routes.py  ✅ Testes das rotas
│   └── test_subscription_decorator.py ✅ Testes do decorator
├── SUBSCRIPTION_API.md              ✅ Documentação da API
├── SUBSCRIPTION_SETUP.md            ✅ Este arquivo
├── SUBSCRIPTION_TESTING_GUIDE.md    ✅ Guia de testes
├── SUBSCRIPTION_USAGE_EXAMPLES.md   ✅ Exemplos de uso
└── SUBSCRIPTION_IMPLEMENTATION_GUIDE.md ✅ Guia completo
```

## Testando o Sistema

### 1. Testar Criação de Assinatura

```bash
# 1. Login (obter token JWT)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "cliente@email.com", "password": "senha"}'

# 2. Listar planos
curl http://localhost:5000/api/subscriptions/plans

# 3. Criar assinatura
curl -X POST http://localhost:5000/api/subscriptions/subscribe \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {seu_token}" \
  -d '{"plan": "pro"}'

# 4. Verificar status
curl http://localhost:5000/api/subscriptions/status \
  -H "Authorization: Bearer {seu_token}"
```

### 2. Testar Webhooks (Modo Desenvolvimento)

```bash
# Terminal 1: Servidor Flask
python app.py

# Terminal 2: Stripe CLI listener
stripe listen --forward-to localhost:5000/api/subscriptions/webhook

# Terminal 3: Simular eventos
stripe trigger invoice.paid
stripe trigger customer.subscription.deleted
```

### 3. Testar Controle de Acesso

```python
# Adicione em qualquer rota:
from flask_jwt_extended import jwt_required
from src.decorators import subscription_required

@app.route('/api/teste-premium')
@jwt_required()
@subscription_required(['pro', 'enterprise'])
def teste_premium():
    return jsonify({'message': 'Acesso permitido!'})
```

### 4. Executar Testes Unitários

```bash
# Instalar dependências de teste
pip install pytest pytest-cov pytest-mock

# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=src --cov-report=html

# Executar testes específicos
pytest tests/test_subscription_model.py
pytest tests/test_subscription_routes.py
pytest tests/test_subscription_decorator.py

# Ver relatório detalhado
pytest -vv
```

**Cobertura de Testes:**
- ✅ 24 testes do model Subscription
- ✅ 23 testes das rotas de API
- ✅ 17 testes do decorator
- **Total: 64 testes**

Para mais detalhes, consulte `SUBSCRIPTION_TESTING_GUIDE.md`

## Cartões de Teste

Use estes números para testar:

- **Sucesso:** `4242 4242 4242 4242`
- **Falha:** `4000 0000 0000 0002`
- **3D Secure:** `4000 0027 6000 3184`

**CVV:** Qualquer 3 dígitos
**Data:** Qualquer data futura
**CEP:** Qualquer CEP

## Troubleshooting

### Erro: "Webhook secret não configurado"
**Solução:** Adicione STRIPE_WEBHOOK_SECRET no .env

### Erro: "Plano inválido"
**Solução:** Verifique se os IDs dos preços estão corretos no .env

### Erro: "ImportError: stripe"
**Solução:** Execute `pip install stripe`

### Erro: Webhook não recebe eventos
**Solução:** Verifique se o Stripe CLI está rodando e apontando para a URL correta

### Erro: "Subscription not found"
**Solução:** Execute a migração SQL para criar a tabela subscriptions

## Status da Implementação

### ✅ Concluído
- Backend Flask completo
- Model Subscription
- Rotas de API
- Webhook do Stripe
- Decorator de controle de acesso
- Testes unitários (64 testes, >80% cobertura)
- Fixtures de teste
- Documentação completa

### 📋 Pendente
- Frontend React (ver SUBSCRIPTION_IMPLEMENTATION_GUIDE.md)
- Deploy em produção
- Configuração de produção no Stripe
- Testes de integração E2E

## Recursos Úteis

### Documentação do Projeto
- `SUBSCRIPTION_API.md` - Documentação completa da API
- `SUBSCRIPTION_TESTING_GUIDE.md` - Guia de testes
- `SUBSCRIPTION_USAGE_EXAMPLES.md` - Exemplos práticos
- `SUBSCRIPTION_IMPLEMENTATION_GUIDE.md` - Guia completo de implementação

### Documentação Externa
- [Documentação Stripe](https://stripe.com/docs)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Pytest Documentation](https://docs.pytest.org/)

## Contato

Se encontrar problemas ou tiver dúvidas:
1. Verifique os logs do console
2. Consulte a documentação do Stripe
3. Revise o arquivo SUBSCRIPTION_API.md
4. Verifique se todas as variáveis de ambiente estão configuradas

---

**Sistema implementado em:** 2025-10-30
**Versão:** 1.0.0
