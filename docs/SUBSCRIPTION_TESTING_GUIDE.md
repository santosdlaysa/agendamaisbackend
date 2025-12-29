# Guia de Testes - Sistema de Assinaturas

## Visão Geral

Este guia explica como executar e criar testes para o sistema de assinaturas do AgendaMais.

## Estrutura de Testes

```
tests/
├── conftest.py                        # Configurações e fixtures
├── test_subscription_model.py         # Testes do model Subscription
├── test_subscription_routes.py        # Testes das rotas de API
└── test_subscription_decorator.py     # Testes do decorator
```

## Instalação de Dependências

```bash
# Instalar pytest e dependências de teste
pip install pytest pytest-cov pytest-mock
```

## Executar Testes

### Executar Todos os Testes

```bash
pytest
```

### Executar Testes Específicos

```bash
# Apenas testes do model
pytest tests/test_subscription_model.py

# Apenas testes das rotas
pytest tests/test_subscription_routes.py

# Apenas testes do decorator
pytest tests/test_subscription_decorator.py

# Executar teste específico
pytest tests/test_subscription_model.py::TestSubscriptionModel::test_create_subscription
```

### Executar com Cobertura

```bash
# Gerar relatório de cobertura
pytest --cov=src --cov-report=html

# Ver relatório
# Abra htmlcov/index.html no navegador
```

### Executar com Verbose

```bash
# Ver detalhes de cada teste
pytest -v

# Ver output completo
pytest -vv
```

## Fixtures Disponíveis

### Fixtures de App e Cliente

- `app` - Aplicação Flask configurada para testes
- `client` - Cliente de teste Flask
- `db_session` - Sessão de banco de dados

### Fixtures de Usuários

- `test_user` - Usuário admin de teste
- `test_client_user` - Cliente de teste
- `auth_token` - Token JWT de autenticação
- `auth_headers` - Headers com autenticação

### Fixtures de Assinatura

- `test_subscription` - Assinatura ativa (plano Pro)
- `test_subscription_basic` - Assinatura básica
- `test_subscription_trialing` - Assinatura em trial
- `test_subscription_canceled` - Assinatura cancelada

### Fixtures de Mock

- `mock_stripe_customer` - Mock de customer do Stripe
- `mock_stripe_subscription` - Mock de subscription do Stripe
- `mock_stripe_webhook_event` - Mock de webhook event

## Exemplos de Testes

### Testar Model

```python
def test_create_subscription(app, db_session, test_client_user):
    """Testar criação de assinatura"""
    with app.app_context():
        subscription = Subscription(
            client_id=test_client_user.id,
            plan='basic',
            status='trialing'
        )
        db.session.add(subscription)
        db.session.commit()

        assert subscription.id is not None
        assert subscription.plan == 'basic'
```

### Testar Rota

```python
def test_get_plans(client):
    """Testar listagem de planos"""
    response = client.get('/api/subscriptions/plans')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'plans' in data
    assert len(data['plans']) == 3
```

### Testar Decorator

```python
def test_subscription_required_without_subscription(client, auth_headers):
    """Testar acesso sem assinatura"""
    response = client.get('/test/protected-route', headers=auth_headers)

    assert response.status_code == 403
    data = json.loads(response.data)
    assert data['code'] == 'SUBSCRIPTION_REQUIRED'
```

### Testar com Mock do Stripe

```python
@patch('stripe.Customer.create')
def test_create_subscription(mock_create, client, auth_headers):
    """Testar criação com mock do Stripe"""
    mock_create.return_value = MagicMock(id='cus_test123')

    response = client.post(
        '/api/subscriptions/subscribe',
        headers=auth_headers,
        json={'plan': 'pro'}
    )

    assert response.status_code == 201
    mock_create.assert_called_once()
```

## Cobertura de Testes

### Model Subscription (test_subscription_model.py)

✅ **24 testes**
- Criação de assinatura
- Conversão para dicionário
- Verificação de status ativo
- Acesso a features
- Relacionamento com cliente
- Unicidade de stripe_subscription_id
- Deleção em cascata
- Timestamps
- Valores de planos e status
- Consultas por cliente e status

### Rotas (test_subscription_routes.py)

✅ **23 testes**
- Listagem de planos
- Status de assinatura (com/sem assinatura)
- Criação de assinatura
- Cancelamento
- Reativação
- Webhooks (paid, failed, deleted, updated)
- Validações de autenticação
- Tratamento de erros

### Decorator (test_subscription_decorator.py)

✅ **17 testes**
- Acesso sem autenticação
- Acesso sem assinatura
- Acesso com diferentes status
- Verificação de planos específicos
- Check de features
- Mensagens de erro
- Integração com múltiplos usuários

**Total: 64 testes**

## Mocks do Stripe

Para evitar chamadas reais à API do Stripe durante os testes, usamos mocks:

```python
from unittest.mock import patch, MagicMock

@patch('stripe.Customer.create')
@patch('stripe.Subscription.create')
def test_with_stripe_mock(mock_sub, mock_cust, client):
    mock_cust.return_value = MagicMock(id='cus_test')
    mock_sub.return_value = MagicMock(
        id='sub_test',
        status='trialing'
    )

    # Seu teste aqui
```

## Variáveis de Ambiente para Testes

As fixtures configuram automaticamente variáveis de teste:

```python
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['STRIPE_SECRET_KEY'] = 'sk_test_mock_key'
os.environ['STRIPE_WEBHOOK_SECRET'] = 'whsec_test_mock_secret'
```

## Boas Práticas

### 1. Use Fixtures

```python
# Ruim
def test_something():
    client = create_client()
    subscription = create_subscription()
    # ...

# Bom
def test_something(test_client_user, test_subscription):
    # Use as fixtures
```

### 2. Teste um Comportamento por Teste

```python
# Ruim
def test_subscription():
    # Testa criação
    # Testa atualização
    # Testa deleção

# Bom
def test_create_subscription():
    # Apenas criação

def test_update_subscription():
    # Apenas atualização
```

### 3. Use Nomes Descritivos

```python
# Ruim
def test_1():
    pass

# Bom
def test_subscription_required_without_active_subscription():
    pass
```

### 4. Mock Chamadas Externas

```python
# Sempre mock chamadas ao Stripe
@patch('stripe.Customer.create')
def test_create_customer(mock_create):
    # Teste sem chamar Stripe de verdade
```

### 5. Limpe Após os Testes

```python
@pytest.fixture
def cleanup():
    yield
    # Código de limpeza aqui
```

## Testes de Integração

Para testes de integração com Stripe real (opcional):

```bash
# Configure variáveis reais
export STRIPE_SECRET_KEY=sk_test_real_key
export STRIPE_WEBHOOK_SECRET=whsec_real_secret

# Execute com flag de integração
pytest -m integration
```

## Debugging de Testes

### Ver Output de Print

```bash
pytest -s
```

### Parar no Primeiro Erro

```bash
pytest -x
```

### Executar Último Teste que Falhou

```bash
pytest --lf
```

### Usar Debugger

```python
def test_something():
    import pdb; pdb.set_trace()
    # Seu código
```

## CI/CD

Exemplo de configuração para GitHub Actions:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: pytest --cov=src
```

## Estatísticas de Cobertura

Meta de cobertura: **> 80%**

Verificar cobertura:

```bash
pytest --cov=src --cov-report=term-missing
```

## Testes Adicionais Recomendados

### Testes de Performance

```python
import time

def test_subscription_query_performance(db_session):
    start = time.time()
    # Query
    end = time.time()
    assert (end - start) < 0.1  # Menos de 100ms
```

### Testes de Segurança

```python
def test_subscription_sql_injection(client):
    response = client.get('/api/subscriptions/status?id=1; DROP TABLE subscriptions;')
    assert response.status_code != 500
```

### Testes de Carga

```python
def test_concurrent_subscriptions(client):
    import threading
    results = []

    def create_sub():
        response = client.post('/api/subscriptions/subscribe')
        results.append(response.status_code)

    threads = [threading.Thread(target=create_sub) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
```

## Troubleshooting

### Erro: "No module named 'pytest'"

```bash
pip install pytest
```

### Erro: "Database locked"

Use SQLite em memória para testes:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
```

### Erro: "Stripe API key invalid"

Os testes usam mocks. Verifique se os patches estão corretos.

### Testes Lentos

Use `-n auto` para paralelização:

```bash
pip install pytest-xdist
pytest -n auto
```

## Recursos Adicionais

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Última atualização:** 2025-10-30
