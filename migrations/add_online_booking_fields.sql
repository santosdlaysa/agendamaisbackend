-- Migration: Adicionar campos para agendamento online
-- Data: 2026-01-04

-- Adicionar campos ao users (estabelecimento)
ALTER TABLE users ADD COLUMN IF NOT EXISTS slug VARCHAR(100) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_address VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_logo VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS online_booking_enabled BOOLEAN DEFAULT TRUE;

-- Adicionar campos ao appointments
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS booking_code VARCHAR(8) UNIQUE;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'admin';
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);

-- Criar índices para otimização
CREATE INDEX IF NOT EXISTS idx_users_slug ON users(slug);
CREATE INDEX IF NOT EXISTS idx_appointments_booking_code ON appointments(booking_code);
CREATE INDEX IF NOT EXISTS idx_appointments_source ON appointments(source);
CREATE INDEX IF NOT EXISTS idx_appointments_user_id ON appointments(user_id);

-- Atualizar slug para usuários existentes (baseado no email)
UPDATE users
SET slug = LOWER(REPLACE(SPLIT_PART(email, '@', 1), '.', '-'))
WHERE slug IS NULL;

-- Comentário: Para usar o agendamento online, configure o slug do estabelecimento
-- Exemplo: UPDATE users SET slug = 'minha-barbearia', business_name = 'Minha Barbearia' WHERE id = 1;
