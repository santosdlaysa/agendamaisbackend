from src.config.database import db
from datetime import datetime


class Reminder(db.Model):
    """Modelo para lembretes de agendamentos"""
    __tablename__ = 'reminders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)

    # Tipo de lembrete
    type = db.Column(db.String(50), nullable=False)  # email, sms, whatsapp

    # Status do lembrete
    status = db.Column(db.String(50), default='pending')  # pending, scheduled, sent, failed, cancelled

    # Quando enviar
    scheduled_at = db.Column(db.DateTime, nullable=False)

    # Quando foi enviado
    sent_at = db.Column(db.DateTime)

    # ID da mensagem no provedor (Twilio, etc)
    external_id = db.Column(db.String(100))

    # Mensagem enviada
    message_content = db.Column(db.Text)

    # Erro se falhou
    error_message = db.Column(db.Text)

    # Tentativas de envio
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=3)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref=db.backref('reminders', lazy=True))
    appointment = db.relationship('Appointment', backref=db.backref('reminders', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'appointment_id': self.appointment_id,
            'type': self.type,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'external_id': self.external_id,
            'error_message': self.error_message,
            'attempts': self.attempts,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def to_dict_with_appointment(self):
        data = self.to_dict()
        if self.appointment:
            data['appointment'] = {
                'id': self.appointment.id,
                'date': self.appointment.appointment_date.isoformat() if self.appointment.appointment_date else None,
                'time': str(self.appointment.start_time)[:5] if self.appointment.start_time else None,
                'client_name': self.appointment.client.name if self.appointment.client else None,
                'service_name': self.appointment.service.name if self.appointment.service else None
            }
        return data


class ReminderLog(db.Model):
    """Log de todas as tentativas de envio de lembretes"""
    __tablename__ = 'reminder_logs'

    id = db.Column(db.Integer, primary_key=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('reminders.id'), nullable=False)

    # Resultado da tentativa
    success = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text)

    # ID externo se sucesso
    external_id = db.Column(db.String(100))

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento
    reminder = db.relationship('Reminder', backref=db.backref('logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'reminder_id': self.reminder_id,
            'success': self.success,
            'error_message': self.error_message,
            'external_id': self.external_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
