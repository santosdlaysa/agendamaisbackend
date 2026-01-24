-- Migration: Adicionar campos de onboarding obrigatório
-- Data: 2025-01-23
-- Descrição: Adiciona campos para controlar se o usuário completou o onboarding

-- Adicionar campo de status do onboarding
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;

-- Adicionar campo de data de conclusão do onboarding
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMP;

-- Atualizar usuários existentes que já têm business_name e slug preenchidos
-- Estes são considerados como tendo completado o onboarding
UPDATE users
SET onboarding_completed = TRUE,
    onboarding_completed_at = COALESCE(updated_at, created_at, NOW())
WHERE business_name IS NOT NULL
  AND business_name != ''
  AND slug IS NOT NULL
  AND slug != '';
