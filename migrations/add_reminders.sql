-- ============================================
-- Migration: Sistema de Lembretes
-- Data: 2025-01-07
-- Descrição: Cria tabelas para lembretes de agendamentos
-- ============================================

-- ============================================
-- 1. TABELA REMINDER_SETTINGS (Configurações por usuário)
-- ============================================
CREATE TABLE IF NOT EXISTS reminder_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Configurações de email
    email_enabled BOOLEAN DEFAULT TRUE,
    email_hours_before INTEGER DEFAULT 24,

    -- Configurações de SMS
    sms_enabled BOOLEAN DEFAULT FALSE,
    sms_hours_before INTEGER DEFAULT 2,

    -- Configurações de WhatsApp
    whatsapp_enabled BOOLEAN DEFAULT FALSE,
    whatsapp_hours_before INTEGER DEFAULT 2,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraint: um registro por usuário
    UNIQUE(user_id)
);

-- Índice para busca rápida
CREATE INDEX IF NOT EXISTS idx_reminder_settings_user_id ON reminder_settings(user_id);

-- ============================================
-- 2. TABELA REMINDERS (Lembretes individuais)
-- ============================================
CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    appointment_id INTEGER NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,

    -- Tipo de lembrete
    type VARCHAR(50) NOT NULL CHECK (type IN ('email', 'sms', 'whatsapp')),

    -- Status do lembrete
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'sent', 'failed', 'cancelled')),

    -- Quando enviar
    scheduled_at TIMESTAMP NOT NULL,

    -- Quando foi enviado
    sent_at TIMESTAMP,

    -- ID da mensagem no provedor (Twilio, etc)
    external_id VARCHAR(100),

    -- Mensagem enviada
    message_content TEXT,

    -- Erro se falhou
    error_message TEXT,

    -- Tentativas de envio
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_appointment_id ON reminders(appointment_id);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);
CREATE INDEX IF NOT EXISTS idx_reminders_scheduled_at ON reminders(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_reminders_status_scheduled ON reminders(status, scheduled_at);

-- ============================================
-- 3. TABELA REMINDER_LOGS (Log de tentativas)
-- ============================================
CREATE TABLE IF NOT EXISTS reminder_logs (
    id SERIAL PRIMARY KEY,
    reminder_id INTEGER NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,

    -- Resultado da tentativa
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,

    -- ID externo se sucesso
    external_id VARCHAR(100),

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para busca por reminder
CREATE INDEX IF NOT EXISTS idx_reminder_logs_reminder_id ON reminder_logs(reminder_id);

-- ============================================
-- 4. FUNÇÃO PARA ATUALIZAR updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- 5. TRIGGERS PARA updated_at
-- ============================================
DROP TRIGGER IF EXISTS update_reminder_settings_updated_at ON reminder_settings;
CREATE TRIGGER update_reminder_settings_updated_at
    BEFORE UPDATE ON reminder_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_reminders_updated_at ON reminders;
CREATE TRIGGER update_reminders_updated_at
    BEFORE UPDATE ON reminders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. QUERIES DE VERIFICAÇÃO
-- ============================================

-- Verificar estrutura das tabelas
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('reminder_settings', 'reminders', 'reminder_logs')
ORDER BY table_name, ordinal_position;

-- ============================================
-- FIM DA MIGRATION
-- ============================================
