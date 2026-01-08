-- ============================================
-- Migration: Adicionar Multi-Tenancy (Isolamento por Empresa)
-- Data: 2025-01-07
-- Descrição: Adiciona user_id nas tabelas para isolar dados por empresa
-- ============================================

-- ============================================
-- 1. ADICIONAR user_id NA TABELA CLIENTS
-- ============================================
ALTER TABLE clients ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

-- Índice para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);

-- ============================================
-- 2. ADICIONAR user_id NA TABELA PROFESSIONALS
-- ============================================
ALTER TABLE professionals ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

-- Índice para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_professionals_user_id ON professionals(user_id);

-- ============================================
-- 3. ADICIONAR user_id NA TABELA SERVICES
-- ============================================
ALTER TABLE services ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

-- Índice para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_services_user_id ON services(user_id);

-- ============================================
-- 4. VERIFICAR SE APPOINTMENTS JÁ TEM user_id
-- ============================================
-- A tabela appointments já deve ter user_id do agendamento online
-- Se não tiver:
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);
CREATE INDEX IF NOT EXISTS idx_appointments_user_id ON appointments(user_id);

-- ============================================
-- 5. ATUALIZAR DADOS EXISTENTES (OPCIONAL)
-- Se houver um único usuário admin, associar todos os dados a ele
-- ============================================

-- Descomente e ajuste o ID do usuário se necessário:
-- UPDATE clients SET user_id = 1 WHERE user_id IS NULL;
-- UPDATE professionals SET user_id = 1 WHERE user_id IS NULL;
-- UPDATE services SET user_id = 1 WHERE user_id IS NULL;
-- UPDATE appointments SET user_id = 1 WHERE user_id IS NULL;

-- ============================================
-- 6. QUERIES DE VERIFICAÇÃO
-- ============================================

-- Verificar estrutura das tabelas
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('clients', 'professionals', 'services', 'appointments')
AND column_name = 'user_id';

-- Contar registros sem user_id (para identificar dados órfãos)
SELECT 'clients' as tabela, COUNT(*) as sem_user_id FROM clients WHERE user_id IS NULL
UNION ALL
SELECT 'professionals', COUNT(*) FROM professionals WHERE user_id IS NULL
UNION ALL
SELECT 'services', COUNT(*) FROM services WHERE user_id IS NULL
UNION ALL
SELECT 'appointments', COUNT(*) FROM appointments WHERE user_id IS NULL;

-- ============================================
-- FIM DA MIGRATION
-- ============================================
