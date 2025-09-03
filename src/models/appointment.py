from src.models.user import db
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
            'notification_sent': self.notification_sent,
            'reminder_sent': self.reminder_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'client': self.client.to_dict() if hasattr(self, 'client') and self.client else None,
            'professional': self.professional.to_dict() if hasattr(self, 'professional') and self.professional else None,
            'service': self.service.to_dict() if hasattr(self, 'service') and self.service else None
        }