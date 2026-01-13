-- Migration: Criar tabela professional_users
-- Data: 2026-01-13
-- Descricao: Tabela para autenticacao de profissionais no portal

CREATE TABLE IF NOT EXISTS professional_users (
    id SERIAL PRIMARY KEY,
    professional_id INTEGER NOT NULL REFERENCES professionals(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    invite_token VARCHAR(255),
    invite_expires_at TIMESTAMP,
    reset_token VARCHAR(255),
    reset_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices para otimizar buscas
CREATE INDEX IF NOT EXISTS idx_professional_users_professional_id ON professional_users(professional_id);
CREATE INDEX IF NOT EXISTS idx_professional_users_email ON professional_users(email);
CREATE INDEX IF NOT EXISTS idx_professional_users_invite_token ON professional_users(invite_token);
CREATE INDEX IF NOT EXISTS idx_professional_users_reset_token ON professional_users(reset_token);

-- Comentarios
COMMENT ON TABLE professional_users IS 'Usuarios do portal do profissional';
COMMENT ON COLUMN professional_users.professional_id IS 'ID do profissional associado';
COMMENT ON COLUMN professional_users.invite_token IS 'Token para ativacao de conta';
COMMENT ON COLUMN professional_users.reset_token IS 'Token para recuperacao de senha';
