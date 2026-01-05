from src.config.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='admin')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Dados do estabelecimento para agendamento online
    slug = db.Column(db.String(100), unique=True, nullable=True)
    business_name = db.Column(db.String(255), nullable=True)
    business_phone = db.Column(db.String(20), nullable=True)
    business_address = db.Column(db.String(500), nullable=True)
    business_logo = db.Column(db.String(500), nullable=True)
    online_booking_enabled = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        """Define a senha do usuário usando hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha fornecida está correta"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'slug': self.slug,
            'business_name': self.business_name,
            'business_phone': self.business_phone,
            'business_address': self.business_address,
            'business_logo': self.business_logo,
            'online_booking_enabled': self.online_booking_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_public_dict(self):
        """Dados públicos do estabelecimento para agendamento online"""
        return {
            'slug': self.slug,
            'business_name': self.business_name or self.name,
            'business_phone': self.business_phone,
            'business_address': self.business_address,
            'business_logo': self.business_logo,
            'online_booking_enabled': self.online_booking_enabled
        }