from src.models.user import db
from datetime import datetime

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
    color = db.Column(db.String(7), default='#3B82F6')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    services = db.relationship('Service', secondary=professional_services, lazy='subquery',
                              backref=db.backref('professionals', lazy=True))
    appointments = db.relationship('Appointment', backref='professional', lazy=True)
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'phone': self.phone,
            'email': self.email,
            'color': self.color,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'services': [service.to_dict() for service in self.services] if hasattr(self, 'services') else []
        }