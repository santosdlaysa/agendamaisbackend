# Guia de Configuração de Variáveis de Ambiente - Stripe

## Onde Obter as Variáveis do Stripe

### STRIPE_SECRET_KEY

**O que é:** Chave secreta para autenticação na API do Stripe (backend).

**Como obter:**

1. Acesse https://dashboard.stripe.com
2. Faça login ou crie uma conta
3. Ative o **modo de teste** (toggle no canto superior direito)
4. No menu lateral, vá em **Developers** > **API keys**
5. Copie a **Secret key** (começa com `sk_test_...`)

**Onde usar:**
```env
STRIPE_SECRET_KEY=sk_test_51234567890abcdef...
```

⚠️ **IMPORTANTE:** Nunca commit esta chave no Git!

---

### STRIPE_WEBHOOK_SECRET

**O que é:** Secret usado para validar webhooks do Stripe.

#### Opção A: Desenvolvimento Local (Recomendado)

**Usando Stripe CLI:**

1. Instalar Stripe CLI:

   **Windows - Opção A (Recomendado):**
   ```powershell
   # Baixe o instalador MSI
   # https://github.com/stripe/stripe-cli/releases/latest
   # Arquivo: stripe_X.X.X_windows_x86_64.msi
   # Execute o instalador e siga o assistente
   ```

   **Windows - Opção B (Scoop):**
   ```powershell
   # Se você não tem Scoop, instale primeiro:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

   # Depois instale Stripe CLI:
   scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
   scoop install stripe
   ```

   **Mac:**
   ```bash
   brew install stripe/stripe-cli/stripe
   ```

   **Linux:**
   ```bash
   # Veja: https://stripe.com/docs/stripe-cli#install
   ```

2. Fazer login:
   ```bash
   stripe login
   ```

3. Iniciar webhook listener:
   ```bash
   stripe listen --forward-to localhost:5000/api/subscriptions/webhook
   ```

4. Copie o **webhook signing secret** exibido no console (começa com `whsec_...`)

**Onde usar:**
```env
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef...
```

#### Opção B: Produção

1. Acesse https://dashboard.stripe.com
2. Vá em **Developers** > **Webhooks**
3. Clique em **Add endpoint**
4. Configure:
   - **Endpoint URL:** `https://seu-dominio.com/api/subscriptions/webhook`
   - **Events to send:**
     - `invoice.paid`
     - `invoice.payment_failed`
     - `customer.subscription.deleted`
     - `customer.subscription.updated`
     - `customer.subscription.trial_will_end`
5. Clique em **Add endpoint**
6. Na página do webhook, clique em **Reveal** no campo **Signing secret**
7. Copie o secret (começa com `whsec_...`)

---

### STRIPE_PRICE_BASIC

**O que é:** ID do preço do plano Básico no Stripe.

**Como criar:**

1. Acesse https://dashboard.stripe.com
2. Vá em **Products** (Produtos)
3. Clique em **Create product** (Criar produto)
4. Configure:
   - **Name:** Plano Básico AgendaMais
   - **Description:** Até 100 agendamentos/mês, 3 profissionais
   - **Pricing model:** Standard pricing
   - **Price:** R$ 29,00 (ou BRL 29.00)
   - **Billing period:** Monthly (Mensal)
5. Clique em **Save product**
6. Na lista de produtos, clique no produto criado
7. Na seção **Pricing**, copie o **API ID** (começa com `price_...`)

**Onde usar:**
```env
STRIPE_PRICE_BASIC=price_1234567890abcdef...
```

---

### STRIPE_PRICE_PRO

**O que é:** ID do preço do plano Pro no Stripe.

**Como criar:**

Siga os mesmos passos do STRIPE_PRICE_BASIC, mas com:
- **Name:** Plano Pro AgendaMais
- **Description:** Agendamentos ilimitados, 10 profissionais, WhatsApp/SMS
- **Price:** R$ 59,00 (ou BRL 59.00)

**Onde usar:**
```env
STRIPE_PRICE_PRO=price_0987654321fedcba...
```

---

### STRIPE_PRICE_ENTERPRISE

**O que é:** ID do preço do plano Enterprise no Stripe.

**Como criar:**

Siga os mesmos passos do STRIPE_PRICE_BASIC, mas com:
- **Name:** Plano Enterprise AgendaMais
- **Description:** Tudo ilimitado, API personalizada, suporte 24/7
- **Price:** R$ 99,00 (ou BRL 99.00)

**Onde usar:**
```env
STRIPE_PRICE_ENTERPRISE=price_abcdef1234567890...
```

---

### DATABASE_URL

**O que é:** URL de conexão com o banco de dados PostgreSQL.

**Formato:**
```
postgresql://usuario:senha@host:porta/nome_banco
```

#### Opção A: PostgreSQL Local

```env
DATABASE_URL=postgresql://postgres:sua_senha@localhost:5432/agendamais
```

**Como configurar:**

1. Instale PostgreSQL: https://www.postgresql.org/download/
2. Crie o banco de dados:
   ```bash
   psql -U postgres
   CREATE DATABASE agendamais;
   \q
   ```
3. Use a URL acima substituindo `sua_senha`

#### Opção B: SQLite (Desenvolvimento apenas)

```env
DATABASE_URL=sqlite:///agendamento.db
```

**Vantagem:** Não precisa instalar PostgreSQL
**Desvantagem:** Não recomendado para produção

#### Opção C: Heroku

```bash
# Heroku fornece automaticamente
heroku config:get DATABASE_URL --app seu-app
```

Copie o valor retornado.

#### Opção D: Render

1. Acesse https://dashboard.render.com
2. Vá no seu serviço de banco de dados
3. Na aba **Connect**, copie a **External Database URL**

```env
DATABASE_URL=postgresql://user:pass@dpg-xxxxx.render.com/dbname
```

#### Opção E: Railway

1. Acesse https://railway.app
2. Vá no seu projeto
3. Clique no serviço PostgreSQL
4. Copie a **DATABASE_URL** da aba **Connect**

```env
DATABASE_URL=postgresql://postgres:pass@containers-us-west-xxx.railway.app:5432/railway
```

#### Opção F: Supabase

1. Acesse https://app.supabase.com
2. Vá no seu projeto
3. Settings > Database > Connection string
4. Copie a **URI** e substitua `[YOUR-PASSWORD]` pela sua senha

```env
DATABASE_URL=postgresql://postgres:SuaSenha@db.xxxxx.supabase.co:5432/postgres
```

---

## Arquivo .env Completo

Após obter todas as variáveis, seu arquivo `.env` deve ficar assim:

```env
# Chaves gerais
SECRET_KEY=sua-secret-key-aqui
JWT_SECRET_KEY=sua-jwt-secret-aqui
FLASK_ENV=development

# Banco de dados
DATABASE_URL=postgresql://postgres:senha@localhost:5432/agendamais

# Stripe
STRIPE_SECRET_KEY=sk_test_51234567890abcdef...
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef...

# IDs dos preços no Stripe
STRIPE_PRICE_BASIC=price_1234567890abcdef...
STRIPE_PRICE_PRO=price_0987654321fedcba...
STRIPE_PRICE_ENTERPRISE=price_abcdef1234567890...

# Twilio (opcional - para WhatsApp/SMS)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_FROM=+14155238886
TWILIO_SMS_FROM=+1234567890
```

---

## Checklist de Configuração

### Desenvolvimento Local

- [ ] Criar conta no Stripe
- [ ] Ativar modo de teste
- [ ] Copiar STRIPE_SECRET_KEY
- [ ] Instalar Stripe CLI
- [ ] Obter STRIPE_WEBHOOK_SECRET com `stripe listen`
- [ ] Criar 3 produtos no Stripe (Básico, Pro, Enterprise)
- [ ] Copiar IDs dos preços (STRIPE_PRICE_*)
- [ ] Configurar DATABASE_URL (PostgreSQL ou SQLite)
- [ ] Copiar .env.example para .env
- [ ] Preencher todas as variáveis no .env

### Produção

- [ ] Mudar para modo live no Stripe
- [ ] Obter chaves de produção (sk_live_...)
- [ ] Criar produtos no modo live
- [ ] Configurar webhook no Stripe Dashboard
- [ ] Obter STRIPE_WEBHOOK_SECRET de produção
- [ ] Configurar DATABASE_URL de produção
- [ ] Adicionar variáveis no serviço de hospedagem (Heroku/Render/etc)

---

## Segurança

### ⚠️ NÃO FAÇA:

- ❌ Commit arquivo .env no Git
- ❌ Compartilhar chaves secretas
- ❌ Usar chaves de teste em produção
- ❌ Usar chaves de produção em desenvolvimento

### ✅ FAÇA:

- ✅ Adicione .env no .gitignore
- ✅ Use variáveis de ambiente no servidor
- ✅ Rotate chaves periodicamente
- ✅ Use modo de teste para desenvolvimento
- ✅ Mantenha .env.example atualizado (sem valores reais)

---

## Troubleshooting

### Erro: "Invalid API key"

**Causa:** STRIPE_SECRET_KEY incorreta ou não configurada

**Solução:**
1. Verifique se copiou a chave correta do dashboard
2. Certifique-se de que está no modo correto (test/live)
3. Verifique se não há espaços extras na chave

### Erro: "Webhook signature verification failed"

**Causa:** STRIPE_WEBHOOK_SECRET incorreto

**Solução:**
1. Para desenvolvimento: reinicie `stripe listen` e copie o novo secret
2. Para produção: verifique o secret no Stripe Dashboard

### Erro: "Price not found"

**Causa:** IDs dos preços (STRIPE_PRICE_*) incorretos

**Solução:**
1. Acesse Stripe Dashboard > Products
2. Clique no produto
3. Copie o correto API ID da seção Pricing

### Erro: "Could not connect to database"

**Causa:** DATABASE_URL incorreta

**Solução:**
1. Verifique formato: `postgresql://user:pass@host:port/dbname`
2. Teste conexão: `psql "postgresql://user:pass@host:port/dbname"`
3. Verifique se o banco de dados existe

---

## Recursos Adicionais

- [Stripe API Keys](https://stripe.com/docs/keys)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)

---

**Última atualização:** 2025-10-30
