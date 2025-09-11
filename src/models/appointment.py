from src.config.database import db
from datetime import datetime

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), default='scheduled')
    notes = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    payment_method = db.Column(db.String(50))
    notification_sent = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'professional_id': self.professional_id,
            'service_id': self.service_id,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'status': self.status,
            'notes': self.notes,
            'price': float(self.price) if self.price else None,
            'payment_method': self.payment_method,
            'notification_sent': self.notification_sent,
            'reminder_sent': self.reminder_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'client': self.client.to_dict() if hasattr(self, 'client') and self.client else None,
            'professional': self.professional.to_dict() if hasattr(self, 'professional') and self.professional else None,
            'service': self.service.to_dict() if hasattr(self, 'service') and self.service else None
        }
    
    def to_dict_with_stats(self):
        """Converte o objeto para dicionário incluindo estatísticas"""
        appointment_dict = self.to_dict()
        appointment_dict['stats'] = {
            'duration_minutes': self.service.duration if hasattr(self, 'service') and self.service else 0,
            'price_formatted': f"R$ {float(self.price):.2f}" if self.price else "R$ 0,00",
            'is_past': self.appointment_date < datetime.now().date() if self.appointment_date else False,
            'is_today': self.appointment_date == datetime.now().date() if self.appointment_date else False
        }
        return appointment_dict
    
    def to_dict_detailed(self):
        """Converte o objeto para dicionário com informações detalhadas"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'professional_id': self.professional_id,
            'service_id': self.service_id,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'status': self.status,
            'notes': self.notes,
            'price': float(self.price) if self.price else None,
            'payment_method': self.payment_method,
            'notification_sent': self.notification_sent,
            'reminder_sent': self.reminder_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'client': self.client.to_dict() if hasattr(self, 'client') and self.client else None,
            'professional': self.professional.to_dict() if hasattr(self, 'professional') and self.professional else None,
            'service': self.service.to_dict() if hasattr(self, 'service') and self.service else None
        }
    
    def calculate_final_price(self):
        """Calcular preço final baseado no serviço"""
        if self.service:
            return float(self.service.price)
        return 0.0
    
    def complete_appointment(self):
        """Marcar agendamento como concluído e calcular valores"""
        self.status = 'completed'
        
        # Calcular preço automaticamente se não foi definido
        if not self.price:
            self.price = self.calculate_final_price()
        
        # Atualizar timestamp
        self.updated_at = datetime.utcnow()
        
        return {
            'status': 'completed',
            'price_calculated': float(self.price) if self.price else 0.0,
            'service_name': self.service.name if self.service else None,
            'completion_time': self.updated_at.isoformat()
        }
    
    @staticmethod
    def check_conflict(professional_id, appointment_date, start_time, end_time, exclude_appointment_id=None):
        """Verificar se existe conflito de horário"""
        query = Appointment.query.filter(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(['scheduled', 'confirmed'])
        )
        
        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)
        
        existing_appointments = query.all()
        
        for apt in existing_appointments:
            if (start_time < apt.end_time and end_time > apt.start_time):
                return True
        
        return False