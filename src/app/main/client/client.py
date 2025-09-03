from src.models.user import db
from datetime import datetime

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com agendamentos
    appointments = db.relationship('Appointment', backref='client', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Client {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict_with_stats(self):
        """Retorna dados do cliente com estatísticas"""
        data = self.to_dict()
        data['total_appointments'] = len(self.appointments)
        data['last_appointment'] = None
        
        if self.appointments:
            last_appointment = max(self.appointments, key=lambda x: x.appointment_date)
            data['last_appointment'] = last_appointment.appointment_date.isoformat()
            
        return data

