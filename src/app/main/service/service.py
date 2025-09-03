from src.models.user import db
from datetime import datetime

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # duração em minutos
    color = db.Column(db.String(7), default='#10B981')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    appointments = db.relationship('Appointment', backref='service', lazy=True)
    professionals = db.relationship('Professional', secondary='professional_services', back_populates='services')

    def __repr__(self):
        return f'<Service {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0,
            'duration': self.duration,
            'color': self.color,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict_with_professionals(self):
        """Retorna dados do serviço com profissionais"""
        data = self.to_dict()
        data['professionals'] = [prof.to_dict() for prof in self.professionals if prof.active]
        return data

    def to_dict_with_stats(self):
        """Retorna dados do serviço com estatísticas"""
        data = self.to_dict_with_professionals()
        data['total_appointments'] = len(self.appointments)
        data['total_professionals'] = len([prof for prof in self.professionals if prof.active])
        return data

