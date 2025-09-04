from src.config.database import db
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
    
    appointments = db.relationship('Appointment', backref='client', lazy=True)
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
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
        """Converte o objeto para dicionário incluindo estatísticas"""
        client_dict = self.to_dict()
        client_dict['stats'] = {
            'total_appointments': len(self.appointments),
            'completed_appointments': len([apt for apt in self.appointments if apt.status == 'completed']),
            'pending_appointments': len([apt for apt in self.appointments if apt.status == 'scheduled'])
        }
        return client_dict