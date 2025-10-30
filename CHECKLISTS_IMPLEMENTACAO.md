# CHECKLISTS DE IMPLEMENTAÇÃO - AGENDAMAIS
### Guia Detalhado de Tarefas por Funcionalidade

---

## 📋 Como Usar Este Documento

- ✅ Marque as tarefas conforme concluir
- Cada melhoria tem sua própria seção
- Tarefas estão organizadas em ordem lógica de execução
- Inclui validações e testes para cada funcionalidade

---

# 🔥 PRIORIDADE ALTA

## 1. SISTEMA DE AVALIAÇÕES E FEEDBACK

### Backend
- [ ] Criar modelo `Review` no SQLAlchemy
  - [ ] Campos: id, appointment_id, client_id, professional_id, rating (1-5), comment, response, created_at, updated_at
  - [ ] Relacionamentos com Appointment, Client, Professional
  - [ ] Índices para queries rápidas
- [ ] Criar migration do banco de dados
- [ ] Criar endpoints REST
  - [ ] POST `/api/reviews` - Criar avaliação
  - [ ] GET `/api/reviews/:id` - Buscar avaliação específica
  - [ ] GET `/api/reviews/appointment/:id` - Buscar por agendamento
  - [ ] GET `/api/reviews/professional/:id` - Buscar por profissional
  - [ ] PUT `/api/reviews/:id/response` - Responder avaliação (apenas owner)
  - [ ] DELETE `/api/reviews/:id` - Deletar avaliação
- [ ] Implementar validações
  - [ ] Apenas cliente do agendamento pode avaliar
  - [ ] Uma avaliação por agendamento
  - [ ] Rating entre 1-5
  - [ ] Apenas agendamentos concluídos podem ser avaliados
- [ ] Criar lógica de cálculo de média de avaliações
- [ ] Adicionar campo `average_rating` na tabela Professional
- [ ] Criar job para atualizar ratings periodicamente

### Frontend
- [ ] Criar componente `ReviewForm.jsx`
  - [ ] Input de rating (estrelas clicáveis)
  - [ ] Textarea para comentário
  - [ ] Validação do formulário
  - [ ] Loading state
  - [ ] Toast de sucesso/erro
- [ ] Criar componente `ReviewCard.jsx`
  - [ ] Exibição de estrelas
  - [ ] Comentário do cliente
  - [ ] Nome e data
  - [ ] Resposta do estabelecimento (se houver)
  - [ ] Botão de responder (apenas owner)
- [ ] Criar componente `ReviewsList.jsx`
  - [ ] Lista de avaliações
  - [ ] Paginação
  - [ ] Filtros (rating, profissional, período)
  - [ ] Ordenação (mais recentes, melhor avaliadas)
- [ ] Criar página `Reviews.jsx`
  - [ ] Dashboard com estatísticas
  - [ ] Média geral de avaliações
  - [ ] Distribuição por estrelas (gráfico)
  - [ ] Lista de avaliações
- [ ] Adicionar modal de avaliação após conclusão de agendamento
  - [ ] Trigger automático ou manual
  - [ ] Opção de avaliar depois
- [ ] Integrar com `Appointments.jsx`
  - [ ] Botão "Avaliar" para agendamentos concluídos sem avaliação
  - [ ] Badge indicando se já foi avaliado
- [ ] Adicionar exibição de rating em `Professionals.jsx`
  - [ ] Estrelas ao lado do nome
  - [ ] Número de avaliações
- [ ] Criar serviço de API `reviewService.js`
  - [ ] create(), get(), getByAppointment(), getByProfessional(), respond(), delete()

### Testes
- [ ] Testes unitários backend
  - [ ] Validações do modelo
  - [ ] CRUD operations
  - [ ] Cálculo de média
- [ ] Testes unitários frontend
  - [ ] Renderização de componentes
  - [ ] Interação com estrelas
  - [ ] Submissão de formulário
- [ ] Testes de integração
  - [ ] Fluxo completo de avaliação
  - [ ] Resposta do estabelecimento

### Documentação
- [ ] Atualizar documentação da API
- [ ] Criar guia do usuário para avaliações
- [ ] Screenshots para documentação

---

## 2. PÁGINA DE AGENDAMENTO PÚBLICO

### Backend
- [ ] Criar endpoint público (sem autenticação)
  - [ ] GET `/api/public/availability/:professional_id` - Horários disponíveis
  - [ ] GET `/api/public/professionals` - Lista de profissionais ativos
  - [ ] GET `/api/public/services` - Lista de serviços
  - [ ] POST `/api/public/appointments` - Criar agendamento público
- [ ] Implementar verificação de disponibilidade em tempo real
  - [ ] Checar conflitos
  - [ ] Considerar horários de trabalho
  - [ ] Bloquear slots já reservados
- [ ] Criar sistema de confirmação
  - [ ] Gerar token único para cada agendamento
  - [ ] Link de confirmação via email/SMS/WhatsApp
  - [ ] Expiração do token (24h)
- [ ] Implementar rate limiting para prevenir spam
- [ ] Adicionar campo `is_public` na tabela Appointment
- [ ] Criar sistema de cadastro simplificado de cliente
  - [ ] Apenas nome, telefone, email
  - [ ] Verificar se cliente já existe (por telefone)

### Frontend
- [ ] Criar página `PublicBooking.jsx` (rota pública)
  - [ ] Layout simplificado sem header de admin
  - [ ] Logo e informações do estabelecimento
  - [ ] Footer com contato
- [ ] Criar componente `ProfessionalSelector.jsx`
  - [ ] Cards com foto e nome
  - [ ] Rating visível
  - [ ] Especialidades
- [ ] Criar componente `ServiceSelector.jsx`
  - [ ] Lista de serviços
  - [ ] Preço e duração
  - [ ] Descrição
  - [ ] Filtro por categoria
- [ ] Criar componente `DateTimePicker.jsx`
  - [ ] Calendário visual
  - [ ] Horários disponíveis por dia
  - [ ] Indicação visual de ocupação
  - [ ] Bloqueio de horários passados
- [ ] Criar componente `ClientInfoForm.jsx`
  - [ ] Nome completo
  - [ ] Telefone (com máscara)
  - [ ] Email
  - [ ] Observações opcionais
  - [ ] Validação em tempo real
- [ ] Criar componente `BookingConfirmation.jsx`
  - [ ] Resumo do agendamento
  - [ ] Dados do cliente
  - [ ] Instruções de confirmação
  - [ ] Opções de adição ao calendário
- [ ] Implementar stepper/wizard
  - [ ] Passo 1: Escolher profissional
  - [ ] Passo 2: Escolher serviço
  - [ ] Passo 3: Escolher data/hora
  - [ ] Passo 4: Informações do cliente
  - [ ] Passo 5: Confirmação
- [ ] Criar página de confirmação via link
  - [ ] Validar token
  - [ ] Marcar agendamento como confirmado
  - [ ] Página de sucesso
- [ ] Adicionar configuração no admin
  - [ ] Toggle para ativar/desativar agendamento público
  - [ ] Customizar link público (/book/:slug)
  - [ ] Configurar antecedência mínima (ex: 2h)
  - [ ] Configurar antecedência máxima (ex: 30 dias)

### Integração
- [ ] Criar serviço de envio de confirmação
  - [ ] Email com link de confirmação
  - [ ] SMS com link de confirmação
  - [ ] WhatsApp com link de confirmação
- [ ] Integrar com sistema de lembretes existente

### Testes
- [ ] Teste de disponibilidade em tempo real
- [ ] Teste de criação de agendamento público
- [ ] Teste de confirmação via token
- [ ] Teste de rate limiting
- [ ] Teste de responsividade mobile
- [ ] Teste com múltiplos usuários simultâneos

### SEO e Marketing
- [ ] Meta tags para SEO
- [ ] Open Graph para compartilhamento
- [ ] Schema.org markup
- [ ] Google Analytics integration
- [ ] QR Code para compartilhamento

### Documentação
- [ ] Guia de configuração para admins
- [ ] Material de divulgação do link público
- [ ] Guia do cliente para agendamento

---

## 3. SISTEMA DE COMISSÕES

### Backend
- [ ] Criar modelo `CommissionConfig` no SQLAlchemy
  - [ ] Campos: id, professional_id, type (percentage, fixed, mixed), percentage_value, fixed_value, active, created_at
  - [ ] Relacionamento com Professional
- [ ] Criar modelo `Commission` para histórico
  - [ ] Campos: id, appointment_id, professional_id, service_value, commission_type, commission_value, commission_amount, paid, paid_at, created_at
  - [ ] Relacionamentos
- [ ] Criar migrations
- [ ] Criar endpoints REST
  - [ ] GET `/api/commissions/config/:professional_id` - Config do profissional
  - [ ] POST `/api/commissions/config` - Criar/atualizar config
  - [ ] GET `/api/commissions/report` - Relatório de comissões
  - [ ] GET `/api/commissions/pending` - Comissões a pagar
  - [ ] PUT `/api/commissions/:id/pay` - Marcar como pago
  - [ ] GET `/api/commissions/history/:professional_id` - Histórico
- [ ] Implementar cálculo automático
  - [ ] Trigger ao concluir agendamento
  - [ ] Calcular com base na config do profissional
  - [ ] Gravar no histórico
- [ ] Criar lógica para diferentes tipos
  - [ ] Porcentagem do valor do serviço
  - [ ] Valor fixo por atendimento
  - [ ] Misto (fixo + porcentagem)
- [ ] Implementar filtros e relatórios
  - [ ] Por período
  - [ ] Por profissional
  - [ ] Por status (pago/pendente)

### Frontend
- [ ] Criar componente `CommissionConfig.jsx`
  - [ ] Formulário de configuração
  - [ ] Seleção de tipo de comissão
  - [ ] Inputs para valores
  - [ ] Toggle ativo/inativo
  - [ ] Preview do cálculo
- [ ] Criar componente `CommissionReport.jsx`
  - [ ] Dashboard com métricas
  - [ ] Total a pagar por profissional
  - [ ] Gráficos de comissões
  - [ ] Filtros de período
- [ ] Criar componente `CommissionsList.jsx`
  - [ ] Tabela de comissões
  - [ ] Colunas: profissional, data, serviço, valor, comissão, status
  - [ ] Checkbox para selecionar múltiplas
  - [ ] Ação em lote: marcar como pago
  - [ ] Exportar para Excel
- [ ] Criar componente `CommissionDetails.jsx`
  - [ ] Detalhes de uma comissão específica
  - [ ] Link para o agendamento
  - [ ] Histórico de pagamentos
- [ ] Adicionar seção em `ProfessionalForm.jsx`
  - [ ] Tab "Comissões"
  - [ ] Configuração inline
- [ ] Adicionar indicador em `Dashboard.jsx`
  - [ ] Total de comissões pendentes
  - [ ] Alerta visual
- [ ] Criar página `Commissions.jsx`
  - [ ] Relatório completo
  - [ ] Gestão de pagamentos
  - [ ] Exportação

### Testes
- [ ] Testes de cálculo de comissões
  - [ ] Porcentagem
  - [ ] Fixa
  - [ ] Mista
- [ ] Testes de geração automática
- [ ] Testes de relatórios
- [ ] Testes de marcação como pago

### Documentação
- [ ] Guia de configuração de comissões
- [ ] Exemplos de cálculos
- [ ] FAQ para profissionais

---

## 4. SISTEMA DE PAGAMENTOS ONLINE

### Pesquisa e Planejamento
- [ ] Escolher gateway de pagamento
  - [ ] Pesquisar Stripe vs PagSeguro vs Mercado Pago
  - [ ] Comparar taxas e features
  - [ ] Verificar disponibilidade no Brasil
  - [ ] Analisar documentação
- [ ] Definir fluxos de pagamento
  - [ ] Pré-pagamento no agendamento
  - [ ] Pagamento pós-atendimento
  - [ ] Pagamento de pacotes/planos
- [ ] Definir métodos de pagamento
  - [ ] Cartão de crédito
  - [ ] Cartão de débito
  - [ ] PIX
  - [ ] Boleto
- [ ] Planejar compliance PCI-DSS
  - [ ] Nunca armazenar dados de cartão
  - [ ] Usar tokens do gateway
  - [ ] HTTPS obrigatório

### Backend
- [ ] Criar conta no gateway escolhido
  - [ ] Conta de produção
  - [ ] Conta de sandbox/teste
- [ ] Instalar SDK do gateway
- [ ] Criar modelo `Payment` no SQLAlchemy
  - [ ] Campos: id, appointment_id, amount, method, status, gateway_transaction_id, gateway_response, paid_at, refunded_at, created_at
  - [ ] Relacionamento com Appointment
- [ ] Criar modelo `PaymentConfig`
  - [ ] Campos: gateway_name, api_key, secret_key, webhook_secret, active
- [ ] Criar migrations
- [ ] Criar endpoints REST
  - [ ] POST `/api/payments/create` - Criar intenção de pagamento
  - [ ] POST `/api/payments/confirm` - Confirmar pagamento
  - [ ] POST `/api/payments/webhook` - Webhook do gateway
  - [ ] GET `/api/payments/:id` - Buscar pagamento
  - [ ] POST `/api/payments/:id/refund` - Estornar pagamento
  - [ ] GET `/api/payments/report` - Relatório de pagamentos
- [ ] Implementar integração com gateway
  - [ ] Criar checkout session
  - [ ] Processar pagamento
  - [ ] Validar webhook signatures
  - [ ] Atualizar status do agendamento
- [ ] Implementar sistema de estorno
  - [ ] Validações (tempo limite, status)
  - [ ] Comunicação com gateway
  - [ ] Atualização de registros
- [ ] Implementar segurança
  - [ ] Validação de valores
  - [ ] Proteção contra replay attacks
  - [ ] Rate limiting
  - [ ] Logs de transações

### Frontend
- [ ] Criar componente `PaymentForm.jsx`
  - [ ] Integração com widget do gateway
  - [ ] Campos de cartão (via iframe/widget)
  - [ ] Seleção de método
  - [ ] Opção PIX (QR Code)
  - [ ] Loading states
  - [ ] Error handling
- [ ] Criar componente `PaymentStatus.jsx`
  - [ ] Indicadores visuais de status
  - [ ] Pendente, Aprovado, Recusado, Estornado
  - [ ] Mensagens contextuais
- [ ] Criar componente `PaymentDetails.jsx`
  - [ ] Detalhes da transação
  - [ ] Número da transação
  - [ ] Método usado
  - [ ] Comprovante
  - [ ] Botão de estorno (admin)
- [ ] Integrar em `AppointmentForm.jsx`
  - [ ] Opção de pagamento antecipado
  - [ ] Toggle para requer pagamento
  - [ ] Link de pagamento
- [ ] Integrar em `CompleteAppointmentModal.jsx`
  - [ ] Opção de cobrar agora
  - [ ] Link de pagamento para cliente
- [ ] Criar página `Payments.jsx`
  - [ ] Lista de pagamentos
  - [ ] Filtros (status, método, período)
  - [ ] Busca por transação
  - [ ] Exportação
- [ ] Adicionar indicadores em `Dashboard.jsx`
  - [ ] Total recebido no mês
  - [ ] Taxa de conversão de pagamentos
  - [ ] Pagamentos pendentes
- [ ] Criar configuração em `Settings.jsx`
  - [ ] Credenciais do gateway
  - [ ] Toggle ativar/desativar
  - [ ] Teste de conexão
  - [ ] Configurar métodos aceitos

### Testes
- [ ] Testes com cartões de teste do gateway
- [ ] Teste de webhook
- [ ] Teste de estorno
- [ ] Teste de diferentes métodos
- [ ] Teste de falhas de pagamento
- [ ] Teste de segurança

### Compliance e Legal
- [ ] Termos de uso de pagamento
- [ ] Política de estorno
- [ ] LGPD - consentimento para processar pagamentos
- [ ] Certificado SSL válido
- [ ] PCI-DSS compliance check

### Documentação
- [ ] Guia de configuração do gateway
- [ ] Guia do usuário para pagamentos
- [ ] Documentação de API de pagamentos
- [ ] Troubleshooting de problemas comuns

---

## 5. INTEGRAÇÃO GOOGLE CALENDAR

### Setup Inicial
- [ ] Criar projeto no Google Cloud Console
- [ ] Ativar Google Calendar API
- [ ] Configurar OAuth 2.0
  - [ ] Criar credenciais OAuth
  - [ ] Configurar tela de consentimento
  - [ ] Adicionar escopos necessários
  - [ ] Configurar redirect URIs
- [ ] Instalar biblioteca Google API
  - [ ] Backend: google-api-python-client
  - [ ] Frontend: biblioteca de OAuth

### Backend
- [ ] Criar modelo `GoogleCalendarIntegration`
  - [ ] Campos: id, professional_id, google_account_email, access_token, refresh_token, calendar_id, active, last_sync, created_at
  - [ ] Relacionamento com Professional
- [ ] Criar migration
- [ ] Criar endpoints REST
  - [ ] GET `/api/google-calendar/auth-url` - URL para autenticação
  - [ ] POST `/api/google-calendar/callback` - Callback OAuth
  - [ ] POST `/api/google-calendar/connect` - Conectar conta
  - [ ] DELETE `/api/google-calendar/disconnect/:professional_id` - Desconectar
  - [ ] POST `/api/google-calendar/sync/:professional_id` - Sincronização manual
  - [ ] GET `/api/google-calendar/status/:professional_id` - Status da integração
- [ ] Implementar fluxo OAuth 2.0
  - [ ] Gerar URL de autenticação
  - [ ] Processar callback
  - [ ] Armazenar tokens (criptografados)
  - [ ] Refresh automático de tokens
- [ ] Implementar sincronização de eventos
  - [ ] Criar evento no Google ao criar agendamento
  - [ ] Atualizar evento ao modificar agendamento
  - [ ] Deletar evento ao cancelar agendamento
  - [ ] Mapear campos (título, descrição, data, local, participantes)
- [ ] Implementar sincronização reversa (Google → Sistema)
  - [ ] Webhook/Push notifications do Google
  - [ ] Polling periódico
  - [ ] Detectar conflitos
  - [ ] Política de resolução de conflitos
- [ ] Criar job de sincronização
  - [ ] Executar a cada 5 minutos
  - [ ] Retry logic em falhas
  - [ ] Logs detalhados
- [ ] Implementar tratamento de erros
  - [ ] Token expirado
  - [ ] Quota exceeded
  - [ ] Permissões insuficientes
  - [ ] Conflitos de horário

### Frontend
- [ ] Criar componente `GoogleCalendarConnect.jsx`
  - [ ] Botão "Conectar Google Calendar"
  - [ ] Fluxo de autenticação
  - [ ] Status da conexão
  - [ ] Email conectado
  - [ ] Botão de desconectar
- [ ] Criar componente `GoogleCalendarSettings.jsx`
  - [ ] Configurações de sincronização
  - [ ] Selecionar calendário (se múltiplos)
  - [ ] Opções de sincronização
    - [ ] Bidirecional ou apenas enviar
    - [ ] Incluir informações do cliente
    - [ ] Lembrete padrão
  - [ ] Sincronização manual
  - [ ] Status da última sincronização
- [ ] Integrar em `ProfessionalForm.jsx`
  - [ ] Tab "Integrações"
  - [ ] Google Calendar section
- [ ] Adicionar indicadores visuais
  - [ ] Ícone de sincronizado em agendamentos
  - [ ] Badge "Sincronizado com Google"
  - [ ] Alertas de falhas de sincronização
- [ ] Criar página `Integrations.jsx`
  - [ ] Google Calendar
  - [ ] Futuras integrações

### Testes
- [ ] Teste de fluxo OAuth completo
- [ ] Teste de criação de evento
- [ ] Teste de atualização de evento
- [ ] Teste de deleção de evento
- [ ] Teste de refresh de token
- [ ] Teste de sincronização reversa
- [ ] Teste de resolução de conflitos
- [ ] Teste de erro de token expirado

### Documentação
- [ ] Guia de conexão passo a passo
- [ ] FAQ de problemas comuns
- [ ] Política de privacidade sobre dados do Google
- [ ] Documentação técnica da integração

---

## 6. MODO ESCURO (DARK MODE)

### Planejamento
- [ ] Definir paleta de cores dark mode
  - [ ] Background primário
  - [ ] Background secundário
  - [ ] Texto primário
  - [ ] Texto secundário
  - [ ] Cores de destaque
  - [ ] Cores de status
- [ ] Garantir contraste WCAG AA
- [ ] Testar com várias telas

### Backend
- [ ] Criar campo `theme_preference` na tabela User
  - [ ] Valores: 'light', 'dark', 'system'
- [ ] Criar migration
- [ ] Criar endpoint
  - [ ] PUT `/api/user/preferences/theme` - Salvar preferência

### Frontend
- [ ] Configurar Tailwind para dark mode
  - [ ] Editar `tailwind.config.js`
  - [ ] Adicionar classe `dark` ao html
  - [ ] Definir variáveis de cor
- [ ] Criar contexto `ThemeContext.jsx`
  - [ ] Estado do tema atual
  - [ ] Função para alternar tema
  - [ ] Persistência em localStorage
  - [ ] Sincronização com backend
  - [ ] Detecção de preferência do sistema
- [ ] Criar componente `ThemeToggle.jsx`
  - [ ] Toggle button com ícone (sol/lua)
  - [ ] Animação de transição
  - [ ] Posicionar no header
- [ ] Aplicar dark mode em todos os componentes
  - [ ] Dashboard.jsx - adicionar classes dark:
  - [ ] Layout.jsx - background e texto
  - [ ] Clients.jsx - cards e tabelas
  - [ ] ClientForm.jsx - inputs e modais
  - [ ] Professionals.jsx
  - [ ] ProfessionalForm.jsx
  - [ ] Services.jsx
  - [ ] ServiceForm.jsx
  - [ ] Appointments.jsx
  - [ ] AppointmentForm.jsx
  - [ ] CompleteAppointmentModal.jsx
  - [ ] Reminders.jsx
  - [ ] ReminderSettings.jsx
  - [ ] FinancialReport.jsx
  - [ ] Login.jsx
- [ ] Atualizar componentes UI
  - [ ] Button.jsx - variantes dark
  - [ ] Input - borders e backgrounds
  - [ ] Select
  - [ ] Modal
  - [ ] Toast notifications
  - [ ] Badges
  - [ ] Cards
  - [ ] Tabelas
- [ ] Ajustar gráficos para dark mode
  - [ ] Cores de linhas/barras
  - [ ] Texto de eixos
  - [ ] Backgrounds
- [ ] Adicionar transição suave
  - [ ] CSS transition para cores
  - [ ] Evitar flash de conteúdo

### Testes
- [ ] Teste visual de todos os componentes
- [ ] Teste de contraste de cores
- [ ] Teste de persistência da preferência
- [ ] Teste de sincronização com preferência do sistema
- [ ] Teste de transição entre temas
- [ ] Teste de acessibilidade

### Documentação
- [ ] Atualizar screenshots na documentação
- [ ] Adicionar capturas dark mode
- [ ] Guia de uso do toggle

---

## 7. ONBOARDING/TUTORIAL

### Planejamento
- [ ] Definir fluxo do onboarding
  - [ ] Identificar momentos-chave
  - [ ] Definir passos do tour
  - [ ] Criar scripts/textos
- [ ] Escolher biblioteca
  - [ ] Avaliar Intro.js vs Shepherd.js vs React Joyride
  - [ ] Instalar biblioteca escolhida

### Backend
- [ ] Criar campo `onboarding_completed` na tabela User
- [ ] Criar modelo `UserProgress`
  - [ ] Campos: user_id, step_id, completed, completed_at
- [ ] Criar migration
- [ ] Criar endpoint
  - [ ] PUT `/api/user/onboarding/complete` - Marcar como completo
  - [ ] POST `/api/user/onboarding/step` - Completar passo específico
  - [ ] GET `/api/user/onboarding/progress` - Buscar progresso

### Frontend
- [ ] Criar componente `OnboardingTour.jsx`
  - [ ] Integração com biblioteca escolhida
  - [ ] Definir steps do tour
  - [ ] Callbacks para ações
  - [ ] Botões: Próximo, Anterior, Pular, Concluir
- [ ] Definir steps do tour
  - [ ] Step 1: Bem-vindo ao AgendaMais
  - [ ] Step 2: Dashboard - visão geral do sistema
  - [ ] Step 3: Cadastrar primeiro cliente
  - [ ] Step 4: Cadastrar primeiro profissional
  - [ ] Step 5: Cadastrar primeiro serviço
  - [ ] Step 6: Criar primeiro agendamento
  - [ ] Step 7: Sistema de lembretes
  - [ ] Step 8: Relatórios financeiros
  - [ ] Step 9: Configurações
  - [ ] Step 10: Pronto para começar!
- [ ] Criar componente `SetupChecklist.jsx`
  - [ ] Lista de tarefas iniciais
  - [ ] Checkboxes para tarefas completadas
  - [ ] Links diretos para cada ação
  - [ ] Progresso visual (% completo)
  - [ ] Pode ser fechada/minimizada
- [ ] Criar tooltips contextuais
  - [ ] Componente `Tooltip.jsx`
  - [ ] Aparecer em hover ou click
  - [ ] Posicionamento inteligente
  - [ ] Fechar com X ou click fora
- [ ] Implementar lógica de exibição
  - [ ] Mostrar no primeiro login
  - [ ] Não mostrar se já completado
  - [ ] Opção de refazer tour (menu Ajuda)
  - [ ] Detectar primeiro acesso a cada página
- [ ] Criar vídeos tutoriais (opcional)
  - [ ] Gravar screencasts curtos (30s-1min)
  - [ ] Upload para YouTube/Vimeo
  - [ ] Embedar em modal
  - [ ] Links na ajuda
- [ ] Adicionar em `Layout.jsx`
  - [ ] Menu "Ajuda" no header
  - [ ] Opção "Fazer tour novamente"
  - [ ] Link para documentação
  - [ ] Link para vídeos
- [ ] Criar página `Help.jsx`
  - [ ] FAQ
  - [ ] Tutoriais em vídeo
  - [ ] Documentação
  - [ ] Contato para suporte

### Conteúdo
- [ ] Escrever textos do onboarding
  - [ ] Tom amigável e didático
  - [ ] Instruções claras
  - [ ] Destaque dos benefícios
- [ ] Criar imagens/ícones
- [ ] Gravar vídeos (se aplicável)

### Testes
- [ ] Teste do fluxo completo do onboarding
- [ ] Teste de pular onboarding
- [ ] Teste de refazer tour
- [ ] Teste de persistência de progresso
- [ ] Teste de responsividade mobile

### Documentação
- [ ] Atualizar README com link para tour
- [ ] Criar FAQ baseado em onboarding

---

## 8. AUTENTICAÇÃO DE DOIS FATORES (2FA)

### Pesquisa
- [ ] Definir método de 2FA
  - [ ] TOTP (Time-based OTP) via app autenticador
  - [ ] SMS
  - [ ] Ambos
- [ ] Escolher biblioteca
  - [ ] Backend: pyotp (Python)
  - [ ] Frontend: qrcode.react

### Backend
- [ ] Instalar biblioteca pyotp
- [ ] Criar campos na tabela User
  - [ ] `two_factor_enabled` (boolean)
  - [ ] `two_factor_secret` (string, encrypted)
  - [ ] `two_factor_backup_codes` (json, encrypted)
- [ ] Criar migration
- [ ] Criar endpoints REST
  - [ ] POST `/api/auth/2fa/setup` - Iniciar setup 2FA
  - [ ] POST `/api/auth/2fa/enable` - Ativar 2FA (após verificação)
  - [ ] POST `/api/auth/2fa/disable` - Desativar 2FA
  - [ ] POST `/api/auth/2fa/verify` - Verificar código 2FA no login
  - [ ] POST `/api/auth/2fa/backup-codes` - Gerar novos códigos
- [ ] Implementar geração de secret
  - [ ] Gerar secret único por usuário
  - [ ] Criptografar antes de salvar
  - [ ] Gerar QR code para apps autenticadores
- [ ] Implementar verificação de código
  - [ ] Validar código TOTP
  - [ ] Verificar códigos de backup
  - [ ] Rate limiting (prevenir brute force)
  - [ ] Lockout após tentativas falhas
- [ ] Gerar códigos de backup
  - [ ] 10 códigos únicos
  - [ ] Hash antes de salvar
  - [ ] Uso único
- [ ] Modificar fluxo de login
  - [ ] Se 2FA ativo, exigir código após senha
  - [ ] Token JWT apenas após 2FA bem-sucedido
- [ ] Implementar SMS 2FA (opcional)
  - [ ] Integração com Twilio
  - [ ] Gerar código numérico
  - [ ] Expiração de 5 minutos
  - [ ] Rate limiting

### Frontend
- [ ] Criar componente `TwoFactorSetup.jsx`
  - [ ] Step 1: Explicação do 2FA
  - [ ] Step 2: QR Code para scan
  - [ ] Step 3: Input para verificar código
  - [ ] Step 4: Mostrar códigos de backup
  - [ ] Step 5: Confirmação de ativação
- [ ] Criar componente `TwoFactorVerification.jsx`
  - [ ] Input de 6 dígitos
  - [ ] Auto-focus e auto-submit
  - [ ] Opção "Usar código de backup"
  - [ ] Link "Problemas para acessar?"
  - [ ] Loading state
  - [ ] Error handling
- [ ] Criar componente `TwoFactorSettings.jsx`
  - [ ] Toggle ativar/desativar
  - [ ] Status atual
  - [ ] Botão "Gerar novos códigos de backup"
  - [ ] Botão "Reconfigurar 2FA"
  - [ ] Lista de métodos configurados
- [ ] Modificar `Login.jsx`
  - [ ] Após login bem-sucedido, verificar se 2FA ativo
  - [ ] Redirecionar para verificação 2FA
  - [ ] Não armazenar token ainda
- [ ] Adicionar em `Settings.jsx` ou perfil
  - [ ] Seção "Segurança"
  - [ ] Configuração de 2FA
- [ ] Criar modal de códigos de backup
  - [ ] Exibir códigos uma única vez
  - [ ] Opção de copiar
  - [ ] Opção de baixar como arquivo
  - [ ] Aviso para guardar em local seguro

### Testes
- [ ] Teste de setup completo
- [ ] Teste de verificação de código válido
- [ ] Teste de verificação de código inválido
- [ ] Teste de códigos de backup
- [ ] Teste de desativação de 2FA
- [ ] Teste de rate limiting
- [ ] Teste de lockout por tentativas
- [ ] Teste de recuperação de acesso

### Segurança
- [ ] Audit de implementação
- [ ] Teste de vulnerabilidades
- [ ] Documentar processo de recuperação de conta

### Documentação
- [ ] Guia de setup de 2FA para usuários
- [ ] Lista de apps autenticadores recomendados
- [ ] FAQ sobre 2FA
- [ ] Processo de recuperação se perder acesso

---

# 🟡 PRIORIDADE MÉDIA

## 9. SISTEMA DE FIDELIDADE/PONTOS

### Planejamento
- [ ] Definir regras de pontuação
  - [ ] Pontos por agendamento
  - [ ] Pontos por valor gasto
  - [ ] Bônus por frequência
  - [ ] Níveis/tiers VIP
- [ ] Definir recompensas
  - [ ] Desconto em percentual
  - [ ] Serviço grátis
  - [ ] Brinde
  - [ ] Upgrade de serviço

### Backend
- [ ] Criar modelo `LoyaltyProgram`
  - [ ] Campos: name, description, points_per_real, points_per_appointment, active
- [ ] Criar modelo `ClientPoints`
  - [ ] Campos: client_id, current_points, total_earned, total_redeemed, level
- [ ] Criar modelo `PointsTransaction`
  - [ ] Campos: client_id, appointment_id, type (earn/redeem), points, description, created_at
- [ ] Criar modelo `Reward`
  - [ ] Campos: name, description, points_required, reward_type, discount_value, active
- [ ] Criar modelo `ClientLevel`
  - [ ] Campos: name, min_points, benefits, icon, color
- [ ] Criar migrations
- [ ] Criar endpoints REST
  - [ ] GET `/api/loyalty/program` - Detalhes do programa
  - [ ] POST `/api/loyalty/program` - Criar/atualizar programa
  - [ ] GET `/api/loyalty/points/:client_id` - Pontos do cliente
  - [ ] GET `/api/loyalty/transactions/:client_id` - Histórico
  - [ ] POST `/api/loyalty/earn` - Adicionar pontos
  - [ ] POST `/api/loyalty/redeem` - Resgatar pontos
  - [ ] GET `/api/loyalty/rewards` - Lista de recompensas
  - [ ] POST `/api/loyalty/rewards` - Criar recompensa
  - [ ] GET `/api/loyalty/levels` - Níveis VIP
  - [ ] GET `/api/loyalty/leaderboard` - Ranking de clientes
- [ ] Implementar lógica de acúmulo
  - [ ] Trigger ao concluir agendamento
  - [ ] Calcular pontos baseado em regras
  - [ ] Atualizar saldo do cliente
  - [ ] Verificar mudança de nível
- [ ] Implementar lógica de resgate
  - [ ] Validar pontos suficientes
  - [ ] Aplicar desconto
  - [ ] Deduzir pontos
  - [ ] Registrar transação
- [ ] Implementar sistema de níveis
  - [ ] Calcular nível baseado em pontos
  - [ ] Atualizar automático
  - [ ] Benefícios por nível

### Frontend
- [ ] Criar componente `LoyaltyProgramConfig.jsx`
  - [ ] Configurar regras de pontuação
  - [ ] Ativar/desativar programa
  - [ ] Configurar níveis VIP
- [ ] Criar componente `RewardsManagement.jsx`
  - [ ] Lista de recompensas
  - [ ] Criar/editar recompensa
  - [ ] Ativar/desativar
- [ ] Criar componente `ClientLoyaltyCard.jsx`
  - [ ] Exibir pontos atuais
  - [ ] Barra de progresso para próximo nível
  - [ ] Nível atual com badge
  - [ ] Benefícios do nível
- [ ] Criar componente `PointsHistory.jsx`
  - [ ] Lista de transações
  - [ ] Filtros
  - [ ] Detalhes de cada transação
- [ ] Criar componente `RewardsCatalog.jsx`
  - [ ] Grid de recompensas disponíveis
  - [ ] Pontos necessários
  - [ ] Botão de resgate
  - [ ] Indicador se tem pontos suficientes
- [ ] Criar componente `LoyaltyLeaderboard.jsx`
  - [ ] Ranking de clientes
  - [ ] Avatares/fotos
  - [ ] Pontos
  - [ ] Níveis
- [ ] Integrar em `ClientForm.jsx`
  - [ ] Exibir pontos do cliente
  - [ ] Opção de adicionar/remover pontos manualmente
- [ ] Integrar em `Clients.jsx`
  - [ ] Coluna de pontos
  - [ ] Badge de nível
  - [ ] Ordenar por pontos
- [ ] Integrar em `CompleteAppointmentModal.jsx`
  - [ ] Mostrar pontos que serão ganhos
  - [ ] Opção de aplicar resgate de pontos como desconto
- [ ] Criar página `Loyalty.jsx`
  - [ ] Dashboard do programa
  - [ ] Estatísticas
  - [ ] Gestão de recompensas
  - [ ] Configurações
- [ ] Adicionar no `Dashboard.jsx`
  - [ ] Total de clientes no programa
  - [ ] Pontos distribuídos no mês
  - [ ] Resgates no mês

### Gamificação
- [ ] Adicionar badges especiais
  - [ ] Primeiro agendamento
  - [ ] 10 agendamentos
  - [ ] Cliente do ano
- [ ] Notificações de progresso
  - [ ] Toast quando ganhar pontos
  - [ ] Comemoração ao subir de nível
  - [ ] Lembrete de pontos prestes a expirar (se aplicável)

### Testes
- [ ] Teste de acúmulo de pontos
- [ ] Teste de resgate
- [ ] Teste de mudança de nível
- [ ] Teste de recompensas
- [ ] Teste de validações

### Documentação
- [ ] Guia do programa de fidelidade para clientes
- [ ] Manual de configuração para admins
- [ ] Exemplos de programas bem-sucedidos

---

## 10. GESTÃO DE ESTOQUE

### Planejamento
- [ ] Definir requisitos
  - [ ] Tipos de produtos (revenda vs uso interno)
  - [ ] Unidades de medida
  - [ ] Controle de lotes (se necessário)
  - [ ] Integração com serviços

### Backend
- [ ] Criar modelo `Product`
  - [ ] Campos: name, description, sku, category, unit_measure, current_stock, min_stock, unit_cost, selling_price, active
- [ ] Criar modelo `StockMovement`
  - [ ] Campos: product_id, type (in/out), quantity, reason, reference_id, user_id, notes, created_at
- [ ] Criar modelo `ProductCategory`
  - [ ] Campos: name, description
- [ ] Criar modelo `ServiceProduct` (associação)
  - [ ] Campos: service_id, product_id, quantity_used
- [ ] Criar migrations
- [ ] Criar endpoints REST
  - [ ] CRUD completo de produtos
  - [ ] GET `/api/products` - Lista com filtros
  - [ ] POST `/api/products` - Criar produto
  - [ ] PUT `/api/products/:id` - Atualizar
  - [ ] DELETE `/api/products/:id` - Deletar
  - [ ] GET `/api/stock/movements` - Histórico de movimentações
  - [ ] POST `/api/stock/in` - Entrada de estoque
  - [ ] POST `/api/stock/out` - Saída manual
  - [ ] GET `/api/stock/low` - Produtos com estoque baixo
  - [ ] GET `/api/stock/report` - Relatório de estoque
- [ ] Implementar lógica de movimentação
  - [ ] Validar quantidade disponível
  - [ ] Atualizar estoque automaticamente
  - [ ] Registrar movimento
  - [ ] Trigger em agendamentos (dar baixa em produtos)
- [ ] Implementar alertas
  - [ ] Detectar estoque abaixo do mínimo
  - [ ] Notificar admins
  - [ ] Email/WhatsApp de alerta

### Frontend
- [ ] Criar componente `ProductsList.jsx`
  - [ ] Tabela de produtos
  - [ ] Indicador visual de estoque (cores)
  - [ ] Filtros (categoria, estoque baixo)
  - [ ] Busca
  - [ ] Ações (editar, deletar)
- [ ] Criar componente `ProductForm.jsx`
  - [ ] Formulário completo
  - [ ] Upload de imagem do produto
  - [ ] Validações
- [ ] Criar componente `StockMovementForm.jsx`
  - [ ] Tipo de movimento
  - [ ] Produto
  - [ ] Quantidade
  - [ ] Motivo/razão
  - [ ] Notas
- [ ] Criar componente `StockHistory.jsx`
  - [ ] Lista de movimentações
  - [ ] Filtros (produto, período, tipo)
  - [ ] Detalhes de cada movimento
- [ ] Criar componente `StockAlerts.jsx`
  - [ ] Lista de produtos com estoque baixo
  - [ ] Ação rápida para adicionar estoque
- [ ] Criar componente `StockReport.jsx`
  - [ ] Valor total do estoque
  - [ ] Produtos mais usados
  - [ ] Gráfico de movimentação
  - [ ] Exportação
- [ ] Integrar em `ServiceForm.jsx`
  - [ ] Seção "Produtos utilizados"
  - [ ] Selecionar produtos e quantidades
  - [ ] Alerta se produto com estoque baixo
- [ ] Criar página `Stock.jsx`
  - [ ] Tabs: Produtos, Movimentações, Alertas, Relatórios
  - [ ] Dashboard de estoque
- [ ] Adicionar em `Dashboard.jsx`
  - [ ] Número de produtos em estoque baixo
  - [ ] Link para alertas

### Testes
- [ ] Teste de criação de produto
- [ ] Teste de movimentação de estoque
- [ ] Teste de baixa automática em agendamento
- [ ] Teste de alertas de estoque baixo
- [ ] Teste de validações

### Documentação
- [ ] Manual de gestão de estoque
- [ ] Fluxo de cadastro de produtos
- [ ] Como configurar estoque mínimo

---

## 11. SISTEMA DE RECORRÊNCIA

### Backend
- [ ] Criar modelo `RecurringAppointment`
  - [ ] Campos: client_id, professional_id, service_id, frequency (weekly/biweekly/monthly), day_of_week, time, start_date, end_date, active
  - [ ] Relacionamentos
- [ ] Criar modelo `RecurrenceException`
  - [ ] Campos: recurring_appointment_id, exception_date, reason
- [ ] Criar migrations
- [ ] Criar endpoints REST
  - [ ] POST `/api/recurring-appointments` - Criar recorrência
  - [ ] GET `/api/recurring-appointments/:client_id` - Listar por cliente
  - [ ] PUT `/api/recurring-appointments/:id` - Atualizar
  - [ ] DELETE `/api/recurring-appointments/:id` - Cancelar série
  - [ ] POST `/api/recurring-appointments/:id/skip` - Pular uma ocorrência
  - [ ] GET `/api/recurring-appointments/:id/upcoming` - Próximas ocorrências
- [ ] Implementar gerador de agendamentos
  - [ ] Job que roda diariamente
  - [ ] Gera agendamentos para próximos 30-60 dias
  - [ ] Verifica se já existe
  - [ ] Respeita exceções
  - [ ] Verifica conflitos
- [ ] Implementar lógica de modificação
  - [ ] Opção: modificar apenas este
  - [ ] Opção: modificar este e futuros
  - [ ] Opção: modificar todos
- [ ] Implementar cancelamento
  - [ ] Cancelar apenas uma ocorrência
  - [ ] Cancelar toda a série
  - [ ] Cancelar a partir de uma data

### Frontend
- [ ] Criar componente `RecurringAppointmentForm.jsx`
  - [ ] Toggle "Tornar recorrente"
  - [ ] Seleção de frequência
  - [ ] Dia da semana (se semanal)
  - [ ] Dia do mês (se mensal)
  - [ ] Data de início
  - [ ] Data de término (opcional)
  - [ ] Preview das próximas ocorrências
- [ ] Criar componente `RecurringAppointmentsList.jsx`
  - [ ] Lista de séries recorrentes
  - [ ] Status ativo/inativo
  - [ ] Próximas ocorrências
  - [ ] Ações (editar, pausar, cancelar)
- [ ] Criar componente `RecurringAppointmentDetails.jsx`
  - [ ] Detalhes da série
  - [ ] Lista de todas as ocorrências
  - [ ] Histórico de exceções
  - [ ] Estatísticas (total agendado, concluído, cancelado)
- [ ] Modificar `AppointmentForm.jsx`
  - [ ] Integrar formulário de recorrência
  - [ ] Detectar se agendamento é parte de série
  - [ ] Opções de modificação (este, futuros, todos)
- [ ] Modificar `Appointments.jsx`
  - [ ] Ícone indicando agendamento recorrente
  - [ ] Filtro para agendamentos recorrentes
  - [ ] Agrupamento por série (opcional)
- [ ] Criar página `RecurringAppointments.jsx`
  - [ ] Gestão completa de séries
  - [ ] Dashboard de recorrências

### Testes
- [ ] Teste de criação de série
- [ ] Teste de geração automática
- [ ] Teste de modificação
- [ ] Teste de cancelamento
- [ ] Teste de exceções
- [ ] Teste de detecção de conflitos

### Documentação
- [ ] Guia de uso de agendamentos recorrentes
- [ ] Exemplos de uso
- [ ] FAQ

---

## 12. LISTA DE ESPERA

### Backend
- [ ] Criar modelo `Waitlist`
  - [ ] Campos: client_id, professional_id, service_id, preferred_date, preferred_time_start, preferred_time_end, notes, status, notified_at, created_at
- [ ] Criar migration
- [ ] Criar endpoints REST
  - [ ] POST `/api/waitlist` - Adicionar à lista
  - [ ] GET `/api/waitlist` - Listar
  - [ ] DELETE `/api/waitlist/:id` - Remover
  - [ ] PUT `/api/waitlist/:id/notify` - Marcar como notificado
  - [ ] GET `/api/waitlist/matches` - Buscar matches para horário cancelado
- [ ] Implementar lógica de notificação
  - [ ] Quando agendamento cancelado
  - [ ] Buscar clientes na lista de espera
  - [ ] Filtrar por preferências (profissional, serviço, data/hora)
  - [ ] Ordenar por prioridade (FIFO, VIP)
  - [ ] Notificar via WhatsApp/SMS
  - [ ] Link direto para agendar
  - [ ] Expiração do link (ex: 2h)
- [ ] Implementar priorização
  - [ ] Ordem de chegada
  - [ ] Clientes VIP primeiro
  - [ ] Clientes com mais faltas por último

### Frontend
- [ ] Criar componente `WaitlistForm.jsx`
  - [ ] Selecionar cliente
  - [ ] Selecionar profissional (opcional)
  - [ ] Selecionar serviço
  - [ ] Data preferida
  - [ ] Horário preferido (range)
  - [ ] Notas adicionais
- [ ] Criar componente `WaitlistTable.jsx`
  - [ ] Lista de clientes na espera
  - [ ] Colunas: cliente, preferências, data cadastro, status
  - [ ] Ações: notificar, remover, converter em agendamento
  - [ ] Ordenação
- [ ] Criar componente `WaitlistNotification.jsx`
  - [ ] Modal de notificação
  - [ ] Preview da mensagem
  - [ ] Botão de envio
- [ ] Integrar em `Appointments.jsx`
  - [ ] Ao cancelar, perguntar se quer notificar lista de espera
  - [ ] Mostrar quantos clientes correspondem ao horário
- [ ] Integrar em `ClientForm.jsx`
  - [ ] Botão "Adicionar à lista de espera"
- [ ] Criar página `Waitlist.jsx`
  - [ ] Gestão completa da lista
  - [ ] Filtros
  - [ ] Estatísticas (taxa de conversão)
- [ ] Adicionar em `Dashboard.jsx`
  - [ ] Número de clientes na lista de espera

### Automação
- [ ] Job para lembrar clientes na lista
  - [ ] A cada X dias, lembrar que estão na espera
  - [ ] Perguntar se ainda tem interesse

### Testes
- [ ] Teste de adição à lista
- [ ] Teste de matching
- [ ] Teste de notificação
- [ ] Teste de conversão em agendamento
- [ ] Teste de priorização

### Documentação
- [ ] Guia de uso da lista de espera
- [ ] Como configurar priorização

---

## 13. MARKETING POR EMAIL

### Setup
- [ ] Escolher serviço de email
  - [ ] Pesquisar SendGrid vs Mailgun vs Amazon SES
  - [ ] Avaliar custos e limites
  - [ ] Criar conta
- [ ] Configurar domínio
  - [ ] SPF, DKIM, DMARC
  - [ ] Verificação de domínio
  - [ ] Email de envio (ex: contato@agendamais.com.br)

### Backend
- [ ] Instalar SDK do serviço escolhido
- [ ] Criar modelo `EmailCampaign`
  - [ ] Campos: name, subject, from_email, from_name, reply_to, html_content, text_content, status, scheduled_at, sent_at, created_by
- [ ] Criar modelo `CampaignRecipient`
  - [ ] Campos: campaign_id, client_id, status (sent/opened/clicked/failed), sent_at, opened_at, clicked_at
- [ ] Criar modelo `EmailTemplate`
  - [ ] Campos: name, subject, html_content, variables, category
- [ ] Criar migrations
- [ ] Criar endpoints REST
  - [ ] CRUD de campanhas
  - [ ] CRUD de templates
  - [ ] POST `/api/email/campaigns/:id/send` - Enviar campanha
  - [ ] POST `/api/email/campaigns/:id/test` - Enviar teste
  - [ ] GET `/api/email/campaigns/:id/stats` - Estatísticas
  - [ ] POST `/api/email/webhook` - Webhook do serviço (opens, clicks)
- [ ] Implementar envio
  - [ ] Processar lista de destinatários
  - [ ] Personalizar conteúdo por cliente
  - [ ] Enviar em lotes (rate limiting)
  - [ ] Registrar envios
  - [ ] Retry em falhas
- [ ] Implementar tracking
  - [ ] Pixel de abertura
  - [ ] Links com tracking
  - [ ] Webhook para eventos
- [ ] Implementar segmentação
  - [ ] Todos os clientes
  - [ ] Clientes ativos (agendaram nos últimos X meses)
  - [ ] Clientes inativos
  - [ ] Clientes VIP
  - [ ] Por profissional
  - [ ] Por serviço utilizado
  - [ ] Custom query

### Frontend
- [ ] Criar componente `EmailCampaignForm.jsx`
  - [ ] Nome da campanha
  - [ ] Assunto
  - [ ] Remetente
  - [ ] Conteúdo (editor HTML)
  - [ ] Preview
  - [ ] Seleção de template
  - [ ] Personalização (variáveis)
- [ ] Criar componente `EmailEditor.jsx`
  - [ ] Editor WYSIWYG (TinyMCE ou similar)
  - [ ] Inserir variáveis {nome_cliente}, {proximo_agendamento}
  - [ ] Preview desktop/mobile
- [ ] Criar componente `EmailTemplateLibrary.jsx`
  - [ ] Grid de templates
  - [ ] Preview
  - [ ] Selecionar para usar
  - [ ] Criar/editar template
- [ ] Criar componente `RecipientSelector.jsx`
  - [ ] Segmentação
  - [ ] Preview de quantos clientes
  - [ ] Lista de destinatários
  - [ ] Exclusão manual
- [ ] Criar componente `CampaignScheduler.jsx`
  - [ ] Enviar agora ou agendar
  - [ ] Seleção de data/hora
  - [ ] Timezone
- [ ] Criar componente `CampaignStats.jsx`
  - [ ] Métricas (enviados, abertos, cliques, falhas)
  - [ ] Taxas (abertura, clique)
  - [ ] Gráficos de timeline
  - [ ] Lista de recipientes com status
- [ ] Criar componente `CampaignsList.jsx`
  - [ ] Lista de campanhas
  - [ ] Status (rascunho, agendada, enviando, enviada)
  - [ ] Estatísticas resumidas
  - [ ] Ações (editar, duplicar, enviar, deletar)
- [ ] Criar página `EmailMarketing.jsx`
  - [ ] Dashboard
  - [ ] Criar campanha
  - [ ] Gerenciar templates
  - [ ] Histórico

### Templates Pré-configurados
- [ ] Template: Bem-vindo
- [ ] Template: Lembrete de agendamento
- [ ] Template: Aniversário
- [ ] Template: Cliente inativo (reconquista)
- [ ] Template: Novidades/Promoções
- [ ] Template: Pesquisa de satisfação
- [ ] Template: Indicação (traga um amigo)

### Compliance
- [ ] Link de descadastramento (obrigatório)
- [ ] Página de preferências de email
- [ ] Consentimento LGPD
- [ ] Política de privacidade

### Testes
- [ ] Teste de envio
- [ ] Teste de tracking
- [ ] Teste de descadastramento
- [ ] Teste de segmentação
- [ ] Teste de personalização

### Documentação
- [ ] Guia de criação de campanhas
- [ ] Boas práticas de email marketing
- [ ] Como interpretar estatísticas

---

## 14. INSTAGRAM/FACEBOOK AGENDAMENTOS

### Pesquisa
- [ ] Estudar Meta Business API
- [ ] Estudar Messenger Platform
- [ ] Estudar Instagram Messaging API
- [ ] Verificar requisitos e aprovações

### Setup Inicial
- [ ] Criar Meta App
- [ ] Configurar permissões
- [ ] Passar por App Review (se necessário)
- [ ] Criar Business Account
- [ ] Conectar Instagram Business Account
- [ ] Conectar Facebook Page

### Backend
- [ ] Instalar SDK do Facebook
- [ ] Criar modelo `SocialMediaIntegration`
  - [ ] Campos: platform, page_id, access_token, page_access_token, active
- [ ] Criar modelo `MessengerConversation`
  - [ ] Campos: platform, sender_id, status, last_message_at
- [ ] Criar migration
- [ ] Criar endpoints REST
  - [ ] POST `/api/social/connect` - Conectar conta
  - [ ] DELETE `/api/social/disconnect` - Desconectar
  - [ ] POST `/api/social/webhook` - Webhook do Facebook
  - [ ] GET `/api/social/status` - Status da integração
- [ ] Implementar OAuth Facebook
  - [ ] Fluxo de autenticação
  - [ ] Obter tokens de longa duração
  - [ ] Armazenar tokens
- [ ] Implementar Webhook Messenger
  - [ ] Verificação do webhook
  - [ ] Receber mensagens
  - [ ] Processar mensagens
- [ ] Implementar chatbot
  - [ ] Detectar intenção de agendamento
  - [ ] Fluxo conversacional
  - [ ] Coleta de informações (serviço, profissional, data/hora)
  - [ ] Validação de disponibilidade
  - [ ] Confirmação de agendamento
  - [ ] Mensagens de erro amigáveis
  - [ ] Comandos: "agendar", "cancelar", "ver agendamentos"
- [ ] Implementar processamento de NLP (opcional)
  - [ ] Usar Wit.ai ou Dialogflow
  - [ ] Entender intenções
  - [ ] Extrair entidades (data, hora, serviço)
- [ ] Implementar ações do Instagram
  - [ ] Botão "Agendar" no perfil
  - [ ] Redirect para página de agendamento
  - [ ] Deep link para app (se existir)

### Frontend
- [ ] Criar componente `SocialMediaConnect.jsx`
  - [ ] Botão "Conectar Facebook"
  - [ ] Botão "Conectar Instagram"
  - [ ] Status da conexão
  - [ ] Informações da página conectada
- [ ] Criar componente `SocialMediaSettings.jsx`
  - [ ] Configurar mensagens do bot
  - [ ] Ativar/desativar bot
  - [ ] Horário de funcionamento do bot
  - [ ] Mensagem automática fora do horário
- [ ] Criar componente `MessengerInbox.jsx`
  - [ ] Lista de conversas
  - [ ] Responder mensagens
  - [ ] Ver histórico
  - [ ] Marcar como lida
- [ ] Adicionar em `Integrations.jsx`
  - [ ] Seção Facebook/Instagram
  - [ ] Status e configurações
- [ ] Criar dashboard de conversas
  - [ ] Estatísticas
  - [ ] Taxa de conversão
  - [ ] Tempo médio de resposta

### Chatbot - Fluxos
- [ ] Fluxo: Boas-vindas
  - [ ] Mensagem de boas-vindas
  - [ ] Menu de opções
- [ ] Fluxo: Novo agendamento
  - [ ] Escolher serviço
  - [ ] Escolher profissional
  - [ ] Escolher data
  - [ ] Escolher horário
  - [ ] Confirmar dados
  - [ ] Nome do cliente
  - [ ] Telefone
  - [ ] Criar agendamento
  - [ ] Enviar confirmação
- [ ] Fluxo: Ver agendamentos
  - [ ] Listar próximos agendamentos
  - [ ] Opção de cancelar
- [ ] Fluxo: Cancelar agendamento
  - [ ] Confirmar cancelamento
  - [ ] Processar
  - [ ] Enviar confirmação
- [ ] Fluxo: Ajuda
  - [ ] FAQ automatizado
  - [ ] Opção de falar com atendente
- [ ] Fallback
  - [ ] Mensagem quando não entender
  - [ ] Sugestões de comandos

### Testes
- [ ] Teste de conexão Facebook/Instagram
- [ ] Teste de webhook
- [ ] Teste de recebimento de mensagens
- [ ] Teste de fluxo completo de agendamento
- [ ] Teste de comandos do bot
- [ ] Teste de tratamento de erros

### Compliance
- [ ] Política de privacidade para bots
- [ ] Consentimento de dados
- [ ] Respeitar opt-out
- [ ] Meta Platform Policies

### Documentação
- [ ] Guia de setup da integração
- [ ] Comandos do chatbot
- [ ] FAQ para clientes

---

## 15. API PÚBLICA

### Planejamento
- [ ] Definir use cases da API
  - [ ] Integrações com outros sistemas
  - [ ] Apps mobile de terceiros
  - [ ] Automações
- [ ] Definir recursos expostos
  - [ ] Clientes (CRUD)
  - [ ] Profissionais (read-only)
  - [ ] Serviços (read-only)
  - [ ] Agendamentos (CRUD)
  - [ ] Disponibilidade (read)
- [ ] Definir rate limits
  - [ ] Por API key
  - [ ] Por endpoint
  - [ ] Throttling

### Backend
- [ ] Criar modelo `APIKey`
  - [ ] Campos: name, key, secret_hash, user_id, permissions, rate_limit, active, last_used_at, created_at, expires_at
- [ ] Criar modelo `APIUsage`
  - [ ] Campos: api_key_id, endpoint, method, status_code, timestamp
- [ ] Criar migrations
- [ ] Implementar autenticação API
  - [ ] API Key + Secret
  - [ ] Header Authorization: Bearer {key}
  - [ ] Validação de key
  - [ ] Validação de permissões
- [ ] Implementar rate limiting
  - [ ] Usar Redis para contadores
  - [ ] Por minuto, hora, dia
  - [ ] Resposta 429 Too Many Requests
  - [ ] Headers X-RateLimit-*
- [ ] Criar endpoints públicos versionados
  - [ ] Versão: /api/v1/
  - [ ] GET `/api/v1/professionals` - Listar profissionais
  - [ ] GET `/api/v1/services` - Listar serviços
  - [ ] GET `/api/v1/availability` - Verificar disponibilidade
  - [ ] POST `/api/v1/clients` - Criar cliente
  - [ ] GET `/api/v1/clients/:id` - Buscar cliente
  - [ ] PUT `/api/v1/clients/:id` - Atualizar cliente
  - [ ] POST `/api/v1/appointments` - Criar agendamento
  - [ ] GET `/api/v1/appointments/:id` - Buscar agendamento
  - [ ] PUT `/api/v1/appointments/:id` - Atualizar agendamento
  - [ ] DELETE `/api/v1/appointments/:id` - Cancelar agendamento
- [ ] Implementar sistema de permissões
  - [ ] Scopes: read:clients, write:clients, read:appointments, write:appointments
  - [ ] Validar por endpoint
- [ ] Implementar webhooks
  - [ ] Configurar URLs de callback
  - [ ] Eventos: appointment.created, appointment.updated, appointment.cancelled
  - [ ] Assinatura HMAC
  - [ ] Retry em falhas
- [ ] Criar documentação Swagger/OpenAPI
  - [ ] Instalar biblioteca (flask-swagger-ui)
  - [ ] Definir schema OpenAPI 3.0
  - [ ] Documentar todos os endpoints
  - [ ] Exemplos de request/response
  - [ ] Códigos de erro
- [ ] Implementar logging
  - [ ] Log de todas as requisições
  - [ ] Análise de uso
  - [ ] Detecção de abuso

### Frontend (Developer Portal)
- [ ] Criar página `APIKeys.jsx`
  - [ ] Lista de API keys
  - [ ] Criar nova key
  - [ ] Regenerar secret
  - [ ] Revogar key
  - [ ] Ver uso
- [ ] Criar componente `APIKeyForm.jsx`
  - [ ] Nome da aplicação
  - [ ] Descrição
  - [ ] Selecionar permissões (scopes)
  - [ ] Rate limit customizado
  - [ ] Data de expiração
- [ ] Criar componente `APIUsageStats.jsx`
  - [ ] Gráfico de uso
  - [ ] Requests por dia
  - [ ] Endpoints mais usados
  - [ ] Erros
- [ ] Criar componente `WebhookConfig.jsx`
  - [ ] URL do webhook
  - [ ] Eventos a receber
  - [ ] Secret para validação
  - [ ] Testar webhook
- [ ] Criar página `APIDocs.jsx`
  - [ ] Embed do Swagger UI
  - [ ] Guia de início rápido
  - [ ] Exemplos de código (cURL, Python, JavaScript)
  - [ ] Changelog
- [ ] Criar portal do desenvolvedor
  - [ ] Página inicial
  - [ ] Documentação
  - [ ] Console de teste
  - [ ] Gerenciar keys

### Documentação
- [ ] Guia de início rápido
  - [ ] Como obter API key
  - [ ] Primeira requisição
  - [ ] Exemplo completo
- [ ] Referência completa
  - [ ] Todos os endpoints
  - [ ] Parâmetros
  - [ ] Responses
  - [ ] Erros
- [ ] Exemplos de código
  - [ ] Python
  - [ ] JavaScript/Node.js
  - [ ] PHP
  - [ ] cURL
- [ ] Webhooks
  - [ ] Como configurar
  - [ ] Eventos disponíveis
  - [ ] Validar assinatura
  - [ ] Boas práticas
- [ ] Rate limits e cotas
- [ ] Changelog e versionamento
- [ ] FAQ
- [ ] Termos de uso da API

### SDKs (opcional)
- [ ] SDK Python
- [ ] SDK JavaScript/Node.js
- [ ] Publicar no npm/PyPI

### Testes
- [ ] Testes de autenticação
- [ ] Testes de rate limiting
- [ ] Testes de permissões
- [ ] Testes de cada endpoint
- [ ] Testes de webhooks
- [ ] Testes de versionamento

### Segurança
- [ ] Audit de segurança
- [ ] Penetration testing
- [ ] Rate limiting abuse protection
- [ ] API key rotation policy

---

*Continua... (checklists restantes para as próximas melhorias)*

---

## 📌 COMO USAR ESTE DOCUMENTO

### Para Cada Feature:
1. Copie o checklist para seu gerenciador de projetos (Jira, Trello, GitHub Issues)
2. Assigne tasks para membros da equipe
3. Marque como concluído conforme avança
4. Documente problemas encontrados

### Estimativas de Tempo:
- Cada checkbox representa aproximadamente 1-4 horas de trabalho
- Some os checkboxes de cada seção para estimar sprint
- Considere tempo de testes e revisão

### Priorização:
- Comece pelos checklists de Prioridade Alta
- Pode paralelizar features independentes
- Respeite dependências técnicas

### Adaptação:
- Este é um guia, não uma regra rígida
- Adapte conforme seu contexto
- Adicione/remova itens conforme necessário

---

*Documento mantido por: Equipe AgendaMais*
*Versão: 1.0*
*Última atualização: 30/10/2025*
