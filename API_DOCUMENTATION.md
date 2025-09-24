# 📚 API Documentation - AgendaMais Backend

## 🌐 Base URL
```
http://localhost:5000
```

---

## 🔐 Autenticação

### 1. **Registrar Usuário**
```http
POST /api/auth/register
```
**Headers:**
```json
{
  "Content-Type": "application/json"
}
```
**Body:**
```json
{
  "name": "Nome do Usuário",
  "email": "usuario@exemplo.com",
  "password": "senha123",
  "role": "admin" // opcional, padrão: "admin"
}
```
**Response (201):**
```json
{
  "message": "Usuário criado com sucesso",
  "user": {
    "id": 2,
    "name": "Nome do Usuário",
    "email": "usuario@exemplo.com",
    "role": "admin",
    "active": true,
    "created_at": "2025-09-11T12:35:15.383905",
    "updated_at": "2025-09-11T12:35:15.383920"
  }
}
```

### 2. **Login**
```http
POST /api/auth/login
```
**Body:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```
**Response (200):**
```json
{
  "message": "Login realizado com sucesso",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "name": "Nome do Usuário",
    "email": "usuario@exemplo.com",
    "role": "admin",
    "active": true
  }
}
```

### 3. **Dados do Usuário Atual**
```http
GET /api/auth/me
```
**Headers:**
```json
{
  "Authorization": "Bearer {access_token}"
}
```

### 4. **Alterar Senha**
```http
POST /api/auth/change-password
```
**Headers:**
```json
{
  "Authorization": "Bearer {access_token}",
  "Content-Type": "application/json"
}
```
**Body:**
```json
{
  "current_password": "senha_atual",
  "new_password": "nova_senha"
}
```

---

## 👥 Clientes

### 1. **Listar Clientes**
```http
GET /api/clients
```
**Query Parameters:**
- `page` (opcional): número da página (padrão: 1)
- `per_page` (opcional): itens por página (padrão: 50)
- `search` (opcional): buscar por nome, email ou telefone

**Response (200):**
```json
{
  "clients": [
    {
      "id": 1,
      "name": "Maria Santos",
      "email": "maria@teste.com",
      "phone": "11988888888",
      "notes": null,
      "created_at": "2025-09-11T13:13:57.569729",
      "updated_at": "2025-09-11T13:13:57.569736"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 1,
    "per_page": 50,
    "total": 1
  }
}
```

### 2. **Criar Cliente**
```http
POST /api/clients
```
**Body:**
```json
{
  "name": "Maria Santos",           // obrigatório
  "email": "maria@teste.com",       // opcional
  "phone": "11988888888",           // opcional
  "notes": "Cliente VIP"            // opcional
}
```

### 3. **Obter Cliente**
```http
GET /api/clients/{client_id}
```

### 4. **Atualizar Cliente**
```http
PUT /api/clients/{client_id}
```
**Body:** (mesmos campos do POST)

### 5. **Excluir Cliente**
```http
DELETE /api/clients/{client_id}
```

---

## 👨‍💼 Profissionais

### 1. **Listar Profissionais**
```http
GET /api/professionals
```
**Query Parameters:**
- `page`, `per_page`, `search` (mesmos do clientes)
- `active` (opcional): true/false para filtrar ativos

### 2. **Criar Profissional**
```http
POST /api/professionals
```
**Body:**
```json
{
  "name": "João Silva",            // obrigatório
  "role": "Barbeiro",              // obrigatório
  "phone": "11999999999",          // opcional
  "email": "joao@teste.com",       // opcional
  "color": "#3B82F6",              // opcional, padrão: "#3B82F6"
  "service_ids": [1, 2, 3],        // opcional: array de IDs dos serviços
  "active": true                   // opcional, padrão: true
}
```

### 3. **Atualizar Profissional**
```http
PUT /api/professionals/{professional_id}
```

### 4. **Obter Profissional**
```http
GET /api/professionals/{professional_id}
```

### 5. **Excluir Profissional**
```http
DELETE /api/professionals/{professional_id}
```

---

## 🛠️ Serviços

### 1. **Listar Serviços**
```http
GET /api/services
```

### 2. **Criar Serviço**
```http
POST /api/services
```
**Body:**
```json
{
  "name": "Corte de Cabelo",       // obrigatório
  "description": "Corte masculino completo", // opcional
  "price": 30.00,                 // obrigatório (decimal)
  "duration": 45,                 // obrigatório (minutos)
  "color": "#10B981",             // opcional, padrão: "#10B981"
  "active": true                  // opcional, padrão: true
}
```

### 3. **Atualizar Serviço**
```http
PUT /api/services/{service_id}
```

### 4. **Obter Serviço**
```http
GET /api/services/{service_id}
```

### 5. **Excluir Serviço**
```http
DELETE /api/services/{service_id}
```

---

## 📅 Agendamentos

### 1. **Listar Agendamentos**
```http
GET /api/appointments
```
**Query Parameters:**
- `page`, `per_page`: paginação
- `start_date`: YYYY-MM-DD (filtro data inicial)
- `end_date`: YYYY-MM-DD (filtro data final)
- `professional_id`: ID do profissional
- `client_id`: ID do cliente
- `service_id`: ID do serviço
- `status`: scheduled, completed, cancelled, no_show, confirmed

**Response (200):**
```json
{
  "appointments": [
    {
      "id": 1,
      "client_id": 3,
      "professional_id": 4,
      "service_id": 3,
      "appointment_date": "2025-09-11",
      "start_time": "14:00",
      "end_time": "14:45",
      "status": "completed",
      "notes": "Serviço realizado com sucesso",
      "price": 30.0,
      "notification_sent": false,
      "reminder_sent": false,
      "created_at": "2025-09-11T13:14:05.029842",
      "updated_at": "2025-09-11T13:14:13.812307",
      "client": { /* dados do cliente */ },
      "professional": { /* dados do profissional */ },
      "service": { /* dados do serviço */ }
    }
  ],
  "pagination": { /* dados de paginação */ }
}
```

### 2. **Criar Agendamento**
```http
POST /api/appointments
```
**Body:**
```json
{
  "client_id": 3,                 // obrigatório
  "professional_id": 4,           // obrigatório
  "service_id": 3,                // obrigatório
  "appointment_date": "2025-09-11", // obrigatório (YYYY-MM-DD)
  "start_time": "14:00",          // obrigatório (HH:MM)
  "status": "scheduled",          // opcional, padrão: "scheduled"
  "notes": "Observações",         // opcional
  "price": 35.00                  // opcional, padrão: preço do serviço
}
```

### 3. **Atualizar Agendamento (Reagendar)**
```http
PUT /api/appointments/{appointment_id}
```
**Body:** (mesmos campos do POST)

### 4. **Obter Agendamento**
```http
GET /api/appointments/{appointment_id}
```

### 5. **Excluir Agendamento**
```http
DELETE /api/appointments/{appointment_id}
```

### 6. **🔥 Concluir Agendamento com Cálculo Automático**
```http
PUT /api/appointments/{appointment_id}/complete
```
**Body:**
```json
{
  "notes": "Serviço realizado com sucesso",  // opcional
  "custom_price": 35.00                      // opcional: override do preço
}
```
**Response (200):**
```json
{
  "message": "Agendamento concluído com sucesso e valores calculados",
  "appointment": { /* dados completos do agendamento */ },
  "calculation": {
    "status": "completed",
    "price_calculated": 35.0,
    "service_name": "Corte de Cabelo",
    "completion_time": "2025-09-11T13:14:13.976386",
    "price_override": true  // apenas se custom_price foi usado
  },
  "service_details": {
    "service_name": "Corte de Cabelo",
    "service_duration": 45,
    "original_price": 30.0,
    "final_price": 35.0,
    "professional": "João Silva",
    "client": "Maria Santos",
    "date": "2025-09-11",
    "time": "14:00 - 14:45"
  }
}
```

### 7. **Atualizar Status do Agendamento**
```http
PUT /api/appointments/{appointment_id}/status
```
**Body:**
```json
{
  "status": "completed",          // obrigatório: scheduled, completed, cancelled, no_show, confirmed
  "notes": "Observações",         // opcional
  "price": 40.00                  // opcional: override manual do preço
}
```

### 8. **Verificar Disponibilidade**
```http
POST /api/appointments/check-availability
```
**Body:**
```json
{
  "professional_id": 4,           // obrigatório
  "service_id": 3,                // obrigatório
  "appointment_date": "2025-09-11", // obrigatório (YYYY-MM-DD)
  "start_time": "14:00",          // obrigatório (HH:MM)
  "exclude_appointment_id": 1     // opcional: para reagendamento
}
```
**Response (200):**
```json
{
  "available": true,
  "end_time": "14:45"
}
```

### 9. **Agendamentos para Calendário**
```http
GET /api/appointments/calendar
```
**Query Parameters:**
- `start_date`: YYYY-MM-DD (obrigatório)
- `end_date`: YYYY-MM-DD (obrigatório)
- `professional_id`: ID do profissional (opcional)

**Response (200):**
```json
{
  "events": [
    {
      "id": 1,
      "title": "Maria Santos - Corte de Cabelo",
      "start": "2025-09-11T14:00",
      "end": "2025-09-11T14:45",
      "backgroundColor": "#3B82F6",
      "borderColor": "#3B82F6",
      "textColor": "#ffffff",
      "extendedProps": {
        "appointment": { /* dados completos do agendamento */ }
      }
    }
  ]
}
```

### 10. **🔥 Relatório Financeiro**
```http
GET /api/appointments/financial-report
```
**Query Parameters:**
- `start_date`: YYYY-MM-DD (opcional)
- `end_date`: YYYY-MM-DD (opcional)
- `professional_id`: ID do profissional (opcional)
- `service_id`: ID do serviço (opcional)

**Response (200):**
```json
{
  "financial_summary": {
    "total_revenue": 315.0,
    "total_appointments": 3,
    "average_ticket": 105.0,
    "period": {
      "start_date": "2025-09-01",
      "end_date": "2025-09-30"
    }
  },
  "service_breakdown": {
    "Corte de Cabelo": {
      "count": 2,
      "total_revenue": 65.0,
      "service_id": 3,
      "average_price": 32.5
    }
  },
  "professional_breakdown": {
    "João Silva": {
      "count": 2,
      "total_revenue": 65.0,
      "professional_id": 4,
      "average_ticket": 32.5
    }
  },
  "appointment_details": [
    {
      "id": 2,
      "date": "2025-09-11",
      "client": "Maria Santos",
      "professional": "João Silva",
      "service": "Corte de Cabelo",
      "price": 30.0,
      "duration": 45,
      "start_time": "14:00",
      "end_time": "14:45",
      "notes": "Serviço realizado com sucesso"
    }
  ]
}
```

---

## 📊 Status de Agendamento

### Status Válidos:
- `scheduled` - Agendado
- `confirmed` - Confirmado
- `completed` - Concluído ✅
- `cancelled` - Cancelado
- `no_show` - Faltou

---

## ⚠️ Códigos de Erro

### Códigos HTTP:
- `200` - Sucesso
- `201` - Criado com sucesso
- `400` - Dados inválidos
- `401` - Não autorizado
- `404` - Não encontrado
- `500` - Erro interno do servidor

### Estrutura de Erro:
```json
{
  "message": "Descrição do erro"
}
```

---

## 🔥 Funcionalidades Especiais

### 1. **Cálculo Automático de Preços**
- Ao usar `PUT /api/appointments/{id}/complete`, o preço é calculado automaticamente baseado no serviço
- Use `custom_price` para sobrescrever o preço quando necessário
- O sistema registra se houve override de preço

### 2. **Verificação de Conflitos**
- Ao criar/atualizar agendamentos, o sistema verifica conflitos de horário automaticamente
- Use `/check-availability` para verificar antes de criar

### 3. **Relatórios Financeiros**
- Análise completa de receita por período
- Breakdown por serviço e profissional
- Cálculo de ticket médio e estatísticas

### 4. **Calendário**
- Endpoint específico para integração com calendários (FullCalendar, etc.)
- Eventos formatados com cores e informações completas

---

## 💡 Exemplos de Uso no Frontend

### JavaScript/Fetch:
```javascript
// Concluir agendamento com cálculo automático
const completeAppointment = async (appointmentId, notes, customPrice = null) => {
  const body = { notes };
  if (customPrice) body.custom_price = customPrice;
  
  const response = await fetch(`/api/appointments/${appointmentId}/complete`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(body)
  });
  
  return await response.json();
};

// Obter relatório financeiro
const getFinancialReport = async (startDate, endDate) => {
  const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
  const response = await fetch(`/api/appointments/financial-report?${params}`);
  return await response.json();
};
```

### Axios:
```javascript
// Criar agendamento
const createAppointment = async (appointmentData) => {
  try {
    const response = await axios.post('/api/appointments', appointmentData);
    return response.data;
  } catch (error) {
    throw error.response.data;
  }
};
```

---

## 📱 Lembretes Automáticos

### 1. **Listar Lembretes**
```http
GET /api/reminders
```
**Query Parameters:**
- `page`, `per_page`: paginação
- `appointment_id`: ID do agendamento
- `professional_id`: ID do profissional
- `client_id`: ID do cliente
- `reminder_type`: whatsapp ou sms
- `status`: pending, sent, failed
- `start_date`: YYYY-MM-DD (filtro data inicial)
- `end_date`: YYYY-MM-DD (filtro data final)

**Response (200):**
```json
{
  "reminders": [
    {
      "id": 1,
      "appointment_id": 5,
      "reminder_type": "whatsapp",
      "reminder_time": "2025-09-10T13:00:00",
      "message": "🗓️ *Lembrete de Agendamento*\n\nOlá *Maria Santos*!...",
      "phone_number": "+5511999999999",
      "status": "sent",
      "sent_at": "2025-09-10T13:00:15",
      "error_message": null,
      "attempts": 1,
      "created_at": "2025-09-09T14:00:00",
      "updated_at": "2025-09-10T13:00:15",
      "appointment": {
        /* dados completos do agendamento */
      }
    }
  ],
  "pagination": { /* dados de paginação */ }
}
```

### 2. **Obter Lembrete Específico**
```http
GET /api/reminders/{reminder_id}
```

### 3. **Criar Lembretes para Agendamento**
```http
POST /api/reminders/appointment/{appointment_id}
```
**Response (201):**
```json
{
  "message": "Lembretes criados com sucesso",
  "success": true,
  "appointment_id": 5,
  "reminders_created": [
    {
      "type": "whatsapp",
      "scheduled_for": "2025-09-10T13:00:00",
      "hours_before": 24
    }
  ],
  "total_reminders": 1
}
```

### 4. **Enviar Lembrete Imediatamente**
```http
POST /api/reminders/{reminder_id}/send
```
**Response (200):**
```json
{
  "message": "Lembrete enviado com sucesso",
  "success": true,
  "reminder_id": 1,
  "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "sent_at": "2025-09-10T14:30:00"
}
```

### 5. **Excluir Lembrete**
```http
DELETE /api/reminders/{reminder_id}
```

### 6. **Obter Configurações de Lembrete**
```http
GET /api/reminders/settings?professional_id={id}
```
**Response (200):**
```json
{
  "professional_id": 1,
  "professional_name": "João Silva",
  "settings": [
    {
      "id": 1,
      "professional_id": 1,
      "reminder_type": "whatsapp",
      "enabled": true,
      "hours_before": 24,
      "custom_message": null,
      "created_at": "2025-09-10T10:00:00",
      "updated_at": "2025-09-10T10:00:00"
    },
    {
      "id": 2,
      "professional_id": 1,
      "reminder_type": "sms",
      "enabled": false,
      "hours_before": 24,
      "custom_message": null,
      "created_at": "2025-09-10T10:00:00",
      "updated_at": "2025-09-10T10:00:00"
    }
  ]
}
```

### 7. **Atualizar Configurações de Lembrete**
```http
PUT /api/reminders/settings
```
**Body:**
```json
{
  "professional_id": 1,
  "settings": [
    {
      "reminder_type": "whatsapp",
      "enabled": true,
      "hours_before": 24,
      "custom_message": "Olá {client_name}! Lembrete do seu agendamento amanhã às {time} com {professional_name}."
    },
    {
      "reminder_type": "sms",
      "enabled": false,
      "hours_before": 2
    }
  ]
}
```

### 8. **Lembretes Próximos**
```http
GET /api/reminders/upcoming?hours=24
```
**Response (200):**
```json
{
  "success": true,
  "count": 3,
  "reminders": [
    {
      "id": 5,
      "reminder_time": "2025-09-11T09:00:00",
      "reminder_type": "whatsapp",
      "status": "pending",
      "appointment": { /* dados do agendamento */ }
    }
  ]
}
```

### 9. **Processar Lembretes Pendentes**
```http
POST /api/reminders/process
```
**Response (200):**
```json
{
  "message": "Lembretes processados com sucesso",
  "success": true,
  "processed_count": 2,
  "results": [
    {
      "reminder_id": 5,
      "appointment_id": 10,
      "type": "whatsapp",
      "result": {
        "success": true,
        "reminder_id": 5,
        "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "sent_at": "2025-09-11T09:00:15"
      }
    }
  ]
}
```

### 10. **Agendador Automático**

#### Iniciar Agendador:
```http
POST /api/reminders/scheduler/start
```

#### Parar Agendador:
```http
POST /api/reminders/scheduler/stop
```

#### Status do Agendador:
```http
GET /api/reminders/scheduler/status
```
**Response (200):**
```json
{
  "scheduler": {
    "running": true,
    "check_interval": 300,
    "thread_alive": true
  }
}
```

### 11. **Testes de Conexão**

#### Testar WhatsApp:
```http
POST /api/reminders/test/whatsapp
```

#### Testar SMS:
```http
POST /api/reminders/test/sms
```

### 12. **Estatísticas dos Lembretes**
```http
GET /api/reminders/stats
```
**Query Parameters:**
- `start_date`: YYYY-MM-DD (opcional)
- `end_date`: YYYY-MM-DD (opcional)
- `professional_id`: ID do profissional (opcional)

**Response (200):**
```json
{
  "stats": {
    "total_reminders": 50,
    "sent_reminders": 45,
    "pending_reminders": 3,
    "failed_reminders": 2,
    "success_rate": 90.0,
    "by_type": {
      "whatsapp": 35,
      "sms": 15
    },
    "period": {
      "start_date": "2025-09-01",
      "end_date": "2025-09-30"
    }
  }
}
```

---

## 🔧 Configuração dos Lembretes

### Variáveis de Ambiente Obrigatórias:
```env
# Configurações Twilio para WhatsApp e SMS
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_FROM=+14155238886
TWILIO_SMS_FROM=+1234567890

# Números para teste (opcional)
TEST_WHATSAPP_NUMBER=+5511999999999
TEST_SMS_NUMBER=+5511999999999

# Configurações do agendador de lembretes
REMINDER_CHECK_INTERVAL=300
```

### Framework e Stack:
- **Backend:** Flask 2.3.3 (Python)
- **ORM:** SQLAlchemy via Flask-SQLAlchemy 3.0.5
- **Banco de Dados:** PostgreSQL ou SQLite
- **Notificações:** Twilio API (WhatsApp & SMS)
- **Autenticação:** JWT via Flask-JWT-Extended

### Funcionalidades dos Lembretes:
- ✅ **Criação automática** ao fazer agendamento
- ✅ **Configurações por profissional** (WhatsApp/SMS)
- ✅ **Agendamento automático** com processamento em background
- ✅ **Retry automático** para falhas (máx 3 tentativas)
- ✅ **Mensagens personalizáveis** com templates
- ✅ **Monitoramento e estatísticas** completas
- ✅ **Testes de conexão** para WhatsApp e SMS

### Novos Campos no Agendamento:
Quando um agendamento é criado, a resposta agora inclui:
```json
{
  "message": "Agendamento criado com sucesso",
  "appointment": { /* dados do agendamento */ },
  "reminders_created": [
    {
      "type": "whatsapp",
      "scheduled_for": "2025-09-10T13:00:00",
      "hours_before": 24
    }
  ],
  "total_reminders": 1
}
```

---

*Documentação atualizada em: 23/09/2025*  
*Versão da API: 1.1*  
*Framework: Flask 2.3.3 + SQLAlchemy*