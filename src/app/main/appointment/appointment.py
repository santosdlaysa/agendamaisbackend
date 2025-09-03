from src.models.user import db
from datetime import datetime, time

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), default='scheduled')  # scheduled, completed, cancelled, no_show
    notes = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    notification_sent = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Appointment {self.id} - {self.appointment_date} {self.start_time}>'

    def to_dict(self):
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
            'price': float(self.price) if self.price else 0,
            'notification_sent': self.notification_sent,
            'reminder_sent': self.reminder_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict_detailed(self):
        """Retorna dados do agendamento com informações detalhadas"""
        data = self.to_dict()
        
        # Adicionar dados do cliente
        if self.client:
            data['client'] = {
                'id': self.client.id,
                'name': self.client.name,
                'phone': self.client.phone,
                'email': self.client.email
            }
        
        # Adicionar dados do profissional
        if self.professional:
            data['professional'] = {
                'id': self.professional.id,
                'name': self.professional.name,
                'role': self.professional.role,
                'color': self.professional.color
            }
        
        # Adicionar dados do serviço
        if self.service:
            data['service'] = {
                'id': self.service.id,
                'name': self.service.name,
                'duration': self.service.duration,
                'price': float(self.service.price) if self.service.price else 0,
                'color': self.service.color
            }
        
        return data

    @staticmethod
    def check_conflict(professional_id, appointment_date, start_time, end_time, exclude_id=None):
        """Verifica se há conflito de horários para um profissional"""
        query = Appointment.query.filter(
            Appointment.professional_id == professional_id,
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(['scheduled', 'completed']),
            db.or_(
                db.and_(
                    Appointment.start_time <= start_time,
                    Appointment.end_time > start_time
                ),
                db.and_(
                    Appointment.start_time < end_time,
                    Appointment.end_time >= end_time
                ),
                db.and_(
                    Appointment.start_time >= start_time,
                    Appointment.end_time <= end_time
                )
            )
        )
        
        if exclude_id:
            query = query.filter(Appointment.id != exclude_id)
        
        return query.first() is not None

    def get_datetime(self):
        """Retorna datetime combinando data e hora de início"""
        if self.appointment_date and self.start_time:
            return datetime.combine(self.appointment_date, self.start_time)
        return None

    def get_end_datetime(self):
        """Retorna datetime combinando data e hora de fim"""
        if self.appointment_date and self.end_time:
            return datetime.combine(self.appointment_date, self.end_time)
        return None

