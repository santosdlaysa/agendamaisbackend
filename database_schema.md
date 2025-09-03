# Schema do Banco de Dados - Sistema de Agendamento

Este documento contém todas as declarações SQL necessárias para criar as tabelas do banco de dados do sistema de agendamento.

## 1. Tabela de Usuários (users)

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

## 2. Tabela de Clientes (clients)

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

## 3. Tabela de Profissionais (professionals)

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

## 4. Tabela de Serviços (services)

```sql
CREATE TABLE services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    duration INTEGER NOT NULL, -- duração em minutos
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

## 5. Tabela de Relacionamento Profissional-Serviços (professional_services)

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

## 6. Tabela de Agendamentos (appointments)

```sql
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    professional_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, completed, cancelled, no_show
    notes TEXT,
    price DECIMAL(10,2),
    notification_sent BOOLEAN DEFAULT FALSE,
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE RESTRICT,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE RESTRICT
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

## 7. Triggers para Atualização Automática de Timestamps

```sql
-- Função para atualizar o campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para cada tabela
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at 
    BEFORE UPDATE ON clients 
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

## 8. Dados Iniciais (Opcional)

```sql
-- Inserir usuário administrador padrão
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

## 9. Consultas Úteis

```sql
-- Verificar agendamentos de um profissional em uma data específica
SELECT 
    a.id,
    a.appointment_date,
    a.start_time,
    a.end_time,
    c.name as client_name,
    s.name as service_name,
    a.status
FROM appointments a
JOIN clients c ON a.client_id = c.id
JOIN services s ON a.service_id = s.id
WHERE a.professional_id = ? AND a.appointment_date = ?
ORDER BY a.start_time;

-- Buscar horários disponíveis de um profissional
SELECT 
    p.name as professional_name,
    ps.service_id,
    s.name as service_name,
    s.duration
FROM professionals p
JOIN professional_services ps ON p.id = ps.professional_id
JOIN services s ON ps.service_id = s.id
WHERE p.id = ? AND p.active = true AND s.active = true;

-- Relatório de agendamentos por período
SELECT 
    DATE_TRUNC('month', a.appointment_date) as month,
    COUNT(*) as total_appointments,
    SUM(CASE WHEN a.status = 'completed' THEN a.price ELSE 0 END) as revenue
FROM appointments a
WHERE a.appointment_date BETWEEN ? AND ?
GROUP BY DATE_TRUNC('month', a.appointment_date)
ORDER BY month;
```

## Notas Importantes

1. **PostgreSQL**: Este schema foi criado para PostgreSQL. Para outros SGBDs, ajuste os tipos de dados conforme necessário.

2. **Senhas**: A senha padrão do usuário administrador é `admin123`. Certifique-se de alterá-la após a configuração inicial.

3. **Chaves Estrangeiras**: 
   - Agendamentos são deletados em cascata quando um cliente é removido
   - Agendamentos são restritos quando um profissional ou serviço é removido

4. **Índices**: Os índices foram criados para otimizar as consultas mais comuns do sistema.

5. **Triggers**: Os triggers garantem que o campo `updated_at` seja atualizado automaticamente em todas as modificações.

6. **Status dos Agendamentos**: 
   - `scheduled`: Agendado
   - `completed`: Concluído
   - `cancelled`: Cancelado
   - `no_show`: Cliente não compareceu

7. **Cores**: As cores são armazenadas em formato hexadecimal (#RRGGBB) para identificação visual no calendário.