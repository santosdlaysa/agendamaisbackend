-- ============================================
-- Migration: Configurações de Lembretes por Profissional
-- Data: 2025-01-09
-- Descrição: Cria tabela para configurações de lembretes por profissional
-- ============================================

-- ============================================
-- 1. TABELA PROFESSIONAL_REMINDER_SETTINGS
-- ============================================
CREATE TABLE IF NOT EXISTS professional_reminder_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    professional_id INTEGER NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    reminder_type VARCHAR(20) NOT NULL CHECK (reminder_type IN ('email', 'sms', 'whatsapp')),

    -- Configurações
    enabled BOOLEAN DEFAULT TRUE,
    hours_before INTEGER DEFAULT 24,
    custom_message TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraint: uma configuração por profissional/tipo
    UNIQUE(professional_id, reminder_type)
);

-- Índices para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_prof_reminder_settings_user_id ON professional_reminder_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_prof_reminder_settings_professional_id ON professional_reminder_settings(professional_id);
CREATE INDEX IF NOT EXISTS idx_prof_reminder_settings_type ON professional_reminder_settings(reminder_type);

-- ============================================
-- 2. TRIGGER PARA updated_at
-- ============================================
DROP TRIGGER IF EXISTS update_professional_reminder_settings_updated_at ON professional_reminder_settings;
CREATE TRIGGER update_professional_reminder_settings_updated_at
    BEFORE UPDATE ON professional_reminder_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 3. QUERIES DE VERIFICAÇÃO
-- ============================================

-- Verificar estrutura da tabela
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'professional_reminder_settings'
ORDER BY ordinal_position;

-- ============================================
-- FIM DA MIGRATION
-- ============================================
