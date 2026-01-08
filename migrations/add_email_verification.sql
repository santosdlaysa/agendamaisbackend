-- ============================================
-- Migration: Adicionar verificação de email
-- Data: 2025-01-06
-- Descrição: Adiciona campos para verificação de email no cadastro
-- ============================================

-- Campos de verificação de email na tabela users
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP;

-- Índice para busca por token
CREATE INDEX IF NOT EXISTS idx_users_email_verification_token ON users(email_verification_token);

-- Comentários nas colunas
COMMENT ON COLUMN users.email_verified IS 'Se o email foi verificado';
COMMENT ON COLUMN users.email_verification_token IS 'Token para verificação de email';
COMMENT ON COLUMN users.email_verification_expires IS 'Expiração do token de verificação';
COMMENT ON COLUMN users.email_verified_at IS 'Data/hora da verificação do email';

-- ============================================
-- FIM DA MIGRATION
-- ============================================
