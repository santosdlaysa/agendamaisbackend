# 📊 Estrutura Completa do Banco de Dados - AgendaMais Backend

## 🎯 TABELAS DE SUBSCRIPTION (Sistema SaaS com Stripe)

### 1. **SUBSCRIPTIONS** (Assinaturas)
Gerencia os planos de assinatura SaaS dos clientes com integração Stripe

**Colunas:**
```sql
- id                      INTEGER PRIMARY KEY (auto-increment)
- client_id               INTEGER NOT NULL (FK → clients.id)
- plan                    VARCHAR(50) NOT NULL ('basic', 'pro', 'enterprise')
- stripe_customer_id      VARCHAR(100)
- stripe_subscription_id  VARCHAR(100) UNIQUE
- status                  VARCHAR(20) NOT NULL DEFAULT 'trialing'
                         ('active', 'past_due', 'canceled', 'trialing')
- start_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- end_date               TIMESTAMP
- trial_end              TIMESTAMP
- cancel_at_period_end   BOOLEAN DEFAULT FALSE
- created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Criação da Tabela:**
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    plan VARCHAR(50) NOT NULL,
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100) UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'trialing',
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    trial_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT chk_plan CHECK (plan IN ('basic', 'pro', 'enterprise')),
    CONSTRAINT chk_status CHECK (status IN ('active', 'past_due', 'canceled', 'trialing'))
);

-- Índices para a tabela subscriptions
CREATE INDEX idx_subscriptions_client_id ON subscriptions(client_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_stripe_customer_id ON subscriptions(stripe_customer_id);
CREATE INDEX idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);
```

**Relacionamentos:**
- `client_id` → CASCADE DELETE de `clients`
- Um cliente pode ter uma assinatura (1:1)

---

## 👥 TABELAS CORE DO SISTEMA

### 2. **USERS** (Usuários/Administradores)
Armazena contas de administradores e usuários do sistema

**Colunas:**
```sql
- id            INTEGER PRIMARY KEY (auto-increment)
- name          VARCHAR(255) NOT NULL
- email         VARCHAR(255) NOT NULL UNIQUE
- password_hash VARCHAR(255) NOT NULL
- role          VARCHAR(50) NOT NULL DEFAULT 'admin'
- active        BOOLEAN DEFAULT TRUE
- created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Criação da Tabela:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'admin',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para a tabela users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(active);
```

**Relacionamentos:**
- Tabela independente para autenticação

---

### 3. **CLIENTS** (Clientes)
Armazena informações dos clientes/pacientes

**Colunas:**
```sql
- id         INTEGER PRIMARY KEY (auto-increment)
- name       VARCHAR(255) NOT NULL
- phone      VARCHAR(20)
- email      VARCHAR(255)
- notes      TEXT
- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Criação da Tabela:**
```sql
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para a tabela clients
CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_phone ON clients(phone);
```

**Relacionamentos:**
- Um para muitos com `appointments` (cliente tem múltiplos agendamentos)
- Um para um com `subscriptions` (cliente tem uma assinatura)

---

### 4. **PROFESSIONALS** (Profissionais)
Armazena informações dos prestadores de serviço

**Colunas:**
```sql
- id         INTEGER PRIMARY KEY (auto-increment)
- name       VARCHAR(255) NOT NULL
- role       VARCHAR(255) NOT NULL
- phone      VARCHAR(20)
- email      VARCHAR(255)
- color      VARCHAR(7) DEFAULT '#3B82F6' (cor hexadecimal para calendário)
- active     BOOLEAN DEFAULT TRUE
- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Criação da Tabela:**
```sql
CREATE TABLE professionals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    color VARCHAR(7) DEFAULT '#3B82F6',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para a tabela professionals
CREATE INDEX idx_professionals_name ON professionals(name);
CREATE INDEX idx_professionals_active ON professionals(active);
CREATE INDEX idx_professionals_email ON professionals(email);
```

**Relacionamentos:**
- Um para muitos com `appointments`
- Muitos para muitos com `services` através de `professional_services`

---

### 5. **SERVICES** (Serviços)
Armazena os serviços/tratamentos oferecidos

**Colunas:**
```sql
- id          INTEGER PRIMARY KEY (auto-increment)
- name        VARCHAR(255) NOT NULL
- description TEXT
- price       DECIMAL(10,2) NOT NULL
- duration    INTEGER NOT NULL (duração em minutos)
- color       VARCHAR(7) DEFAULT '#10B981' (cor hexadecimal para calendário)
- active      BOOLEAN DEFAULT TRUE
- created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Criação da Tabela:**
```sql
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    duration INTEGER NOT NULL,
    color VARCHAR(7) DEFAULT '#10B981',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para a tabela services
CREATE INDEX idx_services_name ON services(name);
CREATE INDEX idx_services_active ON services(active);
CREATE INDEX idx_services_price ON services(price);
```

**Relacionamentos:**
- Um para muitos com `appointments`
- Muitos para muitos com `professionals` através de `professional_services`

---

### 6. **PROFESSIONAL_SERVICES** (Tabela de Associação)
Relaciona profissionais aos serviços que podem prestar

**Colunas:**
```sql
- professional_id INTEGER NOT NULL (FK → professionals.id)
- service_id      INTEGER NOT NULL (FK → services.id)
```

**Criação da Tabela:**
```sql
CREATE TABLE professional_services (
    professional_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    PRIMARY KEY (professional_id, service_id),
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
);

-- Índices para a tabela professional_services
CREATE INDEX idx_professional_services_professional ON professional_services(professional_id);
CREATE INDEX idx_professional_services_service ON professional_services(service_id);
```

**Relacionamentos:**
- CASCADE DELETE de ambos `professionals` e `services`

---

### 7. **APPOINTMENTS** (Agendamentos)
Armazena os agendamentos/consultas

**Colunas:**
```sql
- id                 INTEGER PRIMARY KEY (auto-increment)
- client_id          INTEGER NOT NULL (FK → clients.id)
- professional_id    INTEGER NOT NULL (FK → professionals.id)
- service_id         INTEGER NOT NULL (FK → services.id)
- appointment_date   DATE NOT NULL
- start_time         TIME NOT NULL
- end_time           TIME NOT NULL
- status             VARCHAR(50) DEFAULT 'scheduled'
                    ('scheduled', 'completed', 'cancelled', 'no_show', 'confirmed')
- notes              TEXT
- price              DECIMAL(10,2)
- payment_method     VARCHAR(50) (adicionado via migração)
- notification_sent  BOOLEAN DEFAULT FALSE
- reminder_sent      BOOLEAN DEFAULT FALSE
- created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Criação da Tabela:**
```sql
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    professional_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT,
    price DECIMAL(10,2),
    payment_method VARCHAR(50),
    notification_sent BOOLEAN DEFAULT FALSE,
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE RESTRICT,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE RESTRICT,
    CONSTRAINT chk_status CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show', 'confirmed'))
);

-- Índices para a tabela appointments
CREATE INDEX idx_appointments_client ON appointments(client_id);
CREATE INDEX idx_appointments_professional ON appointments(professional_id);
CREATE INDEX idx_appointments_service ON appointments(service_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_datetime ON appointments(appointment_date, start_time);
CREATE INDEX idx_appointments_professional_date ON appointments(professional_id, appointment_date);
```

**Relacionamentos:**
- `client_id` → CASCADE DELETE de `clients`
- `professional_id` → RESTRICT DELETE de `professionals`
- `service_id` → RESTRICT DELETE de `services`

---

## 🔧 TRIGGERS DO BANCO DE DADOS

### Função `update_updated_at_column()`
Atualiza automaticamente o timestamp `updated_at` quando um registro é modificado

```sql
-- Função para atualizar o campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

**Triggers criados:**
```sql
-- Trigger para users
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para clients
CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para professionals
CREATE TRIGGER update_professionals_updated_at
    BEFORE UPDATE ON professionals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para services
CREATE TRIGGER update_services_updated_at
    BEFORE UPDATE ON services
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para appointments
CREATE TRIGGER update_appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para subscriptions
CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 📊 RESUMO ESTATÍSTICO

- **Total de Tabelas:** 7
  - 1 tabela de Subscription (integração Stripe)
  - 6 tabelas Core (incluindo 1 tabela de associação)

- **Total de Índices:** 26

- **Total de Triggers:** 6

- **Banco de Dados:** PostgreSQL (produção) / SQLite (desenvolvimento)

---

## 🎨 RECURSOS PRINCIPAIS

1. ✅ **Gerenciamento automático de timestamps** via triggers
2. ✅ **Deleção em cascata** para dados relacionados ao cliente
3. ✅ **Restrição de deleção** para profissionais/serviços com agendamentos
4. ✅ **Integração completa com Stripe** para pagamentos e assinaturas
5. ✅ **Sistema de cores** para visualização em calendário
6. ✅ **Sistema de rastreamento de notificações**
7. ✅ **Gerenciamento flexível de assinaturas** com períodos de teste
8. ✅ **Planos SaaS** (basic, pro, enterprise)

---

## 🔗 DIAGRAMA DE RELACIONAMENTOS

```
┌─────────────┐
│    USERS    │  (Autenticação Independente)
└─────────────┘

┌─────────────┐         ┌──────────────────┐
│   CLIENTS   │ ◄─────► │  SUBSCRIPTIONS   │  (Integração Stripe)
│     (1)     │  1:1    │       (1)        │
└──────┬──────┘         └──────────────────┘
       │
       │ 1:N
       ▼
┌──────────────┐
│ APPOINTMENTS │
│     (N)      │
└──────┬───┬───┘
       │   │
   N:1 │   │ N:1
       │   │
       ▼   ▼
┌──────────────┐         ┌──────────────────────────┐         ┌──────────────┐
│PROFESSIONALS │ ◄─────► │ PROFESSIONAL_SERVICES    │ ◄─────► │   SERVICES   │
│     (1)      │   N:M   │     (Junction Table)     │   N:M   │      (1)     │
└──────────────┘         └──────────────────────────┘         └──────────────┘
```

**Legenda:**
- `1:1` = Relacionamento um-para-um
- `1:N` = Relacionamento um-para-muitos
- `N:M` = Relacionamento muitos-para-muitos
- `◄───►` = Relacionamento bidirecional

---

## 🚀 SCRIPT COMPLETO DE CRIAÇÃO DO BANCO

Execute os comandos abaixo na ordem para criar todo o banco de dados:

```sql
-- ============================================
-- 1. CRIAR FUNÇÃO DE TRIGGER
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- 2. CRIAR TABELAS
-- ============================================

-- Tabela USERS
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'admin',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela CLIENTS
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela SUBSCRIPTIONS
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    plan VARCHAR(50) NOT NULL,
    stripe_customer_id VARCHAR(100),
    stripe_subscription_id VARCHAR(100) UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'trialing',
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    trial_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT chk_plan CHECK (plan IN ('basic', 'pro', 'enterprise')),
    CONSTRAINT chk_status CHECK (status IN ('active', 'past_due', 'canceled', 'trialing'))
);

-- Tabela PROFESSIONALS
CREATE TABLE professionals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    color VARCHAR(7) DEFAULT '#3B82F6',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela SERVICES
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    duration INTEGER NOT NULL,
    color VARCHAR(7) DEFAULT '#10B981',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela PROFESSIONAL_SERVICES (Junction)
CREATE TABLE professional_services (
    professional_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    PRIMARY KEY (professional_id, service_id),
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
);

-- Tabela APPOINTMENTS
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    professional_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT,
    price DECIMAL(10,2),
    payment_method VARCHAR(50),
    notification_sent BOOLEAN DEFAULT FALSE,
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE RESTRICT,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE RESTRICT,
    CONSTRAINT chk_status CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show', 'confirmed'))
);

-- ============================================
-- 3. CRIAR ÍNDICES
-- ============================================

-- Índices USERS
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(active);

-- Índices CLIENTS
CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_phone ON clients(phone);

-- Índices SUBSCRIPTIONS
CREATE INDEX idx_subscriptions_client_id ON subscriptions(client_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_stripe_customer_id ON subscriptions(stripe_customer_id);
CREATE INDEX idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);

-- Índices PROFESSIONALS
CREATE INDEX idx_professionals_name ON professionals(name);
CREATE INDEX idx_professionals_active ON professionals(active);
CREATE INDEX idx_professionals_email ON professionals(email);

-- Índices SERVICES
CREATE INDEX idx_services_name ON services(name);
CREATE INDEX idx_services_active ON services(active);
CREATE INDEX idx_services_price ON services(price);

-- Índices PROFESSIONAL_SERVICES
CREATE INDEX idx_professional_services_professional ON professional_services(professional_id);
CREATE INDEX idx_professional_services_service ON professional_services(service_id);

-- Índices APPOINTMENTS
CREATE INDEX idx_appointments_client ON appointments(client_id);
CREATE INDEX idx_appointments_professional ON appointments(professional_id);
CREATE INDEX idx_appointments_service ON appointments(service_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_datetime ON appointments(appointment_date, start_time);
CREATE INDEX idx_appointments_professional_date ON appointments(professional_id, appointment_date);

-- ============================================
-- 4. CRIAR TRIGGERS
-- ============================================

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_professionals_updated_at
    BEFORE UPDATE ON professionals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_services_updated_at
    BEFORE UPDATE ON services
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at
    BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## 📝 DADOS INICIAIS (Opcional)

```sql
-- Inserir usuário administrador padrão (senha: admin123)
INSERT INTO users (name, email, password_hash, role)
VALUES ('Administrador', 'admin@agendamais.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfAoNtMy7QkldyG', 'admin');

-- Inserir alguns serviços padrão
INSERT INTO services (name, description, price, duration, color) VALUES
('Corte de Cabelo', 'Corte de cabelo masculino e feminino', 30.00, 30, '#3B82F6'),
('Manicure', 'Cuidados com as unhas das mãos', 25.00, 45, '#10B981'),
('Pedicure', 'Cuidados com as unhas dos pés', 30.00, 60, '#F59E0B'),
('Sobrancelha', 'Design de sobrancelhas', 20.00, 20, '#EF4444');

-- Inserir profissional padrão
INSERT INTO professionals (name, role, email, color) VALUES
('Maria Silva', 'Cabeleireira', 'maria@agendamais.com', '#8B5CF6');

-- Vincular profissional aos serviços
INSERT INTO professional_services (professional_id, service_id)
SELECT 1, id FROM services WHERE name IN ('Corte de Cabelo', 'Sobrancelha');
```

---

## 🔍 CONSULTAS ÚTEIS

### Verificar agendamentos de um profissional
```sql
SELECT
    a.id,
    a.appointment_date,
    a.start_time,
    a.end_time,
    c.name as client_name,
    s.name as service_name,
    a.status,
    a.price,
    a.payment_method
FROM appointments a
JOIN clients c ON a.client_id = c.id
JOIN services s ON a.service_id = s.id
WHERE a.professional_id = ? AND a.appointment_date = ?
ORDER BY a.start_time;
```

### Verificar assinatura ativa de um cliente
```sql
SELECT
    c.name as client_name,
    sub.plan,
    sub.status,
    sub.start_date,
    sub.end_date,
    sub.trial_end,
    sub.stripe_subscription_id
FROM subscriptions sub
JOIN clients c ON sub.client_id = c.id
WHERE c.id = ? AND sub.status = 'active';
```

### Relatório de receita por período
```sql
SELECT
    DATE_TRUNC('month', a.appointment_date) as month,
    COUNT(*) as total_appointments,
    SUM(CASE WHEN a.status = 'completed' THEN a.price ELSE 0 END) as revenue,
    SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END) as no_shows
FROM appointments a
WHERE a.appointment_date BETWEEN ? AND ?
GROUP BY DATE_TRUNC('month', a.appointment_date)
ORDER BY month;
```

### Listar clientes com assinaturas expiradas
```sql
SELECT
    c.id,
    c.name,
    c.email,
    sub.plan,
    sub.status,
    sub.end_date
FROM clients c
JOIN subscriptions sub ON c.id = sub.client_id
WHERE sub.status = 'canceled'
   OR (sub.end_date IS NOT NULL AND sub.end_date < CURRENT_TIMESTAMP);
```

---

## ⚠️ TABELAS PLANEJADAS (Não Implementadas)

As seguintes tabelas são referenciadas no código mas ainda não foram implementadas:

### REMINDER (Sistema de Lembretes Automáticos)
**Status:** Planejado, não implementado

**Propósito:** Gerenciar lembretes automáticos para agendamentos

**Estrutura Proposta:**
```sql
CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    appointment_id INTEGER NOT NULL,
    reminder_time TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);
```

### REMINDER_SETTINGS (Configurações de Lembretes)
**Status:** Planejado, não implementado

**Propósito:** Armazenar configurações personalizadas de lembretes

**Estrutura Proposta:**
```sql
CREATE TABLE reminder_settings (
    id SERIAL PRIMARY KEY,
    client_id INTEGER,
    advance_notice_hours INTEGER DEFAULT 24,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
```

**Nota:** O código trata gracefully a ausência desses módulos:
```
Warning: Could not import reminder models: No module named 'src.models.reminder'
Warning: Reminder functionality not available: No module named 'src.app.main.reminder'
```

---

## 📚 REFERÊNCIAS E DOCUMENTAÇÃO

- **API Documentation:** `API_DOCUMENTATION.md`
- **Subscription Documentation:**
  - `SUBSCRIPTION_API.md`
  - `SUBSCRIPTION_IMPLEMENTATION_GUIDE.md`
  - `SUBSCRIPTION_SETUP.md`
  - `SUBSCRIPTION_TESTING_GUIDE.md`
  - `SUBSCRIPTION_USAGE_EXAMPLES.md`
- **Schema Prisma:** `schema.prisma`
- **Setup Guide:** `SETUP.md`
- **Migration Script:** `migrate_payment_method.py`

---

## 🔐 CONSIDERAÇÕES DE SEGURANÇA

1. **Senhas**: Armazenadas como hash usando bcrypt (`password_hash`)
2. **Dados do Stripe**: `stripe_customer_id` e `stripe_subscription_id` são sensíveis
3. **LGPD**: Email e telefone de clientes devem seguir regulamentação
4. **Notas**: Campo `notes` pode conter informações sensíveis
5. **Tokens JWT**: Não armazenados no banco (apenas em memória/cookies)

---

## 🛠️ INSTRUÇÕES DE SETUP

### 1. Criar Banco PostgreSQL
```bash
# Criar banco de dados
createdb agendamais

# Conectar ao banco
psql agendamais

# Executar script de criação
\i database_setup.sql
```

### 2. Configurar Variáveis de Ambiente
```env
DATABASE_URL=postgresql://user:password@localhost:5432/agendamais
SECRET_KEY=sua_chave_secreta_aqui
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Executar Migrações
```bash
# Via Python
python migrate_payment_method.py

# Ou via NPM
npm run migrate
```

### 4. Iniciar Aplicação
```bash
# Via Python
python run.py

# Ou via NPM
npm start
```

---

**Versão do Documento:** 2.0
**Última Atualização:** 2025-11-06
**Banco de Dados:** PostgreSQL 12+ / SQLite 3+
**Framework ORM:** SQLAlchemy 2.0.43
**Payment Gateway:** Stripe API v13.1.0
