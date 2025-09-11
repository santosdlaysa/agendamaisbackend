# 💰 Rotas de Cálculo de Valores - Frontend Guide

## 🎯 Principais Rotas para o Frontend

### 1. **🔥 Concluir Agendamento com Cálculo Automático**

**Rota Mais Importante:**
```http
PUT /api/appointments/{appointment_id}/complete
```

**Dados para Enviar:**
```javascript
// Exemplo 1: Cálculo automático (usa preço do serviço)
{
  "notes": "Serviço realizado com sucesso"
}

// Exemplo 2: Com preço personalizado
{
  "notes": "Cliente pediu serviço adicional",
  "custom_price": 45.00
}
```

**Código JavaScript:**
```javascript
const completeAppointment = async (appointmentId, notes, customPrice = null) => {
  const body = { notes };
  if (customPrice) {
    body.custom_price = customPrice;
  }
  
  const response = await fetch(`/api/appointments/${appointmentId}/complete`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });
  
  const result = await response.json();
  
  // result.calculation.price_calculated - valor calculado
  // result.service_details.final_price - preço final
  // result.calculation.price_override - se houve override
  
  return result;
};
```

**Resposta da API:**
```json
{
  "message": "Agendamento concluído com sucesso e valores calculados",
  "calculation": {
    "status": "completed",
    "price_calculated": 35.0,
    "service_name": "Corte de Cabelo", 
    "completion_time": "2025-09-11T13:14:13.976386",
    "price_override": true
  },
  "service_details": {
    "original_price": 30.0,
    "final_price": 35.0,
    "service_name": "Corte de Cabelo",
    "professional": "João Silva",
    "client": "Maria Santos"
  }
}
```

---

### 2. **📊 Relatório Financeiro**

```http
GET /api/appointments/financial-report
```

**Query Parameters:**
```javascript
const params = {
  start_date: '2025-09-01',    // opcional: YYYY-MM-DD
  end_date: '2025-09-30',      // opcional: YYYY-MM-DD  
  professional_id: 4,          // opcional: filtrar por profissional
  service_id: 3                // opcional: filtrar por serviço
};
```

**Código JavaScript:**
```javascript
const getFinancialReport = async (filters = {}) => {
  const params = new URLSearchParams();
  
  if (filters.startDate) params.append('start_date', filters.startDate);
  if (filters.endDate) params.append('end_date', filters.endDate);
  if (filters.professionalId) params.append('professional_id', filters.professionalId);
  if (filters.serviceId) params.append('service_id', filters.serviceId);
  
  const response = await fetch(`/api/appointments/financial-report?${params}`);
  return await response.json();
};

// Exemplo de uso
const report = await getFinancialReport({
  startDate: '2025-09-01',
  endDate: '2025-09-30',
  professionalId: 4
});

console.log(`Receita Total: R$ ${report.financial_summary.total_revenue}`);
console.log(`Ticket Médio: R$ ${report.financial_summary.average_ticket}`);
```

---

### 3. **Atualizar Status (Método Alternativo)**

```http
PUT /api/appointments/{appointment_id}/status
```

**Para marcar como concluído:**
```javascript
const updateStatus = async (appointmentId, status, notes = '', customPrice = null) => {
  const body = { status, notes };
  if (customPrice) body.price = customPrice;
  
  const response = await fetch(`/api/appointments/${appointmentId}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  
  return await response.json();
};

// Usar para concluir (mas recomendo usar /complete)
await updateStatus(1, 'completed', 'Serviço finalizado', 40.00);
```

---

## 🛠️ Componentes React Sugeridos

### 1. **Componente para Concluir Agendamento**

```jsx
import React, { useState } from 'react';

const CompleteAppointmentModal = ({ appointment, onComplete, onClose }) => {
  const [notes, setNotes] = useState('');
  const [customPrice, setCustomPrice] = useState('');
  const [loading, setLoading] = useState(false);

  const handleComplete = async () => {
    setLoading(true);
    try {
      const result = await fetch(`/api/appointments/${appointment.id}/complete`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          notes,
          custom_price: customPrice ? parseFloat(customPrice) : null
        })
      });
      
      const data = await result.json();
      
      if (result.ok) {
        onComplete(data);
        alert(`Agendamento concluído! Valor: R$ ${data.calculation.price_calculated}`);
      } else {
        alert(data.message);
      }
    } catch (error) {
      alert('Erro ao concluir agendamento');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal">
      <h3>Concluir Agendamento</h3>
      
      <div>
        <label>Cliente: {appointment.client.name}</label>
        <label>Serviço: {appointment.service.name}</label>
        <label>Preço Original: R$ {appointment.service.price}</label>
      </div>
      
      <textarea
        placeholder="Observações (opcional)"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />
      
      <input
        type="number"
        step="0.01"
        placeholder={`Preço customizado (padrão: R$ ${appointment.service.price})`}
        value={customPrice}
        onChange={(e) => setCustomPrice(e.target.value)}
      />
      
      <div>
        <button onClick={handleComplete} disabled={loading}>
          {loading ? 'Processando...' : 'Concluir e Calcular'}
        </button>
        <button onClick={onClose}>Cancelar</button>
      </div>
    </div>
  );
};
```

### 2. **Componente de Relatório Financeiro**

```jsx
const FinancialReport = () => {
  const [report, setReport] = useState(null);
  const [filters, setFilters] = useState({
    startDate: '2025-09-01',
    endDate: '2025-09-30'
  });

  const loadReport = async () => {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/appointments/financial-report?${params}`);
    const data = await response.json();
    setReport(data);
  };

  useEffect(() => {
    loadReport();
  }, [filters]);

  if (!report) return <div>Carregando...</div>;

  return (
    <div>
      <h2>Relatório Financeiro</h2>
      
      <div className="summary">
        <div>Receita Total: R$ {report.financial_summary.total_revenue}</div>
        <div>Total de Agendamentos: {report.financial_summary.total_appointments}</div>
        <div>Ticket Médio: R$ {report.financial_summary.average_ticket}</div>
      </div>
      
      <h3>Por Serviço:</h3>
      {Object.entries(report.service_breakdown).map(([service, data]) => (
        <div key={service}>
          {service}: {data.count} agendamentos - R$ {data.total_revenue}
        </div>
      ))}
      
      <h3>Por Profissional:</h3>
      {Object.entries(report.professional_breakdown).map(([professional, data]) => (
        <div key={professional}>
          {professional}: {data.count} agendamentos - R$ {data.total_revenue}
        </div>
      ))}
    </div>
  );
};
```

---

## 🎯 Fluxo Recomendado no Frontend

### 1. **Lista de Agendamentos**
```javascript
// Buscar agendamentos do dia
const todayAppointments = await fetch('/api/appointments?appointment_date=2025-09-11&status=scheduled');
```

### 2. **Botão "Concluir"**
```javascript
// Ao clicar no botão "Concluir" de um agendamento
const completeButton = (appointment) => {
  return (
    <button onClick={() => completeAppointment(appointment.id, 'Serviço realizado')}>
      Concluir (R$ {appointment.service.price})
    </button>
  );
};
```

### 3. **Confirmação Visual**
```javascript
// Após conclusão, mostrar resultado
const showCompletionResult = (result) => {
  const message = `
    Agendamento concluído!
    Serviço: ${result.service_details.service_name}
    Valor cobrado: R$ ${result.calculation.price_calculated}
    ${result.calculation.price_override ? '(Preço customizado)' : '(Preço padrão)'}
  `;
  alert(message);
};
```

---

## 📋 Checklist para o Frontend

### ✅ Implementar:
- [ ] Modal/formulário para concluir agendamento
- [ ] Campo para observações da conclusão
- [ ] Campo opcional para preço customizado
- [ ] Exibição do preço calculado após conclusão
- [ ] Relatório financeiro com filtros
- [ ] Dashboard com estatísticas
- [ ] Indicador visual de agendamentos concluídos

### 🔥 Funcionalidades Especiais:
- [ ] Botão "Concluir com Preço Padrão" (sem modal)
- [ ] Botão "Concluir com Preço Personalizado" (com modal)
- [ ] Exibição de override de preço no histórico
- [ ] Gráficos de receita por período
- [ ] Comparação de ticket médio por profissional

---

**Base URL:** `http://localhost:5000`  
**Todas as rotas retornam JSON**  
**Status HTTP: 200 = sucesso, 400 = erro de dados, 404 = não encontrado**