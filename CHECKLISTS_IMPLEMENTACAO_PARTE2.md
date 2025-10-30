# CHECKLISTS DE IMPLEMENTAÇÃO - PARTE 2
### Melhorias 16-35

---

## 16. SISTEMA DE PERMISSÕES E ROLES

### Planejamento
- [ ] Definir roles
  - [ ] Admin (acesso total)
  - [ ] Gerente (gestão operacional, sem configurações sensíveis)
  - [ ] Recepcionista (agendamentos e clientes)
  - [ ] Profissional (próprios agendamentos apenas)
- [ ] Mapear permissões por módulo
  - [ ] Clientes: visualizar, criar, editar, deletar
  - [ ] Profissionais: visualizar, criar, editar, deletar
  - [ ] Serviços: visualizar, criar, editar, deletar
  - [ ] Agendamentos: visualizar, criar, editar, deletar, concluir
  - [ ] Lembretes: visualizar, configurar, enviar
  - [ ] Relatórios: visualizar, exportar
  - [ ] Configurações: visualizar, editar
  - [ ] Usuários: visualizar, criar, editar, deletar
  - [ ] Comissões: visualizar, pagar
  - [ ] Estoque: visualizar, movimentar

### Backend
- [ ] Criar modelo `Role`
  - [ ] Campos: name, description, permissions (JSON), system_role (boolean), created_at
- [ ] Criar modelo `UserRole`
  - [ ] Campos: user_id, role_id
- [ ] Modificar modelo `User`
  - [ ] Adicionar relacionamento com roles
- [ ] Criar migrations
- [ ] Seed roles padrão
  - [ ] Admin
  - [ ] Gerente
  - [ ] Recepcionista
  - [ ] Profissional
- [ ] Criar endpoints REST
  - [ ] GET `/api/roles` - Listar roles
  - [ ] POST `/api/roles` - Criar role customizado
  - [ ] PUT `/api/roles/:id` - Editar role (apenas custom)
  - [ ] DELETE `/api/roles/:id` - Deletar role (apenas custom)
  - [ ] POST `/api/users/:id/roles` - Atribuir role a usuário
  - [ ] DELETE `/api/users/:id/roles/:role_id` - Remover role
  - [ ] GET `/api/permissions` - Listar todas as permissões
- [ ] Implementar middleware de autorização
  - [ ] Decorator @requires_permission('permission_name')
  - [ ] Verificar permissões do usuário
  - [ ] Retornar 403 Forbidden se não autorizado
- [ ] Aplicar autorização em todos os endpoints
  - [ ] Revisar cada endpoint
  - [ ] Adicionar decorators apropriados
  - [ ] Regras especiais (ex: profissional só vê próprios dados)
- [ ] Implementar helper functions
  - [ ] has_permission(user, permission)
  - [ ] has_role(user, role_name)
  - [ ] can_access_resource(user, resource)
- [ ] Implementar filtros por role
  - [ ] Profissionais só veem próprios agendamentos
  - [ ] Gerentes veem tudo exceto configurações sensíveis
  - [ ] Recepcionistas não veem relatórios financeiros

### Frontend
- [ ] Criar componente `RolesList.jsx`
  - [ ] Tabela de roles
  - [ ] Indicador de role sistema vs custom
  - [ ] Número de usuários por role
  - [ ] Ações (editar, deletar custom roles)
- [ ] Criar componente `RoleForm.jsx`
  - [ ] Nome e descrição
  - [ ] Checklist de permissões por módulo
  - [ ] Visual hierárquico (módulo > ações)
  - [ ] Validações
- [ ] Criar componente `PermissionsMatrix.jsx`
  - [ ] Tabela: Roles vs Permissões
  - [ ] Visualização clara de quem pode o quê
  - [ ] Modo de edição rápida
- [ ] Criar componente `UserRoleAssignment.jsx`
  - [ ] Multi-select de roles
  - [ ] Preview de permissões combinadas
  - [ ] Salvar atribuição
- [ ] Modificar `AuthContext.jsx`
  - [ ] Incluir roles e permissões do usuário
  - [ ] Função hasPermission(permission)
  - [ ] Função hasRole(roleName)
- [ ] Criar hook `usePermissions.js`
  - [ ] const { hasPermission, hasRole } = usePermissions()
  - [ ] Facilitar uso em componentes
- [ ] Criar componente `ProtectedAction.jsx`
  - [ ] Wrapper para botões/links
  - [ ] Só renderiza se usuário tem permissão
  - [ ] Exemplo: <ProtectedAction permission="delete:clients"><Button>Deletar</Button></ProtectedAction>
- [ ] Aplicar proteções em toda aplicação
  - [ ] Dashboard - mostrar/esconder cards baseado em permissões
  - [ ] Clientes - botões de ações
  - [ ] Profissionais - botões de ações
  - [ ] Serviços - botões de ações
  - [ ] Agendamentos - botões de ações, filtros
  - [ ] Lembretes - acesso ao módulo
  - [ ] Relatórios - acesso ao módulo
  - [ ] Configurações - seções visíveis
- [ ] Criar rota protegida `ProtectedRoute.jsx`
  - [ ] Verificar permissão antes de renderizar rota
  - [ ] Redirecionar para acesso negado se não autorizado
- [ ] Criar página `AccessDenied.jsx`
  - [ ] Mensagem amigável
  - [ ] Sugestão de contatar admin
  - [ ] Voltar para página anterior
- [ ] Criar página `RolesManagement.jsx`
  - [ ] Gestão completa de roles
  - [ ] Apenas acessível por admin
- [ ] Modificar `UserForm.jsx` / `Users.jsx`
  - [ ] Seção de atribuição de roles
  - [ ] Visualizar permissões
- [ ] Adicionar indicador visual
  - [ ] Badge com role do usuário no header
  - [ ] Tooltip explicando permissões

### Testes
- [ ] Testes de autorização por endpoint
- [ ] Testes de criação de role custom
- [ ] Testes de atribuição de role
- [ ] Testes de múltiplas roles
- [ ] Testes de proteção de UI
- [ ] Testes de edge cases (sem role, role deletado)

### Documentação
- [ ] Matriz de permissões documentada
- [ ] Guia para criar roles customizados
- [ ] FAQ sobre permissões

---

## 17. CHAT INTERNO

### Pesquisa
- [ ] Escolher tecnologia
  - [ ] WebSockets (Socket.io)
  - [ ] Server-Sent Events
  - [ ] Polling (menos preferível)
- [ ] Avaliar bibliotecas
  - [ ] Backend: Flask-SocketIO
  - [ ] Frontend: Socket.io-client

### Backend
- [ ] Instalar Flask-SocketIO
- [ ] Configurar WebSocket server
- [ ] Criar modelo `ChatRoom`
  - [ ] Campos: name, type (direct/group), created_by, created_at
- [ ] Criar modelo `ChatParticipant`
  - [ ] Campos: room_id, user_id, joined_at, last_read_at
- [ ] Criar modelo `ChatMessage`
  - [ ] Campos: room_id, user_id, message, message_type (text/image/file), attachment_url, sent_at, edited_at
- [ ] Criar modelo `ChatMessageReceipt`
  - [ ] Campos: message_id, user_id, read_at
- [ ] Criar migrations
- [ ] Implementar eventos Socket.IO
  - [ ] connect - usuário conecta
  - [ ] disconnect - usuário desconecta
  - [ ] join_room - entrar em sala
  - [ ] leave_room - sair de sala
  - [ ] send_message - enviar mensagem
  - [ ] typing - indicador de digitação
  - [ ] mark_as_read - marcar mensagens como lidas
- [ ] Implementar handlers
  - [ ] Autenticação via JWT em handshake
  - [ ] Validações de permissões
  - [ ] Broadcast de mensagens
  - [ ] Persistência de mensagens
  - [ ] Notificações para usuários offline
- [ ] Criar endpoints REST (fallback)
  - [ ] GET `/api/chat/rooms` - Listar salas do usuário
  - [ ] POST `/api/chat/rooms` - Criar sala
  - [ ] GET `/api/chat/rooms/:id/messages` - Histórico de mensagens
  - [ ] POST `/api/chat/messages/:id/read` - Marcar como lida
  - [ ] GET `/api/chat/unread` - Contador de não lidas
- [ ] Implementar upload de arquivos
  - [ ] Endpoint de upload
  - [ ] Validação de tipo e tamanho
  - [ ] Storage (S3 ou local)
  - [ ] Thumbnail para imagens
- [ ] Implementar busca de mensagens
  - [ ] Full-text search
  - [ ] Filtros por sala, usuário, data
- [ ] Implementar presença (online/offline)
  - [ ] Tracking de conexões ativas
  - [ ] Broadcast de status

### Frontend
- [ ] Instalar socket.io-client
- [ ] Criar contexto `ChatContext.jsx`
  - [ ] Conexão WebSocket
  - [ ] Estado de salas
  - [ ] Estado de mensagens
  - [ ] Funções de envio
  - [ ] Contador de não lidas
- [ ] Criar hook `useChat.js`
  - [ ] Abstração do contexto
  - [ ] Hooks para salas específicas
- [ ] Criar componente `ChatWindow.jsx`
  - [ ] Container principal do chat
  - [ ] Pode ser modal ou sidebar
  - [ ] Minimizar/Maximizar/Fechar
- [ ] Criar componente `ChatRoomList.jsx`
  - [ ] Lista de salas/conversas
  - [ ] Última mensagem
  - [ ] Badge de não lidas
  - [ ] Indicador online/offline
  - [ ] Buscar conversas
- [ ] Criar componente `ChatRoom.jsx`
  - [ ] Header com nome e participantes
  - [ ] Lista de mensagens
  - [ ] Input de mensagem
  - [ ] Ações (anexar, emoji)
  - [ ] Scroll para última mensagem
  - [ ] Load more ao scrollar para cima
- [ ] Criar componente `ChatMessage.jsx`
  - [ ] Bolha de mensagem
  - [ ] Avatar do usuário
  - [ ] Nome e timestamp
  - [ ] Suporte a texto, imagem, arquivo
  - [ ] Status de leitura (visto/entregue)
  - [ ] Opção de editar/deletar próprias mensagens
- [ ] Criar componente `ChatInput.jsx`
  - [ ] Textarea com auto-resize
  - [ ] Botão de envio
  - [ ] Indicador de digitação
  - [ ] Upload de arquivo
  - [ ] Emoji picker
  - [ ] Shortcuts (Enter para enviar, Shift+Enter para nova linha)
- [ ] Criar componente `ChatParticipants.jsx`
  - [ ] Lista de membros da sala
  - [ ] Status online/offline
  - [ ] Adicionar/remover participantes
- [ ] Criar componente `NewChatModal.jsx`
  - [ ] Selecionar usuário(s)
  - [ ] Criar chat direto ou grupo
  - [ ] Nome do grupo (se aplicável)
- [ ] Implementar notificações
  - [ ] Toast para novas mensagens
  - [ ] Som de notificação (opcional)
  - [ ] Badge no ícone de chat
  - [ ] Título da página pisca quando nova mensagem
- [ ] Adicionar botão de chat no header
  - [ ] Ícone com badge de não lidas
  - [ ] Clique abre ChatWindow
- [ ] Implementar busca de mensagens
  - [ ] Input de busca
  - [ ] Destacar resultados
  - [ ] Navegar entre resultados

### Features Avançadas (Opcional)
- [ ] Reações a mensagens (emoji)
- [ ] Thread/Respostas
- [ ] Menções (@usuário)
- [ ] Formatação de texto (bold, italic)
- [ ] Compartilhar agendamento no chat
- [ ] Videochamada integrada (WebRTC)

### Testes
- [ ] Testes de conexão WebSocket
- [ ] Testes de envio/recebimento de mensagens
- [ ] Testes de presença
- [ ] Testes de mensagens não lidas
- [ ] Testes de salas em grupo
- [ ] Testes de upload de arquivo
- [ ] Testes de reconexão

### Escalabilidade
- [ ] Configurar Redis para pub/sub (se múltiplos servers)
- [ ] Load balancing sticky sessions

### Documentação
- [ ] Guia de uso do chat
- [ ] Etiqueta de comunicação
- [ ] FAQ

---

## 18. FOLHA DE PONTO

### Backend
- [ ] Criar modelo `TimeSheet`
  - [ ] Campos: user_id, clock_in, clock_out, work_hours, break_hours, notes, status, created_at
- [ ] Criar modelo `BreakTime`
  - [ ] Campos: timesheet_id, break_start, break_end, duration
- [ ] Criar migrations
- [ ] Criar endpoints REST
  - [ ] POST `/api/timesheet/clock-in` - Registrar entrada
  - [ ] POST `/api/timesheet/clock-out` - Registrar saída
  - [ ] POST `/api/timesheet/break-start` - Iniciar pausa
  - [ ] POST `/api/timesheet/break-end` - Terminar pausa
  - [ ] GET `/api/timesheet/current` - Ponto atual do usuário
  - [ ] GET `/api/timesheet/user/:id` - Histórico por usuário
  - [ ] GET `/api/timesheet/report` - Relatório de pontos
  - [ ] PUT `/api/timesheet/:id` - Ajustar manualmente (admin)
- [ ] Implementar validações
  - [ ] Não pode dar clock-in se já está em expediente
  - [ ] Não pode dar clock-out sem clock-in
  - [ ] Validar ordem de eventos
  - [ ] Limite de horas por dia (alerta)
- [ ] Implementar cálculos
  - [ ] Horas trabalhadas
  - [ ] Horas de pausa
  - [ ] Horas líquidas
  - [ ] Horas extras
  - [ ] Totais por período
- [ ] Implementar relatórios
  - [ ] Por usuário
  - [ ] Por período
  - [ ] Totalizadores
  - [ ] Exportação para Excel

### Frontend
- [ ] Criar componente `ClockInOut.jsx`
  - [ ] Botão grande "REGISTRAR PONTO"
  - [ ] Exibir horário atual
  - [ ] Status atual (fora/dentro/pausa)
  - [ ] Último registro
  - [ ] Horas trabalhadas hoje
- [ ] Criar componente `TimeSheetCard.jsx`
  - [ ] Card no dashboard do profissional
  - [ ] Clock in/out rápido
  - [ ] Resumo do dia
- [ ] Criar componente `TimeSheetHistory.jsx`
  - [ ] Tabela de registros
  - [ ] Colunas: data, entrada, saída, pausas, total
  - [ ] Filtros de período
  - [ ] Indicador de irregularidades
- [ ] Criar componente `TimeSheetEdit.jsx`
  - [ ] Formulário de ajuste manual (admin)
  - [ ] Justificativa obrigatória
  - [ ] Log de alterações
- [ ] Criar componente `TimeSheetReport.jsx`
  - [ ] Relatório consolidado
  - [ ] Filtros: usuário, período
  - [ ] Gráficos de horas
  - [ ] Estatísticas (média, total, extras)
  - [ ] Exportação
- [ ] Criar página `TimeSheet.jsx`
  - [ ] Clock in/out
  - [ ] Histórico pessoal
  - [ ] Relatórios (admin)
- [ ] Adicionar widget no `Dashboard.jsx`
  - [ ] Clock in/out rápido
  - [ ] Status atual
- [ ] Implementar alertas
  - [ ] Esqueceu de bater ponto
  - [ ] Pausa muito longa
  - [ ] Jornada excessiva

### Geolocalização (Opcional)
- [ ] Capturar localização no clock in/out
- [ ] Validar se está no estabelecimento
- [ ] Relatório com mapa

### Testes
- [ ] Teste de registro de ponto
- [ ] Teste de pausas
- [ ] Teste de cálculos
- [ ] Teste de validações
- [ ] Teste de ajustes manuais

### Compliance
- [ ] Conformidade com legislação trabalhista
- [ ] Armazenamento seguro de dados
- [ ] Relatórios para auditorias

### Documentação
- [ ] Guia de uso da folha de ponto
- [ ] Políticas da empresa sobre ponto
- [ ] FAQ

---

## 19. MÚLTIPLAS UNIDADES/FRANQUIAS

### Planejamento
- [ ] Definir modelo de negócio
  - [ ] Unidades independentes com dados separados
  - [ ] Unidades com dashboard consolidado
  - [ ] Transferência de dados entre unidades
- [ ] Definir hierarquia
  - [ ] Matriz
  - [ ] Filiais
  - [ ] Franquias

### Backend
- [ ] Criar modelo `Organization`
  - [ ] Campos: name, type (headquarters/branch/franchise), parent_id, address, phone, email, settings, active, created_at
- [ ] Criar modelo `OrganizationUser`
  - [ ] Campos: organization_id, user_id, role_id
- [ ] Modificar modelos existentes
  - [ ] Adicionar organization_id em: Client, Professional, Service, Appointment, etc.
  - [ ] Índices para queries eficientes
- [ ] Criar migrations (cuidado com dados existentes)
- [ ] Criar endpoints REST
  - [ ] CRUD de organizações
  - [ ] GET `/api/organizations` - Listar organizações
  - [ ] POST `/api/organizations` - Criar organização
  - [ ] PUT `/api/organizations/:id` - Atualizar
  - [ ] DELETE `/api/organizations/:id` - Desativar
  - [ ] POST `/api/organizations/:id/users` - Adicionar usuário
  - [ ] GET `/api/organizations/:id/stats` - Estatísticas
  - [ ] GET `/api/organizations/consolidated` - Dashboard consolidado
- [ ] Implementar middleware de contexto
  - [ ] Detectar organização do usuário
  - [ ] Filtrar automaticamente queries por organization_id
  - [ ] Prevenir acesso cross-organization
- [ ] Implementar transferências
  - [ ] Transferir cliente entre unidades
  - [ ] Transferir profissional
  - [ ] Histórico de transferências
- [ ] Implementar dashboard consolidado
  - [ ] Agregar dados de todas as unidades
  - [ ] Comparativos
  - [ ] Rankings
- [ ] Implementar configurações por unidade
  - [ ] Personalização de logo
  - [ ] Horários de funcionamento
  - [ ] Serviços disponíveis
  - [ ] Lembretes customizados

### Frontend
- [ ] Criar componente `OrganizationSelector.jsx`
  - [ ] Dropdown de seleção de unidade
  - [ ] No header (se usuário tem acesso a múltiplas)
  - [ ] Persistir seleção
  - [ ] Atualizar contexto
- [ ] Criar componente `OrganizationsList.jsx`
  - [ ] Lista de unidades
  - [ ] Tipo e status
  - [ ] Estatísticas básicas
  - [ ] Ações (editar, configurar)
- [ ] Criar componente `OrganizationForm.jsx`
  - [ ] Dados da organização
  - [ ] Endereço completo
  - [ ] Contatos
  - [ ] Configurações
  - [ ] Logo upload
- [ ] Criar componente `ConsolidatedDashboard.jsx`
  - [ ] Métricas agregadas
  - [ ] Comparação entre unidades
  - [ ] Gráficos comparativos
  - [ ] Filtros
- [ ] Criar componente `OrganizationSettings.jsx`
  - [ ] Configurações específicas da unidade
  - [ ] Herdar da matriz ou customizar
- [ ] Criar componente `TransferModal.jsx`
  - [ ] Transferir cliente/profissional
  - [ ] Selecionar unidade destino
  - [ ] Confirmação
  - [ ] Motivo
- [ ] Modificar `AuthContext.jsx`
  - [ ] Incluir organização(ões) do usuário
  - [ ] Função para trocar contexto de organização
- [ ] Aplicar filtros em toda aplicação
  - [ ] Todos os listings filtram por organização atual
  - [ ] Formulários associam à organização atual
  - [ ] Relatórios por organização
- [ ] Criar página `Organizations.jsx`
  - [ ] Gestão completa (apenas admin matriz)
  - [ ] Dashboard consolidado
  - [ ] Comparativos
- [ ] Adicionar indicador visual
  - [ ] Nome da unidade atual no header
  - [ ] Ícone diferente por tipo

### Multi-tenancy
- [ ] Garantir isolamento de dados
- [ ] Testes de segurança
- [ ] Performance com muitas organizações

### Testes
- [ ] Teste de criação de unidade
- [ ] Teste de filtros por organização
- [ ] Teste de isolamento de dados
- [ ] Teste de transferências
- [ ] Teste de dashboard consolidado
- [ ] Teste de permissões cross-org

### Migração
- [ ] Plano de migração de dados existentes
  - [ ] Criar organização padrão
  - [ ] Associar dados existentes
  - [ ] Validar integridade
- [ ] Rollback plan

### Documentação
- [ ] Guia de configuração multi-unidades
- [ ] Como transferir dados
- [ ] Boas práticas

---

## 20. IA PARA HORÁRIOS OTIMIZADOS

### Pesquisa
- [ ] Estudar algoritmos de otimização
  - [ ] Machine Learning
  - [ ] Regras heurísticas
  - [ ] Algoritmos genéticos
- [ ] Definir features/variáveis
  - [ ] Histórico de agendamentos
  - [ ] Padrões de no-show
  - [ ] Duração real vs estimada
  - [ ] Preferências de clientes
  - [ ] Ocupação de profissionais
  - [ ] Dia da semana, hora
  - [ ] Clima, feriados

### Backend
- [ ] Escolher biblioteca ML
  - [ ] scikit-learn
  - [ ] TensorFlow
  - [ ] PyTorch
- [ ] Criar módulo de coleta de dados
  - [ ] Histórico de agendamentos
  - [ ] Features engineering
  - [ ] Limpeza de dados
- [ ] Criar modelo `MLModel`
  - [ ] Campos: name, version, type, parameters, accuracy, trained_at, active
- [ ] Criar modelo `PredictionLog`
  - [ ] Campos: model_id, input_data, prediction, actual_outcome, created_at
- [ ] Implementar modelos preditivos
  - [ ] Modelo 1: Predição de duração real
  - [ ] Modelo 2: Probabilidade de no-show
  - [ ] Modelo 3: Melhor horário para cliente
  - [ ] Modelo 4: Otimização de ocupação
- [ ] Criar pipeline de treinamento
  - [ ] Coleta de dados
  - [ ] Feature engineering
  - [ ] Split train/test
  - [ ] Treinamento
  - [ ] Validação
  - [ ] Salvar modelo
- [ ] Criar job de re-treinamento
  - [ ] Executar mensalmente
  - [ ] Avaliar performance
  - [ ] Deploy se melhor que anterior
- [ ] Criar endpoints REST
  - [ ] POST `/api/ai/suggest-times` - Sugerir melhores horários
  - [ ] POST `/api/ai/predict-no-show` - Probabilidade de no-show
  - [ ] POST `/api/ai/optimize-schedule` - Otimizar agenda
  - [ ] GET `/api/ai/models` - Listar modelos
  - [ ] POST `/api/ai/train` - Treinar modelo (admin)
  - [ ] GET `/api/ai/metrics` - Métricas dos modelos
- [ ] Implementar algoritmo de sugestão
  - [ ] Calcular score para cada slot disponível
  - [ ] Considerar múltiplos fatores
  - [ ] Ordenar por score
  - [ ] Retornar top N sugestões
- [ ] Implementar otimização de agenda
  - [ ] Redistribuir agendamentos
  - [ ] Minimizar gaps
  - [ ] Maximizar ocupação
  - [ ] Respeitar preferências

### Frontend
- [ ] Criar componente `AISuggestions.jsx`
  - [ ] Exibir sugestões de horários
  - [ ] Score visual
  - [ ] Motivo da sugestão
  - [ ] Botão para aceitar
- [ ] Criar componente `NoShowRisk.jsx`
  - [ ] Badge/indicador de risco
  - [ ] Cores (verde/amarelo/vermelho)
  - [ ] Tooltip explicativo
  - [ ] Sugestões de ações
- [ ] Criar componente `ScheduleOptimizer.jsx`
  - [ ] Visualização de otimização
  - [ ] Antes vs Depois
  - [ ] Métricas de melhoria
  - [ ] Aplicar otimização
- [ ] Integrar em `AppointmentForm.jsx`
  - [ ] Botão "Sugerir melhor horário"
  - [ ] Exibir sugestões
  - [ ] Pré-preencher ao selecionar
- [ ] Integrar em `Appointments.jsx`
  - [ ] Badge de risco de no-show
  - [ ] Ordenar por risco (opcional)
  - [ ] Filtro por risco alto
- [ ] Criar página `AIInsights.jsx`
  - [ ] Dashboard de IA
  - [ ] Métricas dos modelos
  - [ ] Accuracy, precision, recall
  - [ ] Análises preditivas
  - [ ] Treinamento de modelos
- [ ] Adicionar em `Dashboard.jsx`
  - [ ] Sugestões de otimização
  - [ ] Alertas de risco
  - [ ] Insights automáticos

### Modelos Específicos

#### Modelo 1: Duração Real
- [ ] Coletar dados históricos de duração
- [ ] Features: serviço, profissional, cliente, horário
- [ ] Treinar modelo de regressão
- [ ] Avaliar MAE/RMSE
- [ ] Usar para estimar duração mais precisa

#### Modelo 2: No-Show Prediction
- [ ] Coletar dados históricos de faltas
- [ ] Features: cliente, histórico, antecedência, dia, hora, clima
- [ ] Treinar modelo de classificação
- [ ] Avaliar AUC, precision, recall
- [ ] Definir threshold de risco

#### Modelo 3: Recomendação de Horário
- [ ] Coletar preferências implícitas
- [ ] Análise de padrões
- [ ] Collaborative filtering
- [ ] Ranking de horários

#### Modelo 4: Otimização de Agenda
- [ ] Algoritmo de otimização
- [ ] Função objetivo (maximizar ocupação, minimizar gaps)
- [ ] Restrições (preferências, disponibilidade)
- [ ] Solver

### Ética e Transparência
- [ ] Explicabilidade dos modelos
- [ ] SHAP values para interpretar predições
- [ ] Avisar usuários sobre uso de IA
- [ ] Consentimento para coleta de dados
- [ ] Opt-out de features de IA

### Testes
- [ ] Teste de cada modelo
- [ ] Teste de sugestões
- [ ] Teste de otimização
- [ ] A/B testing para validar impacto
- [ ] Monitoramento de accuracy em produção

### Infraestrutura
- [ ] GPU para treinamento (se necessário)
- [ ] Armazenamento de modelos
- [ ] Versionamento de modelos
- [ ] Serving de modelos

### Documentação
- [ ] Como funciona cada modelo
- [ ] Dados utilizados
- [ ] Métricas de performance
- [ ] Guia de interpretação

---

## 21. ANÁLISE PREDITIVA DE NO-SHOWS

*Este é parte do item 20 (IA), mas pode ser implementado separadamente como feature mais simples*

### Versão Simplificada (Sem ML)
- [ ] Sistema de pontuação baseado em regras
  - [ ] Histórico de faltas do cliente
  - [ ] Taxa de faltas geral
  - [ ] Antecedência do agendamento
  - [ ] Dia da semana
  - [ ] Horário
  - [ ] Cliente novo vs recorrente
  - [ ] Confirmou ou não
- [ ] Calcular score de risco (0-100)
- [ ] Categorizar em baixo/médio/alto risco
- [ ] Ações preventivas automáticas
  - [ ] Lembrete extra para risco alto
  - [ ] Solicitar confirmação
  - [ ] Cobrar antecipadamente
  - [ ] Política de cancelamento
- [ ] Relatório de predições vs realidade
- [ ] Ajuste de pesos das regras

*Veja checklist completo no item 20 para versão com ML*

---

## 22. APP MOBILE NATIVO

### Planejamento
- [ ] Escolher tecnologia
  - [ ] React Native (reuso de código do web)
  - [ ] Flutter
  - [ ] Nativo (Swift + Kotlin)
- [ ] Definir features para mobile
  - [ ] Todas as features do web?
  - [ ] Features essenciais apenas?
  - [ ] Features mobile-specific?
- [ ] Definir público
  - [ ] App para clientes (agendar)
  - [ ] App para profissionais (gerenciar)
  - [ ] App para admins (gestão completa)
  - [ ] Um app para todos com permissões?

### Setup
- [ ] Configurar ambiente React Native
- [ ] Criar projeto
- [ ] Configurar estrutura de pastas
- [ ] Setup de iOS
  - [ ] Xcode
  - [ ] CocoaPods
  - [ ] Certificados e provisioning
- [ ] Setup de Android
  - [ ] Android Studio
  - [ ] Gradle
  - [ ] Keystore para releases

### Backend
- [ ] Adaptar API para mobile
  - [ ] Endpoints otimizados
  - [ ] Payloads menores
  - [ ] Paginação eficiente
- [ ] Implementar push notifications
  - [ ] Firebase Cloud Messaging
  - [ ] Armazenar device tokens
  - [ ] Enviar notificações
  - [ ] POST `/api/mobile/register-device`
  - [ ] Notificar sobre novos agendamentos
  - [ ] Notificar sobre cancelamentos
  - [ ] Lembretes via push

### Frontend Mobile
- [ ] Criar navegação
  - [ ] React Navigation
  - [ ] Stack Navigator
  - [ ] Tab Navigator
  - [ ] Drawer Navigator
- [ ] Criar telas principais
  - [ ] LoginScreen
  - [ ] DashboardScreen
  - [ ] AppointmentsScreen
  - [ ] AppointmentDetailsScreen
  - [ ] NewAppointmentScreen
  - [ ] ClientsScreen
  - [ ] ClientDetailsScreen
  - [ ] ProfileScreen
  - [ ] SettingsScreen
- [ ] Implementar autenticação
  - [ ] Login/Logout
  - [ ] Persistir token (AsyncStorage)
  - [ ] Refresh token
- [ ] Implementar offline-first
  - [ ] Redux Persist ou similar
  - [ ] Queue de ações offline
  - [ ] Sincronização ao reconectar
- [ ] Implementar push notifications
  - [ ] Solicitar permissões
  - [ ] Lidar com notificações
  - [ ] Deep linking
- [ ] Implementar features mobile-specific
  - [ ] Câmera para foto de perfil
  - [ ] Geolocalização
  - [ ] Calendário nativo
  - [ ] Contatos nativos
  - [ ] Biometria (Face ID, Touch ID)
- [ ] Criar componentes otimizados
  - [ ] FlatList para listas grandes
  - [ ] Imagens otimizadas
  - [ ] Gestos nativos
- [ ] Implementar theme e design
  - [ ] Seguir guidelines (Material Design, iOS HIG)
  - [ ] Dark mode nativo
  - [ ] Acessibilidade

### Features Prioritárias
- [ ] Ver agenda do dia
- [ ] Criar/editar/cancelar agendamento
- [ ] Ver detalhes de clientes
- [ ] Completar agendamento
- [ ] Notificações push
- [ ] Sincronização offline

### Testing
- [ ] Testes unitários (Jest)
- [ ] Testes de integração
- [ ] Testes E2E (Detox)
- [ ] Testar em dispositivos reais
- [ ] Testar offline mode

### Deploy
- [ ] iOS
  - [ ] Apple Developer Account
  - [ ] App Store Connect
  - [ ] Testflight para beta
  - [ ] Submissão para revisão
  - [ ] Screenshots e descrição
- [ ] Android
  - [ ] Google Play Console
  - [ ] Configurar release
  - [ ] Testar com internal testing
  - [ ] Submissão para produção
  - [ ] Screenshots e descrição
- [ ] CI/CD
  - [ ] Fastlane para automação
  - [ ] GitHub Actions ou similar
  - [ ] Builds automáticos

### Documentação
- [ ] Guia de desenvolvimento
- [ ] Guia de deploy
- [ ] Changelog para usuários

---

## 23. SUPORTE MULTI-IDIOMA (i18n)

### Backend
- [ ] Instalar biblioteca de i18n
  - [ ] Flask-Babel
- [ ] Criar arquivos de tradução
  - [ ] messages.po para cada idioma
  - [ ] pt_BR, en_US, es_ES
- [ ] Marcar strings traduzíveis
  - [ ] _('String to translate')
  - [ ] Em mensagens de API
  - [ ] Em emails
  - [ ] Em lembretes
- [ ] Criar endpoint de idioma
  - [ ] PUT `/api/user/preferences/language`
- [ ] Detectar idioma do usuário
  - [ ] Accept-Language header
  - [ ] Preferência salva
  - [ ] Idioma do browser
- [ ] Implementar seleção por organização
  - [ ] Idioma padrão por unidade

### Frontend
- [ ] Instalar biblioteca de i18n
  - [ ] react-i18next
- [ ] Configurar i18next
  - [ ] Recursos de tradução
  - [ ] Detecção de idioma
  - [ ] Fallback
- [ ] Criar arquivos de tradução
  - [ ] JSON por idioma
  - [ ] pt-BR.json
  - [ ] en-US.json
  - [ ] es-ES.json
- [ ] Organizar por namespace
  - [ ] common, dashboard, appointments, etc.
- [ ] Marcar strings traduzíveis
  - [ ] useTranslation hook
  - [ ] {t('key')}
  - [ ] Passar por TODOS os componentes
- [ ] Criar componente `LanguageSelector.jsx`
  - [ ] Dropdown de idiomas
  - [ ] Bandeiras
  - [ ] Persistir seleção
- [ ] Adicionar no header
  - [ ] Seletor de idioma
- [ ] Traduzir conteúdo dinâmico
  - [ ] Nomes de status
  - [ ] Mensagens de erro
  - [ ] Validações
  - [ ] Tooltips
- [ ] Formato de data/hora por locale
  - [ ] date-fns com locales
  - [ ] Formatar datas corretamente
- [ ] Formato de números e moeda
  - [ ] Intl.NumberFormat
  - [ ] Moeda por região

### Traduções
- [ ] Português (pt-BR)
  - [ ] Revisão completa
  - [ ] Termos consistentes
- [ ] Inglês (en-US)
  - [ ] Tradução profissional
  - [ ] Revisão
- [ ] Espanhol (es-ES)
  - [ ] Tradução profissional
  - [ ] Revisão

### Contextos Especiais
- [ ] Emails traduzidos
- [ ] Lembretes traduzidos
- [ ] Notificações push traduzidas
- [ ] Relatórios traduzidos

### Testes
- [ ] Teste de troca de idioma
- [ ] Teste de cada idioma
- [ ] Teste de fallback
- [ ] Verificar strings faltantes
- [ ] Teste de formato de data/hora

### Documentação
- [ ] Guia para adicionar novos idiomas
- [ ] Guia para tradutores
- [ ] Lista de strings por contexto

---

## 24-35: MELHORIAS TÉCNICAS

## 24. CACHE REDIS

### Setup
- [ ] Instalar Redis
- [ ] Configurar Redis no servidor
- [ ] Instalar biblioteca (Flask-Caching, redis-py)

### Implementação
- [ ] Configurar Flask-Caching
- [ ] Identificar queries frequentes para cachear
  - [ ] Lista de profissionais
  - [ ] Lista de serviços
  - [ ] Disponibilidade de horários
  - [ ] Estatísticas do dashboard
- [ ] Implementar cache
  - [ ] Decorator @cache.cached(timeout=300)
  - [ ] Cache de função
  - [ ] Cache de view
- [ ] Implementar invalidação
  - [ ] Invalidar ao criar/editar/deletar
  - [ ] Cache key patterns
- [ ] Usar para sessions
  - [ ] Substituir sessions em arquivo
  - [ ] Flask-Session com Redis
- [ ] Usar para rate limiting
  - [ ] Contadores no Redis
  - [ ] Expiração automática

### Testes
- [ ] Teste de cache hit/miss
- [ ] Teste de invalidação
- [ ] Teste de expiração
- [ ] Benchmarks de performance

---

## 25. OTIMIZAÇÃO DE QUERIES

### Análise
- [ ] Identificar queries lentas
  - [ ] Logs de queries
  - [ ] pg_stat_statements (PostgreSQL)
  - [ ] Tempo de execução
- [ ] Usar EXPLAIN ANALYZE
  - [ ] Analisar plano de execução
  - [ ] Identificar bottlenecks

### Otimizações
- [ ] Criar índices apropriados
  - [ ] organization_id em todas as tabelas
  - [ ] foreign keys
  - [ ] Campos de busca
  - [ ] Campos de ordenação
- [ ] Otimizar joins
  - [ ] Evitar N+1 queries
  - [ ] Usar joinedload/selectinload
- [ ] Implementar paginação eficiente
  - [ ] Cursor-based pagination
  - [ ] Limit/offset otimizado
- [ ] Usar select específico
  - [ ] Não fazer SELECT *
  - [ ] Selecionar apenas campos necessários
- [ ] Implementar eager loading
  - [ ] Carregar relacionamentos de uma vez
- [ ] Adicionar query monitoring
  - [ ] Log de queries lentas
  - [ ] Alertas automáticos

### Testes
- [ ] Benchmarks antes/depois
- [ ] Load testing
- [ ] Monitoramento contínuo

---

## 26. PWA (PROGRESSIVE WEB APP)

### Implementação
- [ ] Criar Service Worker
  - [ ] Cache de assets estáticos
  - [ ] Cache de API responses
  - [ ] Estratégias de caching
  - [ ] Background sync
- [ ] Criar manifest.json
  - [ ] Nome e ícones
  - [ ] Cores do tema
  - [ ] Display mode
  - [ ] Start URL
- [ ] Adicionar meta tags
  - [ ] theme-color
  - [ ] apple-touch-icon
- [ ] Implementar offline mode
  - [ ] Detectar offline/online
  - [ ] Mostrar banner
  - [ ] Queue de ações
- [ ] Implementar install prompt
  - [ ] Botão "Instalar app"
  - [ ] beforeinstallprompt event
- [ ] Otimizar para lighthouse
  - [ ] Performance
  - [ ] Accessibility
  - [ ] Best Practices
  - [ ] SEO
  - [ ] PWA score

### Testes
- [ ] Teste offline
- [ ] Teste de instalação
- [ ] Teste em diferentes navegadores
- [ ] Lighthouse audit

---

## 27. TESTES E2E (CYPRESS/PLAYWRIGHT)

### Setup
- [ ] Escolher ferramenta (Cypress vs Playwright)
- [ ] Instalar e configurar
- [ ] Configurar ambiente de teste

### Casos de Teste
- [ ] Fluxo completo de login
- [ ] Criar cliente
- [ ] Criar profissional
- [ ] Criar serviço
- [ ] Criar agendamento
- [ ] Completar agendamento
- [ ] Gerar relatório
- [ ] Fluxo de lembretes
- [ ] Fluxo de pagamento

### CI/CD
- [ ] Integrar no pipeline
- [ ] Rodar em cada PR
- [ ] Screenshots de falhas
- [ ] Vídeos de execução

---

## 28. AUMENTAR COBERTURA DE TESTES (95%)

### Análise
- [ ] Gerar relatório de cobertura
- [ ] Identificar áreas sem cobertura
- [ ] Priorizar código crítico

### Implementação
- [ ] Testes unitários backend
  - [ ] Todos os models
  - [ ] Todas as views/endpoints
  - [ ] Helpers e utils
  - [ ] Business logic
- [ ] Testes unitários frontend
  - [ ] Todos os componentes
  - [ ] Hooks personalizados
  - [ ] Contexts
  - [ ] Utils
- [ ] Testes de integração
  - [ ] Fluxos completos
  - [ ] Integrações externas (mocked)
- [ ] Configurar CI
  - [ ] Falhar build se cobertura < 95%

---

## 29. AUDITORIA DE AÇÕES

### Backend
- [ ] Criar modelo `AuditLog`
  - [ ] Campos: user_id, action, resource_type, resource_id, old_value, new_value, ip_address, user_agent, created_at
- [ ] Criar migration
- [ ] Implementar decorator @audit_log
- [ ] Aplicar em operações críticas
  - [ ] CRUD de clientes
  - [ ] CRUD de profissionais
  - [ ] CRUD de serviços
  - [ ] CRUD de agendamentos
  - [ ] Pagamentos
  - [ ] Comissões
  - [ ] Alterações de usuário
  - [ ] Alterações de configurações
- [ ] Criar endpoint
  - [ ] GET `/api/audit-logs`

### Frontend
- [ ] Criar página `AuditLogs.jsx`
  - [ ] Lista de logs
  - [ ] Filtros avançados
  - [ ] Busca
  - [ ] Exportação
- [ ] Criar componente `AuditLogDetails.jsx`
  - [ ] Ver detalhes
  - [ ] Diff de valores

---

## 30. TELEMETRIA E MONITORAMENTO

### Sentry (Erros)
- [ ] Criar conta Sentry
- [ ] Instalar SDK backend
- [ ] Instalar SDK frontend
- [ ] Configurar environments
- [ ] Configurar source maps
- [ ] Testar captura de erros
- [ ] Configurar alertas

### Métricas (DataDog/New Relic/Prometheus)
- [ ] Escolher ferramenta
- [ ] Instalar agente
- [ ] Configurar dashboards
  - [ ] Performance de endpoints
  - [ ] Tempo de resposta
  - [ ] Taxa de erro
  - [ ] Uso de recursos
- [ ] Configurar alertas
  - [ ] Latência alta
  - [ ] Taxa de erro alta
  - [ ] Servidor down

### Logs
- [ ] Centralizar logs (ELK, Splunk)
- [ ] Estruturar logs (JSON)
- [ ] Níveis apropriados
- [ ] Rotação de logs

---

## 31. BACKUP AUTOMÁTICO

### Configuração
- [ ] Script de backup PostgreSQL
  - [ ] pg_dump
  - [ ] Compressão
  - [ ] Timestamp no nome
- [ ] Armazenamento
  - [ ] S3 ou similar
  - [ ] Retenção de 30 dias
  - [ ] Cleanup automático de backups antigos
- [ ] Cron job diário
  - [ ] Executar às 3h AM
  - [ ] Notificar em falhas
- [ ] Backup de uploads/arquivos
  - [ ] Sincronizar com S3
  - [ ] Versionamento

### Restore
- [ ] Documentar processo de restore
- [ ] Script de restore
- [ ] Testar restore mensalmente
- [ ] Disaster recovery plan

---

## 32. DOCUMENTAÇÃO DE API

### Swagger/OpenAPI
- [ ] Configurar Swagger UI
- [ ] Documentar cada endpoint
  - [ ] Descrição
  - [ ] Parâmetros
  - [ ] Request body
  - [ ] Responses
  - [ ] Códigos de erro
  - [ ] Exemplos
- [ ] Agrupar por módulo
- [ ] Adicionar autenticação
- [ ] Deploy da documentação

### Guias
- [ ] Guia de início rápido
- [ ] Guia de autenticação
- [ ] Guia de erros comuns
- [ ] Exemplos de integração

---

## 33-35: FEATURES ADICIONAIS

*Adicione aqui qualquer outra melhoria que surja durante o desenvolvimento*

---

## 🎯 RESUMO EXECUTIVO

**Total de Tasks:** ~2.000+ checkboxes
**Tempo Estimado Total:** 104 semanas (~2 anos)
**Equipe Recomendada:** 5 pessoas

### Como Usar:
1. Copie checklists específicos para seu gerenciador de projetos
2. Priorize baseado no roadmap (MELHORIAS.md)
3. Estime sprints (média 15-25 tasks por sprint de 2 semanas)
4. Marque como concluído conforme avança
5. Revise e adapte conforme necessário

### Próximos Passos:
1. Selecionar primeira melhoria para implementar
2. Copiar checklist para ferramenta de gestão
3. Quebrar em tickets individuais
4. Atribuir para equipe
5. Começar desenvolvimento!

---

*Boa sorte com as implementações! 🚀*
