from src.models.user import db
from datetime import datetime

# Tabela de associação para relacionamento N:N entre Professional e Service
professional_services = db.Table('professional_services',
    db.Column('professional_id', db.Integer, db.ForeignKey('professionals.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('services.id'), primary_key=True)
)

class Professional(db.Model):
    __tablename__ = 'professionals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(255))
    color = db.Column(db.String(7), default='#3B82F6')  # Cor para identificação no calendário
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    appointments = db.relationship('Appointment', backref='professional', lazy=True)
    services = db.relationship('Service', secondary=professional_services, back_populates='professionals')

    def __repr__(self):
        return f'<Professional {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'phone': self.phone,
            'email': self.email,
            'color': self.color,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict_with_services(self):
        """Retorna dados do profissional com serviços"""
        data = self.to_dict()
        data['services'] = [service.to_dict() for service in self.services]
        return data

    def to_dict_with_stats(self):
        """Retorna dados do profissional com estatísticas"""
        data = self.to_dict_with_services()
        data['total_appointments'] = len(self.appointments)
        data['total_services'] = len(self.services)
        return data

