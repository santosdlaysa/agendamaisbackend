-- ============================================
-- Migration: Expandir Sistema de Agendamento Online
-- Data: 2025-01-06
-- Descrição: Adiciona configurações avançadas de agendamento,
--            horários de trabalho e sistema de confirmação
-- ============================================

-- ============================================
-- 1. ADICIONAR CAMPOS DE CONFIGURAÇÃO NA TABELA USERS
-- ============================================

-- Configurações de agendamento online
ALTER TABLE users ADD COLUMN IF NOT EXISTS booking_min_advance_hours INTEGER DEFAULT 2;
ALTER TABLE users ADD COLUMN IF NOT EXISTS booking_max_advance_days INTEGER DEFAULT 30;
ALTER TABLE users ADD COLUMN IF NOT EXISTS booking_slot_interval INTEGER DEFAULT 30;
ALTER TABLE users ADD COLUMN IF NOT EXISTS booking_start_hour INTEGER DEFAULT 8;
ALTER TABLE users ADD COLUMN IF NOT EXISTS booking_end_hour INTEGER DEFAULT 18;
ALTER TABLE users ADD COLUMN IF NOT EXISTS booking_require_confirmation BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS booking_allow_cancellation BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS booking_cancellation_min_hours INTEGER DEFAULT 2;

-- Comentários nas colunas
COMMENT ON COLUMN users.booking_min_advance_hours IS 'Antecedência mínima para agendamento online em horas';
COMMENT ON COLUMN users.booking_max_advance_days IS 'Antecedência máxima para agendamento online em dias';
COMMENT ON COLUMN users.booking_slot_interval IS 'Intervalo entre slots de horário em minutos';
COMMENT ON COLUMN users.booking_start_hour IS 'Hora de início padrão para agendamentos';
COMMENT ON COLUMN users.booking_end_hour IS 'Hora de término padrão para agendamentos';
COMMENT ON COLUMN users.booking_require_confirmation IS 'Se requer confirmação via token';
COMMENT ON COLUMN users.booking_allow_cancellation IS 'Se permite cancelamento online';
COMMENT ON COLUMN users.booking_cancellation_min_hours IS 'Antecedência mínima para cancelamento em horas';

-- ============================================
-- 2. ADICIONAR CAMPOS DE CONFIRMAÇÃO NA TABELA APPOINTMENTS
-- ============================================

ALTER TABLE appointments ADD COLUMN IF NOT EXISTS confirmation_token VARCHAR(64) UNIQUE;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS confirmation_token_expires TIMESTAMP;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS confirmation_sent_at TIMESTAMP;

-- Índice para busca por token de confirmação
CREATE INDEX IF NOT EXISTS idx_appointments_confirmation_token ON appointments(confirmation_token);

-- Comentários nas colunas
COMMENT ON COLUMN appointments.confirmation_token IS 'Token único para confirmação do agendamento';
COMMENT ON COLUMN appointments.confirmation_token_expires IS 'Data/hora de expiração do token';
COMMENT ON COLUMN appointments.confirmed_at IS 'Data/hora em que o agendamento foi confirmado';
COMMENT ON COLUMN appointments.confirmation_sent_at IS 'Data/hora em que o token foi enviado';

-- ============================================
-- 3. CRIAR TABELA DE HORÁRIOS DE TRABALHO
-- ============================================

CREATE TABLE IF NOT EXISTS working_hours (
    id SERIAL PRIMARY KEY,
    professional_id INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    break_start TIME,
    break_end TIME,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE CASCADE,
    CONSTRAINT unique_professional_day UNIQUE (professional_id, day_of_week),
    CONSTRAINT valid_hours CHECK (start_time < end_time),
    CONSTRAINT valid_break CHECK (
        (break_start IS NULL AND break_end IS NULL) OR
        (break_start IS NOT NULL AND break_end IS NOT NULL AND break_start < break_end)
    )
);

-- Índices para a tabela working_hours
CREATE INDEX IF NOT EXISTS idx_working_hours_professional ON working_hours(professional_id);
CREATE INDEX IF NOT EXISTS idx_working_hours_day ON working_hours(day_of_week);
CREATE INDEX IF NOT EXISTS idx_working_hours_available ON working_hours(professional_id, day_of_week, is_available);

-- Trigger para updated_at
CREATE TRIGGER IF NOT EXISTS update_working_hours_updated_at
    BEFORE UPDATE ON working_hours
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comentários na tabela
COMMENT ON TABLE working_hours IS 'Horários de trabalho dos profissionais por dia da semana';
COMMENT ON COLUMN working_hours.day_of_week IS '0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo';
COMMENT ON COLUMN working_hours.break_start IS 'Início do intervalo (ex: almoço)';
COMMENT ON COLUMN working_hours.break_end IS 'Fim do intervalo';

-- ============================================
-- 4. CRIAR TABELA DE DATAS BLOQUEADAS
-- ============================================

CREATE TABLE IF NOT EXISTS professional_blocked_dates (
    id SERIAL PRIMARY KEY,
    professional_id INTEGER NOT NULL,
    blocked_date DATE NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professional_id) REFERENCES professionals(id) ON DELETE CASCADE,
    CONSTRAINT unique_professional_blocked_date UNIQUE (professional_id, blocked_date)
);

-- Índices para a tabela professional_blocked_dates
CREATE INDEX IF NOT EXISTS idx_blocked_dates_professional ON professional_blocked_dates(professional_id);
CREATE INDEX IF NOT EXISTS idx_blocked_dates_date ON professional_blocked_dates(blocked_date);
CREATE INDEX IF NOT EXISTS idx_blocked_dates_range ON professional_blocked_dates(professional_id, blocked_date);

-- Comentários na tabela
COMMENT ON TABLE professional_blocked_dates IS 'Datas bloqueadas do profissional (férias, feriados, etc)';
COMMENT ON COLUMN professional_blocked_dates.reason IS 'Motivo do bloqueio (opcional)';

-- ============================================
-- 5. INSERIR HORÁRIOS PADRÃO PARA PROFISSIONAIS EXISTENTES
-- ============================================

-- Inserir horários padrão (Segunda a Sexta, 08:00-18:00 com almoço 12:00-13:00)
-- para todos os profissionais que ainda não têm horários configurados
INSERT INTO working_hours (professional_id, day_of_week, start_time, end_time, break_start, break_end, is_available)
SELECT
    p.id,
    d.day,
    '08:00:00'::TIME,
    '18:00:00'::TIME,
    '12:00:00'::TIME,
    '13:00:00'::TIME,
    TRUE
FROM professionals p
CROSS JOIN (SELECT generate_series(0, 4) as day) d
WHERE NOT EXISTS (
    SELECT 1 FROM working_hours wh
    WHERE wh.professional_id = p.id AND wh.day_of_week = d.day
);

-- Inserir Sábado com horário reduzido (08:00-12:00)
INSERT INTO working_hours (professional_id, day_of_week, start_time, end_time, is_available)
SELECT
    p.id,
    5,
    '08:00:00'::TIME,
    '12:00:00'::TIME,
    TRUE
FROM professionals p
WHERE NOT EXISTS (
    SELECT 1 FROM working_hours wh
    WHERE wh.professional_id = p.id AND wh.day_of_week = 5
);

-- Inserir Domingo como não disponível
INSERT INTO working_hours (professional_id, day_of_week, start_time, end_time, is_available)
SELECT
    p.id,
    6,
    '00:00:00'::TIME,
    '00:00:00'::TIME,
    FALSE
FROM professionals p
WHERE NOT EXISTS (
    SELECT 1 FROM working_hours wh
    WHERE wh.professional_id = p.id AND wh.day_of_week = 6
);

-- ============================================
-- 6. QUERIES DE VERIFICAÇÃO
-- ============================================

-- Verificar se as colunas foram adicionadas corretamente
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name LIKE 'booking_%';

-- Verificar tabela working_hours
SELECT COUNT(*) as total_working_hours FROM working_hours;

-- Verificar tabela professional_blocked_dates
SELECT COUNT(*) as total_blocked_dates FROM professional_blocked_dates;

-- ============================================
-- FIM DA MIGRATION
-- ============================================
