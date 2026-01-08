from src.config.database import db
from datetime import datetime

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Empresa dona do serviço
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(7), default='#10B981')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = db.relationship('User', backref=db.backref('services', lazy=True))
    appointments = db.relationship('Appointment', backref='service', lazy=True)
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else None,
            'duration': self.duration,
            'color': self.color,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict_with_stats(self):
        """Converte o objeto para dicionário incluindo estatísticas"""
        service_dict = self.to_dict()
        service_dict['stats'] = {
            'total_appointments': len(self.appointments),
            'completed_appointments': len([apt for apt in self.appointments if apt.status == 'completed']),
            'pending_appointments': len([apt for apt in self.appointments if apt.status == 'scheduled']),
            'total_professionals': len(self.professionals) if hasattr(self, 'professionals') else 0
        }
        return service_dict
    
    def to_dict_with_professionals(self):
        """Converte o objeto para dicionário incluindo profissionais completos"""
        service_dict = self.to_dict()
        service_dict['professionals'] = [professional.to_dict() for professional in self.professionals] if hasattr(self, 'professionals') else []
        return service_dict